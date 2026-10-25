from httpx import AsyncClient
from urllib.parse import quote
from typing import Any
from lxml import etree

from .base import BaseSruService
from ...models.basicMarc21MD import BasicMarc21MD
from ...models.basicMarc21MD import Marc21MdHoldingInfos
from fastapi import HTTPException

class GbvSruService(BaseSruService):
    """
    Concrete SRU service implementation for the GBV / K10plus library network.
    Maps abstract queries to PICA / K10plus SRU syntax and index fields.
    """
    
    def __init__(self, client: AsyncClient):
        super().__init__(client)
        # standard K10plus union catalog GVK SRU endpoint
        self.baseUrl = "https://sru.k10plus.de/gvk"

    # =====================================================================
    # CONCRETE IMPLEMENTATION: Primary Query & Identifiers
    # =====================================================================

    def buildPrimaryQuery(self, cleanId: str, idType: str) -> str:
        """Translates normalized identifier types into PICA / K10plus SRU index search strings."""
        safeId = quote(cleanId, safe="")
        
        if idType == "bibId":
            return f"pica.ppn={safeId}"
        elif idType == "isbn":
            return f"pica.isb={safeId}"
        
        # Defensive fallback for unvalidated calls
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported identifier type '{idType}' for GBV / K10plus. Use 'bibId' or 'isbn'."
        )

    def extractBaseBibId(self, marcData: BasicMarc21MD) -> str | None:
        """Extracts the PPN / primary bib identifier from parsed MARC21 metadata."""
        if marcData.identifier:
            for idObj in marcData.identifier:
                if idObj.idType in ("primaryBib", "ppn") and idObj.value:
                    return idObj.value
        return None

    def extractMarc21Metadata(self, marcRecord: etree._Element) -> BasicMarc21MD:
        """Parses core MARC21 XML, populates PPN, processes GBV field 924 holdings, and attaches metadata."""
        marcData = super().extractMarc21Metadata(marcRecord)
        
        # extract control field 001 for PPN
        cf001 = marcRecord.find('marc:controlfield[@tag="001"]', namespaces=self.ns)
        if cf001 is not None and cf001.text:
            marcData.primaryBibIdentifier = cf001.text.strip()
            
        # parse GBV tag 924 for institutional holdings (ind1="0" physical, ind1="1" electronic)
        holding924List = marcRecord.xpath('marc:datafield[@tag="924"]', namespaces=self.ns)
        if holding924List:
            customHoldings = []
            for field in holding924List:
                ind1 = field.attrib.get("ind1", "")
                isPhysical = (ind1 == "0")

                if isPhysical:
                
                    subfields = {sub.attrib.get("code"): sub.text for sub in field.findall("marc:subfield", namespaces=self.ns)}
                    
                    customHoldings.append(
                        Marc21MdHoldingInfos(
                            institutionCode=subfields.get("b"),
                            locationCode=subfields.get("h"),
                            callNumber=subfields.get("g")
                        )
                    )
            if customHoldings:
                marcData.holdingInfos = customHoldings
                
        return marcData

    # =====================================================================
    # CONCRETE IMPLEMENTATION: Subsidiary Query Builders (PICA Indexes)
    # =====================================================================

    def buildPersonQuery(self, personName: str) -> str:
        """Builds a PICA-specific person/creator search query (`pica.per`)."""
        return f'pica.per="{personName}"'

    def buildSubjectQuery(self, subjectHeadings: list[str]) -> str:
        """Builds a PICA-specific multi-term subject headings query joined by AND (`pica.slw`)."""
        return " AND ".join([f'pica.slw="{s}"' for s in subjectHeadings])

    def buildClassificationQuery(self, classifications: list[Any]) -> str:
        """
        Prioritizes and builds a PICA classification query for K10plus.
        Prioritizes RVK / BKL / DDC indexes available in K10plus.
        """
        schemeMap: dict[str, list] = {}
        for c in classifications:
            if not c.classificationNumber:
                continue
            schemeMap.setdefault((c.classificationType or "").lower().strip(), []).append(c)

        indexName = "pica.bkl"
        if "rvk" in schemeMap:
            target = schemeMap["rvk"]
            indexName = "pica.rvk"
        elif "bkl" in schemeMap:
            target = schemeMap["bkl"]
            indexName = "pica.bkl"
        elif "ddc" in schemeMap:
            target = schemeMap["ddc"]
            indexName = "pica.ddc"
        else:
            target = [c for cList in schemeMap.values() for c in cList]
            indexName = "pica.bkl"

        if not target:
            return ""

        classNumbers = list(dict.fromkeys([c.classificationNumber for c in target]))
        return " AND ".join([f'{indexName}="{num}"' for num in classNumbers])