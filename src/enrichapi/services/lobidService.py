import logging
import httpx
from ..models.lobidGND import DataLobidGND

logger = logging.getLogger(__name__)

class LobidService:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.baseUrl = "https://lobid.org/gnd"

    async def fetchGndData(self, gndId: str) -> DataLobidGND | None:
        """Fetches raw GND JSON from Lobid and validates directly into DataLobidGND."""
        cleanId = gndId.strip()
        url = f"{self.base_url}/{cleanId}.json"
        
        try:
            res = await self.client.get(url)
            res.raise_for_status()
            
            rawJson = res.json()
            
            # Pydantic validates rawJson directly
            return DataLobidGND(
                gndId=cleanId,
                gndInformation=rawJson
            )

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                logger.info(f"GND ID {cleanId} not found on Lobid.")
            else:
                logger.error(f"Lobid HTTP error for {cleanId}: {exc}")
            return None
        except httpx.TimeoutException:
            logger.error(f"Timeout reaching Lobid for GND ID {cleanId}")
            return None
        except Exception as exc:
            logger.error(f"Error processing Lobid data for {cleanId}: {exc}")
            return None