import httpx
import logging
import time
from typing import Dict, Any, Optional
from ..models.otherAPIs import BookCoverOpenLibrary

logger = logging.getLogger(__name__)


class CoverService:
    def __init__(self, httpClient: Optional[httpx.AsyncClient] = None):
        self._client = httpClient

    async def fetchCover(
        self, 
        basicMarcMd: Dict[str, Any], 
        bypassIsbn: Optional[str] = None,
        imageSize: str = "M"
    ) -> Optional[BookCoverOpenLibrary]:
        """
        Extracts ISBN from basicMarc21MD (or uses bypassIsbn) and validates 
        the Open Library cover image URL.
        """
        # resolve ISBN (bypass > MARC21 extracted identifiers)
        targetIsbn = bypassIsbn
        sourceType = "bypassIsbn" if bypassIsbn else "MARC21 metadata"
        
        if not targetIsbn and basicMarcMd:
            identifiers = basicMarcMd.get("identifier", [])
            for item in identifiers:
                if isinstance(item, dict) and item.get("idType") == "isbn":
                    targetIsbn = item.get("value")
                    if targetIsbn:
                        break

        if not targetIsbn:
            logger.warning("[Cover] No valid ISBN provided or found in MARC metadata. Skipping cover lookup.")
            return None

        cleanIsbn = targetIsbn.replace("-", "").replace(" ", "")
        logger.info(f"[Cover] Initiating cover check | isbn='{cleanIsbn}' size='{imageSize}' (source={sourceType})")

        # build model instance to compute candidate URL
        coverModel = BookCoverOpenLibrary(isbn=cleanIsbn, imageSize=imageSize)
        
        if not coverModel.coverURL:
            logger.warning(f"[Cover] Failed to generate valid candidate cover URL for ISBN '{cleanIsbn}'")
            return None

        logger.debug(f"[Cover] Generated candidate cover URL: '{coverModel.coverURL}'")

        # validate image presence via async HEAD request (Open Library returns 404 if missing)
        client = self._client or httpx.AsyncClient(timeout=5.0)
        shouldClose = self._client is None
        startTime = time.perf_counter()
        
        try:
            logger.debug(f"[Cover] Sending HEAD request to validate image existence at '{coverModel.coverURL}'...")
            response = await client.head(coverModel.coverURL, follow_redirects=True)
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)

            if response.status_code == 200:
                logger.info(f"[Cover] Valid cover image confirmed (HTTP 200) for ISBN '{cleanIsbn}' at '{coverModel.coverURL}' ({elapsedMs}ms)")
                return coverModel
            else:
                logger.info(f"[Cover] Cover image not found (HTTP {response.status_code}) for ISBN '{cleanIsbn}' ({elapsedMs}ms)")
                return None
        
        except httpx.RequestError as exc:
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            logger.warning(f"[Cover] Network request error validating cover URL for ISBN '{cleanIsbn}' ({elapsedMs}ms): {exc}")
            return None

        except Exception as exc:
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            logger.error(f"[Cover] Unexpected error validating cover URL for ISBN '{cleanIsbn}' ({elapsedMs}ms): {exc}", exc_info=True)
            return None

        finally:
            if shouldClose:
                logger.debug("[Cover] Closing transient httpx.AsyncClient connection.")
                await client.aclose()