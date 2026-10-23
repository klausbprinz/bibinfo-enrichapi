import logging
import time
import httpx
from typing import Any
from ..models.lobidGND import DataLobidGND

logger = logging.getLogger(__name__)


class LobidService:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.baseUrl = "https://lobid.org/gnd"

    async def fetchGndData(self, gndId: str | None) -> dict[str, Any]:
        """
        Fetches GND JSON from Lobid and validates into DataLobidGND.
        Returns a standardized EnrichmentEnvelope dictionary containing 
        status, diagnostic message, and payload data.
        """
        
        # phase 1: pre-flight check - verify GND identifier exists before querying
        if not gndId or not gndId.strip():
            logger.debug("[Lobid] Skipped GND lookup: No GND identifier provided")
            return {
                "status": "skipped",
                "message": "No GND identifier available for lookup",
                "data": None
            }

        cleanId = gndId.strip()
        url = f"{self.baseUrl}/{cleanId}.json"

        logger.info(f"[Lobid] Initiating GND lookup | gndId='{cleanId}' url='{url}'")
        startTime = time.perf_counter()

        try:
            # phase 2: execute asynchronous HTTP GET request to Lobid API
            res = await self.client.get(url)
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            
            # handle explicit resource misses gracefully (HTTP 404)
            if res.status_code == 404:
                logger.info(f"[Lobid] GND ID '{cleanId}' not found on Lobid (HTTP 404) ({elapsedMs}ms)")
                return {
                    "status": "not_found",
                    "message": f"GND ID '{cleanId}' not found in Lobid authority database",
                    "data": None
                }
                
            # enforce error checking for other unexpected HTTP status codes
            res.raise_for_status()
            logger.debug(f"[Lobid] HTTP {res.status_code} received for GND ID '{cleanId}' ({elapsedMs}ms)")

            rawJson = res.json()
            
            # extract key structural fields for debugging payload type and name attributes
            typeInfo = rawJson.get("type", [])
            preferredName = rawJson.get("preferredName", "N/A")
            logger.debug(f"[Lobid] Raw JSON fetched for '{cleanId}' | type={typeInfo} preferredName='{preferredName}'")

            # phase 3: validate raw payload into Pydantic model
            validatedData = DataLobidGND(
                gndId=cleanId,
                gndInformation=rawJson
            )
            
            logger.info(f"[Lobid] Successfully validated Lobid payload for GND ID '{cleanId}' ({elapsedMs}ms)")
            return {
                "status": "success",
                "message": f"Successfully retrieved Lobid authority data for GND ID '{cleanId}'",
                "data": validatedData
            }

        except httpx.TimeoutException:
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            errorMsg = f"Timeout reaching Lobid API after {elapsedMs}ms"
            logger.error(f"[Lobid] {errorMsg} for GND ID '{cleanId}'")
            return {
                "status": "error",
                "message": errorMsg,
                "data": None
            }
            
        except httpx.HTTPError as exc:
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            errorMsg = f"HTTP error fetching Lobid data: {exc}"
            logger.error(f"[Lobid] {errorMsg} for GND ID '{cleanId}' ({elapsedMs}ms)", exc_info=True)
            return {
                "status": "error",
                "message": errorMsg,
                "data": None
            }
            
        except Exception as exc:
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            errorMsg = f"Unexpected error processing Lobid payload: {exc}"
            logger.error(f"[Lobid] {errorMsg} for '{cleanId}' ({elapsedMs}ms)", exc_info=True)
            return {
                "status": "error",
                "message": errorMsg,
                "data": None
            }