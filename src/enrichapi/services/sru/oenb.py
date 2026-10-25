from httpx import AsyncClient
from urllib.parse import quote
from typing import Any
from lxml import etree

from .base import BaseSruService
from ...models.basicMarc21MD import BasicMarc21MD

class OenbSruService(BaseSruService):
    """
    Concrete SRU service implementation for the Austrian National Library (Alma / OeNB).
    Maps abstract queries to Ex Libris Alma SRU syntax and index fields.
    """
    
    def __init__(self, client: AsyncClient):
        super().__init__(client)
        # set the specific Alma SRU endpoint for the Austrian National Library
        self.baseUrl = "https://obv-at-oenb.alma.exlibrisgroup.com/view/sru/43ACC_ONB"

    # =====================================================================
    # CONCRETE IMPLEMENTATION: Primary Query & Identifiers
    # =====================================================================

    def buildPrimaryQuery(self, cleanId: str, idType: str) -> str:
        """Translates normalized identifier types into Alma SRU index search strings."""
        safeId = quote(cleanId, safe="")
        if idType == "barcode":
            return f"alma.barcode={safeId}"
        elif idType == "bibId":
            return f"alma.local_control_field_009={safeId}"
        elif idType == "isbn":
            return f"alma.isbn={safeId}"
        return f"alma.local_control_field_009={safeId}"

    def extractMarc21Metadata(self, marcRecord: etree._Element) -> BasicMarc21MD:
        """Parses core MARC21 XML and populates OeNB-specific primary identifier and holdings."""
        marcData = super().extractMarc21Metadata(marcRecord)
        
        # extract control field 009 for Alma AC-number (with MMS-ID fallback)
        cf009 = marcRecord.find('marc:controlfield[@tag="009"]', namespaces=self.ns)
        if cf009 is not None and cf009.text:
            marcData.primaryBibIdentifier = cf009.text.strip()
        else:
            cf001 = marcRecord.find('marc:controlfield[@tag="001"]', namespaces=self.ns)
            if cf001 is not None and cf001.text:
                marcData.primaryBibIdentifier = cf001.text.strip()

        # apply default institution metadata to holdings
        if marcData.holdingInfos:
            for holding in marcData.holdingInfos:
                holding.institutionCode = "43ACC_ONB"
                holding.institutionLabel = "Österreichische Nationalbibliothek"
                
        return marcData

    # =====================================================================
    # CONCRETE IMPLEMENTATION: Subsidiary Query Builders (Alma Indexes)
    # =====================================================================

    def buildPersonQuery(self, authorName: str) -> str:
        """Builds an Alma-specific creator search query."""
        return f'alma.creator="{authorName}"'

    def buildSubjectQuery(self, subjectHeadings: list[str]) -> str:
        """Builds an Alma-specific multi-term subject headings query joined by AND."""
        return " AND ".join([f'alma.subjects="{s}"' for s in subjectHeadings])

    def buildClassificationQuery(self, classifications: list[Any]) -> str:
        """
        Prioritizes and builds an Alma classification query.
        Falls back through BKL -> RVK -> DDC scheme hierarchies.
        """
        schemeMap: dict[str, list] = {}
        for c in classifications:
            if not c.classificationNumber:
                continue
            schemeMap.setdefault((c.classificationType or "").lower().strip(), []).append(c)

        indexName = "alma.other_class_number"
        if "bkl" in schemeMap:
            target = schemeMap["bkl"]
        elif "rvk" in schemeMap:
            target = schemeMap["rvk"]
        elif "ddc" in schemeMap:
            target = schemeMap["ddc"]
            indexName = "alma.dewey_decimal_class_number"
        else:
            target = [c for cList in schemeMap.values() for c in cList]

        if not target:
            return ""

        classNumbers = list(dict.fromkeys([c.classificationNumber for c in target]))
        return " AND ".join([f'{indexName}="{num}"' for num in classNumbers])