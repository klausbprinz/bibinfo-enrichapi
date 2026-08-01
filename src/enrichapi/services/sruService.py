import asyncio
import logging
import httpx

from lxml import etree
from httpx import AsyncClient
from urllib.parse import quote
from typing import Any

from ..util import marc21parser as parse

from ..models.basicMarc21MD import (
    BasicMarc21MD, 
    Marc21MdTitle, 
    Marc21MdMainEntry,
    Marc21MdAddedEntry,
    Marc21MdPhysDescription,
    Marc21MdPublicationNotice,
    Marc21MdClassificationNumber,
    Marc21MdIdentifier,
    Marc21MdItemInfos,
    Marc21MdHoldingInfos
)
from ..models.additionalRecsSRU import (
    AdditionalRecsSRU, 
    AdditionalRecsByAuthor, 
    AdditionalRecsBySubjectHeadings, 
    AdditionalRecsByClassification,
    AdditionalRec
)

logger = logging.getLogger(__name__)

class SruService:
    
    def __init__(self, client: AsyncClient):
        self.client = client
        self.baseUrl = "https://obv-at-oenb.alma.exlibrisgroup.com/view/sru/43ACC_ONB"
        self.ns = {
            "srw": "http://www.loc.gov/zing/srw/", 
            "marc": "http://www.loc.gov/MARC21/slim"
        }

    async def fetchRecord(self, identifier: str, idType: str) -> etree._Element | None:
        """Handles the HTTP lifecycle and parses raw XML into an lxml tree element."""
        cleanId = identifier.strip()
        safeId = quote(cleanId, safe="")
        
        # no double quotes around safeId -> try this now..
        query = (
            f'alma.barcode={safeId}' 
            if idType == "barcode" 
            else f'alma.local_control_field_009={safeId}'
        )
        
        url = f"{self.baseUrl}?version=1.2&operation=searchRetrieve&query={query}"
        
        try:
            res = await self.client.get(url)
            res.raise_for_status()
            
            sruRoot = etree.fromstring(res.content)
            recordElems = sruRoot.findall(".//srw:record", namespaces=self.ns)
            
            if len(recordElems) == 1:
                return recordElems[0].find("srw:recordData/marc:record", namespaces=self.ns)
                
            return None

        except httpx.TimeoutException:
            logger.error(f"Timeout connecting to SRU server for query: {query}")
            return None
        except httpx.HTTPError as exc:
            logger.error(f"HTTP error during SRU fetch: {exc}")
            return None
        except etree.XMLSyntaxError as exc:
            logger.error(f"Failed to parse SRU XML response: {exc}")
            return None

    
    def extractMarc21Metadata(self, marcRecord: etree._Element) -> BasicMarc21MD:
        """Transforms raw XML selectors into pydantic object."""

        # extract title
        titleData = parse.extractTitleData(marcRecord)
        
        titleModel = Marc21MdTitle(
            titleMain=titleData[0],
            titleRemainder=titleData[1],
            titlePartNumber=titleData[2],
            titlePartName=titleData[3]
        )

        # extract main entry (100 / 110 / 111)
        mainEntryModel = None
        for tag, nameType in [("100", "person"), ("110", "corporate"), ("111", "conferenceOrEvent")]:
            field = marcRecord.find(f'marc:datafield[@tag="{tag}"]', namespaces=self.ns)
            if field is not None:
                data = parse.extractEntryData(field)
                if data:
                    mainEntryModel = Marc21MdMainEntry(nameType=nameType, **data)
                    break

        # extract added entries (700 / 710 / 711)
        addedEntriesModels: list[Marc21MdAddedEntry] = []
        tagMap = {"700": "person", "710": "corporate", "711": "conferenceOrEvent"}
        
        df7xxList = marcRecord.xpath(
            'marc:datafield[@tag="700" or @tag="710" or @tag="711"]',
            namespaces=self.ns
        )
        for field in df7xxList:
            nameType = tagMap.get(field.attrib.get("tag"))
            data = parse.extractEntryData(field)
            if data and nameType:
                addedEntriesModels.append(Marc21MdAddedEntry(nameType=nameType, **data))

        # extract physDescriptions
        physDescriptModels = [
            Marc21MdPhysDescription(**d) 
            for d in parse.extractPhysicalDescriptions(marcRecord)
        ]

        # extract publicationNotices
        publicationNoticeModels = [
            Marc21MdPublicationNotice(**d) 
            for d in parse.extractPublicationNotices(marcRecord)
        ]

        # extract classifications
        classificationModels = [
            Marc21MdClassificationNumber(**d) 
            for d in parse.extractClassificationNumbers(marcRecord)
        ]

        # extract identifier
        identifierModels = [
            Marc21MdIdentifier(**d) 
            for d in parse.extractIdentifier(marcRecord)
        ]

        # extract holdings and items
        holdingModels = [
            Marc21MdHoldingInfos(**d)
            for d in parse.extractHoldingInfos(marcRecord)
        ]


        return BasicMarc21MD(
            title=titleModel,
            mainEntry=mainEntryModel,
            addedEntries=addedEntriesModels,
            languageCodes=parse.extractLanguageCodes(marcRecord),
            languageCodesOriginal=parse.extractLanguageCodesOriginal(marcRecord),
            publicationCountryCodes=parse.extractPublicationCountryCodes(marcRecord),
            edition=parse.extractEdition(marcRecord),
            physicalDescriptions=physDescriptModels,
            publicationNotices=publicationNoticeModels,
            genreForms=parse.extractGenreForms(marcRecord),
            subjectHeadings=parse.extractSubjectHeadings(marcRecord),
            classifications=classificationModels,
            bibMaterialType=parse.extractBibMaterialType(marcRecord),
            bibResourceType=parse.extractBibResourceType(marcRecord),
            fullTextURLs=parse.extractFullTextURLs(marcRecord),
            abstracts=parse.extractAbstracts(marcRecord),
            tableOfContentURLs=parse.extractTableOfContentURLs(marcRecord),
            identifier=identifierModels,
            holdingInfos=holdingModels
        )
    
    
    async def fetchAdditionalRecords(self, marcData: BasicMarc21MD, data) -> dict[str, Any]:
        """
        Reuses structured data already parsed by extractMarc21Metadata 
        to coordinate dynamic secondary SRU lookups based on user flags.
        """
        tasks = []
        taskTypes = []
        finalRecords = []

        # extract primaryBib identifier (controlfield 009)
        baseAc = None
        if marcData.identifier:
            for idObj in marcData.identifier:
                if idObj.idType == "primaryBib" and idObj.value:
                    baseAc = idObj.value
                    break

        # author search
        if data.fetchSimilarByAuthor:
            if marcData.mainEntry and marcData.mainEntry.name:
                authorName = marcData.mainEntry.name
                tasks.append(
                    self._executeSubsidiarySRU(
                        f'alma.creator="{authorName}"', 
                        baseIdentifier=baseAc, 
                        maxRecs=data.maxRecs
                    )
                )
                taskTypes.append(("author", authorName))
            else:
                # explicit empty return
                finalRecords.append(
                    AdditionalRecsByAuthor(
                        searchType="author",
                        name="",
                        maxRecs=data.maxRecs,
                        additionalRecs=[]
                    )
                )

        # subject headings search
        if data.fetchSimilarBySubject:
            if marcData.subjectHeadings:
                queryStr = " AND ".join([f'alma.subject="{s}"' for s in marcData.subjectHeadings])
                tasks.append(
                    self._executeSubsidiarySRU(
                        queryStr, 
                        baseIdentifier=baseAc, 
                        maxRecs=data.maxRecs
                    )
                )
                taskTypes.append(("subject", marcData.subjectHeadings))
            else:
                finalRecords.append(
                    AdditionalRecsBySubjectHeadings(
                        searchType="subjectHeadings",
                        subjectHeadings=[],
                        maxRecs=data.maxRecs,
                        additionalRecs=[]
                    )
                )

        # classifications search
        if data.fetchSimilarByClassification:
            targetClassifications = []
            indexName = "alma.other_class_number"

            if marcData.classifications:
                # group available classification objects by scheme type (lowercase)
                schemeMap: dict[str, list] = {}
                for c in marcData.classifications:
                    if not c.classificationNumber:
                        continue
                    ctype = (c.classificationType or "").lower().strip()
                    schemeMap.setdefault(ctype, []).append(c)

                # prioritization hierarchy: BKL -> RVK -> DDC -> Fallback to all others
                chosenSchemeObjs = []
                if "bkl" in schemeMap:
                    chosenSchemeObjs = schemeMap["bkl"]
                    indexName = "alma.other_class_number"
                elif "rvk" in schemeMap:
                    chosenSchemeObjs = schemeMap["rvk"]
                    indexName = "alma.other_class_number"
                elif "ddc" in schemeMap:
                    chosenSchemeObjs = schemeMap["ddc"]
                    indexName = "alma.dewey_decimal_class_number"
                else:
                    # flatten remaining non-empty schemes if none of top 3 are found
                    chosenSchemeObjs = [c for cList in schemeMap.values() for c in cList]
                    indexName = "alma.other_class_number"

                targetClassifications = chosenSchemeObjs

            if targetClassifications:
                # extract numbers and deduplicate preserving order
                classNumbers = list(dict.fromkeys([c.classificationNumber for c in targetClassifications]))
                
                # build SRU clauses joined by AND for precision matching
                queryClauses = [f'{indexName}="{num}"' for num in classNumbers]
                queryStr = " AND ".join(queryClauses)

                tasks.append(
                    self._executeSubsidiarySRU(
                        queryStr, 
                        baseIdentifier=baseAc, 
                        maxRecs=data.maxRecs
                    )
                )
                taskTypes.append(("classification", targetClassifications))
            else:
                finalRecords.append(
                    AdditionalRecsByClassification(
                        searchType="classification",
                        classifications=[],
                        maxRecs=data.maxRecs,
                        additionalRecs=[]
                    )
                )

        # execute dynamic tasks concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for (category, criteria), res in zip(taskTypes, results):
                if isinstance(res, Exception):
                    recs = []
                else:
                    recs = [AdditionalRec(**r) if isinstance(r, dict) else r for r in res]

                if category == "author":
                    finalRecords.append(
                        AdditionalRecsByAuthor(
                            searchType="author",
                            name=criteria,
                            maxRecs=data.maxRecs,
                            additionalRecs=recs
                        )
                    )
                elif category == "subject":
                    finalRecords.append(
                        AdditionalRecsBySubjectHeadings(
                            searchType="subjectHeadings",
                            subjectHeadings=criteria,
                            maxRecs=data.maxRecs,
                            additionalRecs=recs
                        )
                    )
                elif category == "classification":
                    finalRecords.append(
                        AdditionalRecsByClassification(
                            searchType="classification",
                            classifications=marcData.classifications,
                            maxRecs=data.maxRecs,
                            additionalRecs=recs
                        )
                    )

        return {"records": finalRecords}
    

    async def _executeSubsidiarySRU(
        self, 
        queryString: str, 
        baseIdentifier: str | None = None, 
        maxRecs: int = 5
    ) -> list[dict]:
        """Helper network worker to fetch and parse response records from subsidiary queries."""
        
        # always fetch 1 extra record to account for potential base record inclusion
        fetchCount = maxRecs + 1 if baseIdentifier else maxRecs

        params = {
            "version": "1.2",
            "operation": "searchRetrieve",
            "query": queryString,
            "maximumRecords": str(fetchCount)
        }

        try:
            res = await self.client.get(self.baseUrl, params=params)
            res.raise_for_status()

            sruRoot = etree.fromstring(res.content)
            recordDataElems = sruRoot.findall(".//srw:recordData/marc:record", namespaces=self.ns)

            extractedRecords = []
            baseIdClean = baseIdentifier.strip() if baseIdentifier else None

            for recordElem in recordDataElems:
                recDict = parse.extractAdditionalRecData(recordElem)
                
                # guardrail 1: filter out base record if matched
                if baseIdClean and recDict.get("ac") == baseIdClean:
                    continue

                extractedRecords.append(recDict)

            # guardrail 2: enforce strict maxRecs upper limit regardless of whether 0 or 1 item was filtered
            return extractedRecords[:maxRecs]

        except Exception as e:
            # re-raise so asyncio.gather(return_exceptions=True) catches it cleanly per task
            raise e
    