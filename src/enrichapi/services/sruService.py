from lxml import etree
from httpx import AsyncClient
import asyncio

from typing import Any

from ..util import marc21parser as parse

from ..models.basicMarc21MD import (
    BasicMarc21MD, 
    Marc21MdTitle, 
    Marc21MdMainEntry,
    Marc21MdAddedEntry,
    Marc21MdPhysDescription,
    Marc21MdPublicationNotice
)
from ..models.additionalRecsSRU import (
    AdditionalRecsSRU, 
    AdditionalRecsByAuthor, 
    AdditionalRecsBySubjectHeadings, 
    AdditionalRecsByClassification,
    AdditionalRec
)

class SruService:
    
    def __init__(self, client: AsyncClient):
        self.client = client
        self.base_url = "https://obv-at-oenb.alma.exlibrisgroup.com/view/sru/43ACC_ONB"
        self.ns = {
            "srw": "http://www.loc.gov/zing/srw/", 
            "marc": "http://www.loc.gov/MARC21/slim"
        }

    async def fetchRecord(self, identifier: str, id_type: str) -> etree._Element | None:
        """Handles the HTTP lifecycle and parses raw XML into an lxml tree element."""
        
        query = f'alma.barcode="{identifier}"' if id_type == "barcode" else f'alma.local_control_field_009="{identifier}"'
        url = f"{self.base_url}?version=1.2&operation=searchRetrieve&query={query}"
        
        res = await self.client.get(url)
        res.raise_for_status()
        
        sruRoot = etree.fromstring(res.content)
        recordElems = sruRoot.findall(".//srw:record", namespaces=self.ns)
        
        if len(recordElems) == 1:
            return recordElems[0].find("srw:recordData/marc:record", namespaces=self.ns)
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
        for tag, nameType in [("100", "personal"), ("110", "corporate"), ("111", "meeting")]:
            field = marcRecord.find(f'marc:datafield[@tag="{tag}"]', namespaces=self.ns)
            if field is not None:
                data = parse.extractEntryData(field)
                if data:
                    mainEntryModel = Marc21MdMainEntry(nameType=nameType, **data)
                    break

        # extract added entries (700 / 710 / 711)
        addedEntriesModels: list[Marc21MdAddedEntry] = []
        tagMap = {"700": "personal", "710": "corporate", "711": "meeting"}
        
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

        return BasicMarc21MD(
            title=titleModel,
            mainEntry=mainEntryModel,
            addedEntries=addedEntriesModels,
            languageCodes=parse.extractLanguageCodes(marcRecord),
            languageCodesOriginal=parse.extractLanguageCodesOriginal(marcRecord),
            publicationCountryCodes=parse.extractPublicationCountryCodes(marcRecord),
            edition=parse.extractEdition(marcRecord),
            physicalDescriptions=physDescriptModels,
            publicationNotices=publicationNoticeModels


            
            # TODO: map addedEntries, languageCodes, etc
        )
    
    
    async def fetchAdditionalRecords(self, marcData: BasicMarc21MD, data) -> dict[str, Any]:
        """
        Reuses structured data already parsed by extractMarc21Metadata 
        to coordinate dynamic secondary SRU lookups based on user flags.
        """
        tasks = []
        taskTypes = []

        # reuse parsed Main Entry Author data
        if data.fetchSimilarByAuthor and marcData.mainEntry and marcData.mainEntry.name:
            authorName = marcData.mainEntry.name
            tasks.append(self._executeSubsidiarySRU(f'alma.creator="{authorName}"', maxRecs=data.maxRecs))
            taskTypes.append(("author", authorName))

        # reuse parsed subject headings
        if data.fetchSimilarBySubject and marcData.subjectHeadings:
            
            # marcData.subjectHeadings is list[str] of your SH values
            queryStr = " OR ".join([f'alma.subject="{s}"' for s in marcData.subjectHeadings])
            tasks.append(self._executeSubsidiarySRU(queryStr, maxRecs=data.maxRecs))
            taskTypes.append(("subject", marcData.subjectHeadings))

        # reuse parsed classifications
        if data.fetchSimilarByClassification and marcData.classifications:
            
            # find first classification number available in your structured data list
            validClasses = [c.classificationNumber for c in marcData.classifications if c.classificationNumber]
            if validClasses:
                # search using primary classification found
                classNum = validClasses[0]
                tasks.append(self._executeSubsidiarySRU(f'alma.other_class_number="{classNum}"', maxRecs=data.maxRecs))
                taskTypes.append(("classification", classNum))

        if not tasks:
            return {"records": []}

        # concurrent network execution
        results = await asyncio.gather(*tasks, return_exceptions=True)

        finalRecords = []
        for (category, criteria), res in zip(taskTypes, results):
            if isinstance(res, Exception):
                continue
            
            if category == "author":
                finalRecords.append(
                    AdditionalRecsByAuthor(
                        searchType="author",
                        name=criteria,
                        maxRecs=data.maxRecs,
                        additionalRecs=[AdditionalRec(**r) if isinstance(r, dict) else r for r in res]
                    )
                )
            elif category == "subject":
                finalRecords.append(
                    AdditionalRecsBySubjectHeadings(
                        searchType="subjectHeadings",
                        subjectHeadings=criteria,
                        maxRecs=data.maxRecs,
                        additionalRecs=[AdditionalRec(**r) if isinstance(r, dict) else r for r in res]
                    )
                )
            elif category == "classification":
                finalRecords.append(
                    AdditionalRecsByClassification(
                        searchType="classification",
                        classifications=marcData.classifications,
                        maxRecs=data.maxRecs,
                        additionalRecs=[AdditionalRec(**r) if isinstance(r, dict) else r for r in res]
                    )
                )

        return {"records": finalRecords}
    

    async def _executeSubsidiarySRU(self, queryString: str, maxRecs: int = 5) -> list:
        """Helper network worker to parse response records from subsequent queries."""
        
        # this is where nested SRU HTTP fetch will take place
        # for prototype setup, return an empty array or basic simulation structure
        # url = f"{self.base_url}?version=1.2&operation=searchRetrieve&query={queryString}&maximumRecords=5"
        return [
            {
                "ac": "AC99999999", 
                "callNumbers": ["MOCK-123"], 
                "barcodes": [], 
                "isbns": [], 
                "issns": []
            }
        ]
    