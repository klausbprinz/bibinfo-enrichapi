from lxml import etree
from httpx import AsyncClient
import asyncio
from ..models.basicMarc21MD import BasicMarc21MD, Marc21MdTitle, Marc21MdMainEntry
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

    def extractMarc21Metadata(self, marc_record: etree._Element) -> BasicMarc21MD:
        """Transforms raw XML selectors into pydantic object."""
        
        # --- Extract Title (245) ---
        df245a = marc_record.find('marc:datafield[@tag="245"]/marc:subfield[@code="a"]', namespaces=self.ns)
        df245b = marc_record.find('marc:datafield[@tag="245"]/marc:subfield[@code="b"]', namespaces=self.ns)
        
        titleModel = Marc21MdTitle(
            titleMain=df245a.text if df245a is not None else None,
            titleRemainder=df245b.text if df245b is not None else None
        )

        # --- Extract Main Entry (100) ---
        df100a = marc_record.find('marc:datafield[@tag="100"]/marc:subfield[@code="a"]', namespaces=self.ns)
        df100_0 = marc_record.find('marc:datafield[@tag="100"]/marc:subfield[@code="0"]', namespaces=self.ns)
        
        mainEntry = None
        if df100a is not None:
            
            # clean up potential (DE-588) prefixes from raw MARC 0 subfields
            gndClean = df100_0.text.replace("(DE-588)", "").strip() if df100_0 is not None and df100_0.text else None
            mainEntry = Marc21MdMainEntry(
                name=df100a.text,
                nameType="personal",
                gndIdentifier=gndClean
            )

        return BasicMarc21MD(
            title=titleModel,
            mainEntry=mainEntry
            
            # TODO: map addedEntries, languageCodes, etc
        )
    
    
    async def fetchAdditionalRecords(self, marcData: BasicMarc21MD, data) -> AdditionalRecsSRU:
        """
        Reuses structured data already parsed by extractMarc21Metadata 
        to coordinate dynamic secondary SRU lookups based on user flags.
        """
        tasks = []
        taskTypes = []

        # reuse parsed Main Entry Author data
        if data.fetchSimilarByAuthor and marcData.mainEntry and marcData.mainEntry.name:
            authorName = marcData.mainEntry.name
            tasks.append(self._executeSubsidiarySRU(f'alma.creator="{authorName}"'))
            taskTypes.append(("author", authorName))

        # reuse parsed subject headings
        if data.fetchSimilarBySubject and marcData.subjectHeadings:
            
            # marcData.subjectHeadings is list[str] of your SH values
            queryStr = " OR ".join([f'alma.subject="{s}"' for s in marcData.subjectHeadings])
            tasks.append(self._executeSubsidiarySRU(queryStr))
            taskTypes.append(("subject", marcData.subjectHeadings))

        # reuse parsed classifications
        if data.fetchSimilarByClassification and marcData.classifications:
            
            # find first classification number available in your structured data list
            validClasses = [c.classificationNumber for c in marcData.classifications if c.classificationNumber]
            if validClasses:
                # search using primary classification found
                classNum = validClasses[0]
                tasks.append(self._executeSubsidiarySRU(f'alma.other_class_number="{classNum}"'))
                taskTypes.append(("classification", classNum))

        if not tasks:
            return AdditionalRecsSRU(records=[])

        # concurrent network execution
        results = await asyncio.gather(*tasks, return_exceptions=True)

        finalRecords = []
        for (category, criteria), res in zip(taskTypes, results):
            if isinstance(res, Exception):
                continue
            
            if category == "author":
                finalRecords.append({
                    "searchType": "author",
                    "name": criteria,
                    "additionalRecs": res
                })

            elif category == "subject":
                finalRecords.append({
                    "searchType": "subject",
                    "subjectHeadings": criteria,
                    "additionalRecs": res
                })

            elif category == "classification":
                
                # convert list of Marc21MdClassificationNumber models into raw dicts so Pydantic parses them cleanly
                finalRecords.append({
                    "searchType": "classification",
                    "classifications": [c.model_dump() for c in marcData.classifications],
                    "additionalRecs": res
                })

        return {"records": finalRecords}
    

    async def _executeSubsidiarySRU(self, queryString: str) -> list:
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