import logging
import httpx
from ..models.lobidGND import DataLobidGND

logger = logging.getLogger(__name__)


class LobidService:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.baseUrl = "https://lobid.org/gnd"

    async def fetchGndData(self, gndId: str) -> DataLobidGND | None:
        """
        Fetches GND JSON from Lobid and validates directly into DataLobidGND.
        Returns None if record is missing or network failure occurs.
        """
        cleanId = gndId.strip()
        url = f"{self.baseUrl}/{cleanId}.json"

        try:
            res = await self.client.get(url)
            
            if res.status_code == 404:
                logger.info(f"GND ID '{cleanId}' not found on Lobid (404).")
                return None
                
            res.raise_for_status()
            rawJson = res.json()

            # Pydantic handles discriminator routing, nested model mapping, and field validation!
            return DataLobidGND(
                gndId=cleanId,
                gndInformation=rawJson
            )

        except httpx.TimeoutException:
            logger.error(f"Timeout reaching Lobid API for GND ID '{cleanId}'.")
            return None
        except httpx.HTTPError as exc:
            logger.error(f"HTTP error fetching GND ID '{cleanId}': {exc}")
            return None
        except Exception as exc:
            logger.error(f"Unexpected error validating Lobid payload for '{cleanId}': {exc}")
            return None