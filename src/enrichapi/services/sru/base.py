import abc
import asyncio
import logging
import time
import httpx

from lxml import etree
from httpx import AsyncClient, HTTPError, TimeoutException
from urllib.parse import quote
from typing import Any

from ...utils import marc21parser as parse

from ...models.basicMarc21MD import (
    BasicMarc21MD, 
    Marc21MdTitle, 
    Marc21MdMainEntry,
    Marc21MdAddedEntry,
    Marc21MdPhysDescription,
    Marc21MdPublicationNotice,
    Marc21MdClassificationNumber,
    Marc21MdIdentifier,
    Marc21MdElectronicLocation,
    Marc21MdItemInfos,
    Marc21MdHoldingInfos
)
from ...models.additionalRecsSRU import (
    AdditionalRecsSRU, 
    AdditionalRecsByPerson, 
    AdditionalRecsBySubjectHeadings, 
    AdditionalRecsByClassification,
    AdditionalRec
)
from ...models.response import IsbnAmbiguityResponse, IsbnCandidate
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class BaseSruService(abc.ABC):
    """
    Abstract Base Class for institutional SRU services.
    Shares core MARC21 parsing, HTTP lifecycles, and parallel subsidiary coordination,
    while delegating institution-specific query syntax to concrete subclasses.
    """
    
    def __init__(self, client: AsyncClient):
        self.client = client
        self.baseUrl: str = ""
        self.recordSchema: str | None = None
        self.ns = {
            "srw": "http://www.loc.gov/zing/srw/", 
            "marc": "http://www.loc.gov/MARC21/slim"
        }

    # =====================================================================
    # ABSTRACT CONTRACT: Institution-Specific Query Builders
    # =====================================================================

    @abc.abstractmethod
    def buildPrimaryQuery(self, cleanId: str, idType: str) -> str:
        """Constructs the institution-specific primary search query string."""
        pass

    @abc.abstractmethod
    def buildPersonQuery(self, personName: str) -> str:
        """Constructs the subsidiary search query string for author matching."""
        pass

    @abc.abstractmethod
    def buildSubjectQuery(self, subjectHeadings: list[str]) -> str:
        """Constructs the subsidiary search query string for subject headings matching."""
        pass

    @abc.abstractmethod
    def buildClassificationQuery(self, classifications: list[Any]) -> str:
        """Constructs the subsidiary search query string for classification matching."""
        pass

    def extractBaseBibId(self, marcData: BasicMarc21MD) -> str | None:
        return marcData.primaryBibIdentifier

    # =====================================================================
    # CORE PIPELINE: Primary Record Fetching & Ambiguity Resolution
    # =====================================================================

    async def fetchRecord(self, identifier: str, idType: str) -> tuple[etree._Element | None, list[str]]:
        """Handles HTTP lifecycle, applies normalization, strict/pragmatic rules, and ISBN ambiguity resolution."""
        cleanId = identifier.strip()
        
        # normalize legacy or alternate aliases to the universal 'bibId' standard
        normalizedIdType = "bibId" if idType in ("bibId", "ac", "ppn") else idType

        query = self.buildPrimaryQuery(cleanId, normalizedIdType)
        url = f"{self.baseUrl}?version=1.2&operation=searchRetrieve&query={query}&maximumRecords=50"
        if self.recordSchema:
            url += f"&recordSchema={self.recordSchema}"
        
        logger.info(f"[SRU] Initiating primary record fetch | id='{cleanId}' type='{normalizedIdType}' query='{query}'")
        startTime = time.perf_counter()

        warnings: list[str] = []

        try:
            res = await self.client.get(url)
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            res.raise_for_status()
            
            sruRoot = etree.fromstring(res.content)
            recordElems = sruRoot.findall(".//srw:record", namespaces=self.ns)
            count = len(recordElems)
            
            # rule 1: strict system ids (bibId / ac / ppn)
            if normalizedIdType == "bibId":
                if count == 1:
                    logger.info(f"[SRU] Successfully fetched and matched primary MARC21 record for '{cleanId}' ({elapsedMs}ms)")
                    return recordElems[0].find("srw:recordData/marc:record", namespaces=self.ns), warnings
                elif count == 0:
                    logger.warning(f"[SRU] No records found for system identifier '{cleanId}' (query='{query}') ({elapsedMs}ms)")
                else:
                    logger.warning(f"[SRU] Strict system ID collision: Multiple records ({count}) returned for unique id '{cleanId}' ({elapsedMs}ms). Treating as 404.")
                return None, warnings

            # rule 2: pragmatic barcodes (auto-selects first match on collision with warning)
            elif normalizedIdType == "barcode":
                if count == 1:
                    logger.info(f"[SRU] Successfully fetched and matched primary MARC21 record for barcode '{cleanId}' ({elapsedMs}ms)")
                    return recordElems[0].find("srw:recordData/marc:record", namespaces=self.ns), warnings
                elif count == 0:
                    logger.warning(f"[SRU] No records found for barcode '{cleanId}' (query='{query}') ({elapsedMs}ms)")
                    return None, warnings
                else:
                    warningMsg = f"Barcode collision detected: '{cleanId}' matched {count} catalog records. Automatically selected the first record."
                    logger.warning(f"[SRU] {warningMsg} ({elapsedMs}ms)")
                    warnings.append(warningMsg)
                    return recordElems[0].find("srw:recordData/marc:record", namespaces=self.ns), warnings

            # rule 3: ISBN ambiguity handling (triggers HTTP 300 with candidates list if multiple editions match)
            elif normalizedIdType == "isbn":
                if count == 1:
                    logger.info(f"[SRU] Successfully fetched and matched primary MARC21 record for ISBN '{cleanId}' ({elapsedMs}ms)")
                    return recordElems[0].find("srw:recordData/marc:record", namespaces=self.ns), warnings
                elif count == 0:
                    logger.warning(f"[SRU] No records found for ISBN '{cleanId}' (query='{query}') ({elapsedMs}ms)")
                    return None, warnings
                else:
                    logger.warning(f"[SRU] ISBN ambiguity detected: '{cleanId}' matched {count} records. Triggering HTTP 300.")
                    candidates = []
                    for elem in recordElems:
                        marcRec = elem.find("srw:recordData/marc:record", namespaces=self.ns)
                        if marcRec is not None:
                            tempParsed = self.extractMarc21Metadata(marcRec) if hasattr(self, 'extractMarc21Metadata') else None
                            bibIdVal = self.extractBaseBibId(tempParsed) if tempParsed else None
                            
                            titleMain, titleRem, _, _ = parse.extractTitleData(marcRec)
                            fullTitle = f"{titleMain} : {titleRem}" if titleRem else titleMain
                            
                            authorName = None
                            for tag in ("100", "110", "111"):
                                entryField = marcRec.find(f'marc:datafield[@tag="{tag}"]', namespaces=self.ns)
                                if entryField is not None:
                                    entryData = parse.extractEntryData(entryField)
                                    if entryData and entryData.get("name"):
                                        authorName = entryData.get("name")
                                        break
                            
                            pubNotices = parse.extractPublicationNotices(marcRec)
                            publishersVal = pubNotices[0].get("names") if pubNotices else None
                            yearsVal = pubNotices[0].get("dates") if pubNotices else None

                            candidates.append(
                                IsbnCandidate(
                                    bibId=bibIdVal,
                                    title=fullTitle,
                                    author=authorName,
                                    publishers=publishersVal,
                                    dates=yearsVal
                                )
                            )
                    
                    ambiguityResp = IsbnAmbiguityResponse(
                        isbn=cleanId,
                        totalMatches=count,
                        candidates=candidates
                    )
                    raise HTTPException(status_code=300, detail=ambiguityResp.model_dump())

            return None, warnings

        except httpx.TimeoutException:
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            logger.error(f"[SRU] Timeout after {elapsedMs}ms connecting to SRU server for query: {query}")
            return None, warnings
        except httpx.HTTPError as exc:
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            logger.error(f"[SRU] HTTP status error fetching query='{query}' ({elapsedMs}ms)", exc_info=True)
            return None, warnings
        except etree.XMLSyntaxError as exc:
            logger.error(f"[SRU] Failed to parse XML response for query='{query}': {exc}", exc_info=True)
            return None, warnings

    # =====================================================================
    # SHARED PARSER: Raw XML to Pydantic Model Transformation
    # =====================================================================

    def extractMarc21Metadata(self, marcRecord: etree._Element) -> BasicMarc21MD:
        """Transforms raw MARC21 XML selectors into structured Pydantic models."""
        logger.info("[SRU] Parsing raw MARC21 XML into Pydantic data models...")

        titleData = parse.extractTitleData(marcRecord)
        titleModel = Marc21MdTitle(
            titleMain=titleData[0],
            titleRemainder=titleData[1],
            titlePartNumber=titleData[2],
            titlePartName=titleData[3]
        )

        mainEntryModel = None
        for tag, nameType in [("100", "person"), ("110", "corporate"), ("111", "conferenceOrEvent")]:
            field = marcRecord.find(f'marc:datafield[@tag="{tag}"]', namespaces=self.ns)
            if field is not None:
                data = parse.extractEntryData(field)
                if data:
                    mainEntryModel = Marc21MdMainEntry(nameType=nameType, **data)
                    break

        addedEntriesModels: list[Marc21MdAddedEntry] = []
        tagMap = {"700": "person", "710": "corporate", "711": "conferenceOrEvent"}
        df7xxList = marcRecord.xpath('marc:datafield[@tag="700" or @tag="710" or @tag="711"]', namespaces=self.ns)
        for field in df7xxList:
            nameType = tagMap.get(field.attrib.get("tag"))
            data = parse.extractEntryData(field)
            if data and nameType:
                addedEntriesModels.append(Marc21MdAddedEntry(nameType=nameType, **data))

        physDescriptModels = [Marc21MdPhysDescription(**d) for d in parse.extractPhysicalDescriptions(marcRecord)]
        publicationNoticeModels = [Marc21MdPublicationNotice(**d) for d in parse.extractPublicationNotices(marcRecord)]
        classificationModels = [Marc21MdClassificationNumber(**d) for d in parse.extractClassificationNumbers(marcRecord)]
        identifierModels = [Marc21MdIdentifier(**d) for d in parse.extractIdentifier(marcRecord)]
        electronicLocationModels = [Marc21MdElectronicLocation(**d) for d in parse.extractElectronicLocations(marcRecord)]
        holdingModels = [Marc21MdHoldingInfos(**d) for d in parse.extractHoldingInfos(marcRecord)]

        langCodes = parse.extractLanguageCodes(marcRecord)
        subjectHeadings = parse.extractSubjectHeadings(marcRecord)

        return BasicMarc21MD(
            title=titleModel,
            mainEntry=mainEntryModel,
            addedEntries=addedEntriesModels,
            languageCodes=langCodes,
            languageCodesOriginal=parse.extractLanguageCodesOriginal(marcRecord),
            publicationCountryCodes=parse.extractPublicationCountryCodes(marcRecord),
            edition=parse.extractEdition(marcRecord),
            physicalDescriptions=physDescriptModels,
            publicationNotices=publicationNoticeModels,
            genreForms=parse.extractGenreForms(marcRecord),
            subjectHeadings=subjectHeadings,
            classifications=classificationModels,
            bibMaterialType=parse.extractBibMaterialType(marcRecord),
            bibResourceType=parse.extractBibResourceType(marcRecord),
            electronicLocations=electronicLocationModels,
            abstracts=parse.extractAbstracts(marcRecord),
            identifier=identifierModels,
            holdingInfos=holdingModels
        )

    # =====================================================================
    # SUBSIDIARY PIPELINE: Concurrent Similar Records Coordination
    # =====================================================================

    async def fetchAdditionalRecords(self, marcData: BasicMarc21MD, data) -> dict[str, Any]:
        """Coordinates dynamic secondary SRU lookups concurrently using institutional query builders."""
        tasks = []
        taskTypes = []
        finalRecords = []

        baseBibId = self.extractBaseBibId(marcData)
        logger.info(f"[SRU] Preparing subsidiary searches for base record ID='{baseBibId}'")

        # 1. person-based similarity query
        if data.fetchSimilarByPerson:
            if marcData.mainEntry and marcData.mainEntry.name:
                personName = marcData.mainEntry.name
                queryStr = self.buildPersonQuery(personName)
                tasks.append(self._executeSubsidiarySRU(queryStr, baseIdentifier=baseBibId, maxRecs=data.maxRecs))
                taskTypes.append(("person", personName))
            else:
                finalRecords.append(AdditionalRecsByPerson(searchType="person", name="", maxRecs=data.maxRecs, additionalRecs=[]))

        # 2. subject-headings-based similarity query
        if data.fetchSimilarBySubject:
            if marcData.subjectHeadings:
                queryStr = self.buildSubjectQuery(marcData.subjectHeadings)
                tasks.append(self._executeSubsidiarySRU(queryStr, baseIdentifier=baseBibId, maxRecs=data.maxRecs))
                taskTypes.append(("subject", marcData.subjectHeadings))
            else:
                finalRecords.append(AdditionalRecsBySubjectHeadings(searchType="subjectHeadings", subjectHeadings=[], maxRecs=data.maxRecs, additionalRecs=[]))

        # 3. classification-based similarity query
        if data.fetchSimilarByClassification:
            if marcData.classifications:
                queryStr = self.buildClassificationQuery(marcData.classifications)
                if queryStr:
                    tasks.append(self._executeSubsidiarySRU(queryStr, baseIdentifier=baseBibId, maxRecs=data.maxRecs))
                    taskTypes.append(("classification", marcData.classifications))
                else:
                    finalRecords.append(AdditionalRecsByClassification(searchType="classification", classifications=[], maxRecs=data.maxRecs, additionalRecs=[]))
            else:
                finalRecords.append(AdditionalRecsByClassification(searchType="classification", classifications=[], maxRecs=data.maxRecs, additionalRecs=[]))

        # execute dynamic subsidiary tasks concurrently via asyncio.gather
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for (category, criteria), res in zip(taskTypes, results):
                if isinstance(res, Exception):
                    recs = []
                else:
                    recs = [AdditionalRec(**r) if isinstance(r, dict) else r for r in res]

                if category == "person":
                    finalRecords.append(AdditionalRecsByPerson(searchType="person", name=criteria, maxRecs=data.maxRecs, additionalRecs=recs))
                elif category == "subject":
                    finalRecords.append(AdditionalRecsBySubjectHeadings(searchType="subjectHeadings", subjectHeadings=criteria, maxRecs=data.maxRecs, additionalRecs=recs))
                elif category == "classification":
                    finalRecords.append(AdditionalRecsByClassification(searchType="classification", classifications=criteria, maxRecs=data.maxRecs, additionalRecs=recs))

        return {"records": finalRecords}

    async def _executeSubsidiarySRU(self, queryString: str, baseIdentifier: str | None = None, maxRecs: int = 5) -> list[dict]:
        """Worker helper to fetch subsidiary records and filter out the base record match."""
        # fetch 1 extra record to account for potential base record self-inclusion
        fetchCount = maxRecs + 1 if baseIdentifier else maxRecs
        params = {"version": "1.2", "operation": "searchRetrieve", "query": queryString, "maximumRecords": str(fetchCount)}
        if self.recordSchema:
            params["recordSchema"] = self.recordSchema
        
        startTime = time.perf_counter()
        try:
            res = await self.client.get(self.baseUrl, params=params, timeout=8.0)
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            res.raise_for_status()

            sruRoot = etree.fromstring(res.content)
            recordDataElems = sruRoot.findall(".//srw:recordData/marc:record", namespaces=self.ns)

            extractedRecords = []
            baseIdClean = baseIdentifier.strip() if baseIdentifier else None

            for recordElem in recordDataElems:
                recDict = parse.extractAdditionalRecData(recordElem)
                # guardrail: filter out the original source record from similar lists
                if baseIdClean and recDict.get("bibId") == baseIdClean:
                    continue
                extractedRecords.append(recDict)

            return extractedRecords[:maxRecs]
        except Exception as e:
            raise e