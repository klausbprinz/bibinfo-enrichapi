import logging
import time
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

        logger.info(f"[Lobid] Initiating GND lookup | gndId='{cleanId}' url='{url}'")
        startTime = time.perf_counter()

        try:
            res = await self.client.get(url)
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            
            if res.status_code == 404:
                # explicit missing entity log -> safe to fail gracefully
                logger.info(f"[Lobid] GND ID '{cleanId}' not found on Lobid (HTTP 404) ({elapsedMs}ms)")
                return None
                
            res.raise_for_status()
            logger.debug(f"[Lobid] HTTP {res.status_code} received for GND ID '{cleanId}' ({elapsedMs}ms)")

            rawJson = res.json()
            
            # log key extracted info for debugging payload structural type
            typeInfo = rawJson.get("type", [])
            preferredName = rawJson.get("preferredName", "N/A")
            logger.debug(f"[Lobid] Raw JSON fetched for '{cleanId}' | type={typeInfo} preferredName='{preferredName}'")

            # Pydantic handles discriminator routing, nested model mapping, and field validation!
            validatedData = DataLobidGND(
                gndId=cleanId,
                gndInformation=rawJson
            )
            
            logger.info(f"[Lobid] Successfully validated Lobid payload for GND ID '{cleanId}' ({elapsedMs}ms)")
            return validatedData

        except httpx.TimeoutException:
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            logger.error(f"[Lobid] Timeout reaching Lobid API for GND ID '{cleanId}' after {elapsedMs}ms")
            return None
        except httpx.HTTPError as exc:
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            logger.error(f"[Lobid] HTTP error fetching GND ID '{cleanId}' ({elapsedMs}ms): {exc}", exc_info=True)
            return None
        except Exception as exc:
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            logger.error(f"[Lobid] Unexpected error validating Lobid payload for '{cleanId}' ({elapsedMs}ms): {exc}", exc_info=True)
            return None