# this is mock data so far

from httpx import AsyncClient
from ..models.lobidGND import DataLobidGND, PersonLobidGND

class LobidService:
    def __init__(self, client: AsyncClient):
        self.client = client

    async def fetchGndData(self, gndId: str) -> DataLobidGND:
        """Mock implementation pulling simulated Lobid data footprint."""
        
        # this mirrors a valid human target schema (e.g., PersonLobidGND)
        mockInfo = {
            "gndType": "person",
            "entityTypes": ["Person", "AuthorityRecord"],
            "preferredName": "Albert Einstein",
            "professionsOrOccupations": ["Physicist"],
            "datesOfBirth": ["1879-03-14"],
            "datesOfDeath": ["1955-04-18"]
        }
        
        return DataLobidGND(
            gndId=gndId,
            gndInformation=mockInfo
        )