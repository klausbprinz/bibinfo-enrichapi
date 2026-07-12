# this is mock data so far

from httpx import AsyncClient
from ..models.wikidata import DataWikidata

class WikidataService:
    def __init__(self, client: AsyncClient):
        self.client = client

    async def fetchWikidata(self, wikidataId: str | None, gnd_id: str | None) -> DataWikidata:
        """Mock implementation using Pydantic aliases mapping."""
        
        # using property IDs directly to leverage your model's alias mappings
        targetId = wikidataId or "Q1035" 
        
        mock_info = {
            "wikidataType": "person",
            "P31": ["Q5"],  # instance of: human
            "P18": ["https://upload.wikimedia.org/wikipedia/commons/d/d3/Albert_Einstein_Head.jpg"],
            "P27": ["Q155502", "Q40"],  # citizenship flags
            "P106": ["Q169470"]  # occupation: physicist
        }
        
        return DataWikidata(
            wikidataId=targetId,
            otherIds=[gnd_id] if gnd_id else [],
            wikidataInformation=mock_info
        )