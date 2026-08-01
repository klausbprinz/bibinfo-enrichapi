import httpx
import logging
import time
from typing import Dict, Any, Optional
from ..models.otherAPIs import DescriptionGoogleBooks

logger = logging.getLogger(__name__)

class AbstractService:
    def __init__(self, httpClient: Optional[httpx.AsyncClient] = None, googleApiKey: Optional[str] = None):
        self._client = httpClient
        self.googleApiKey = googleApiKey

    async def fetchDescription(
        self, 
        basicMarcMd: Dict[str, Any], 
        bypassIsbn: Optional[str] = None
    ) -> Optional[DescriptionGoogleBooks]:
        """
        Fetches book description using Google Books API with an automatic 
        fallback to Open Library's Works API.
        """
        # extract ISBN
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
            logger.warning("[Abstract] No valid ISBN provided or found in metadata. Skipping description fetch.")
            return None

        cleanIsbn = targetIsbn.replace("-", "").replace(" ", "")
        logger.info(f"[Abstract] Initiating description lookup | isbn='{cleanIsbn}' (source={sourceType})")

        client = self._client or httpx.AsyncClient(timeout=7.0)
        shouldClose = self._client is None
        startTime = time.perf_counter()

        try:
            # primary Strategy: Google Books API
            logger.info(f"[Abstract] Attempting Primary Strategy: Google Books API for ISBN '{cleanIsbn}'...")
            description = await self._fetchFromGoogleBooks(client, cleanIsbn)
            
            # fallback strategy: Open Library API (if Google returns nothing)
            if not description:
                logger.info(f"[Abstract] Google Books yield no result. Attempting Fallback Strategy: Open Library API for ISBN '{cleanIsbn}'...")
                description = await self._fetchFromOpenLibrary(client, cleanIsbn)

            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)

            if description:
                logger.info(f"[Abstract] Successfully retrieved book description for ISBN '{cleanIsbn}' ({len(description)} chars) ({elapsedMs}ms)")
                return DescriptionGoogleBooks(description=description)

            logger.warning(f"[Abstract] No description found on both Google Books and Open Library for ISBN '{cleanIsbn}' ({elapsedMs}ms)")
            return None

        finally:
            if shouldClose:
                logger.debug("[Abstract] Closing transient httpx.AsyncClient connection.")
                await client.aclose()

    async def _fetchFromGoogleBooks(self, client: httpx.AsyncClient, isbn: str) -> Optional[str]:
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
        if self.googleApiKey:
            url += f"&key={self.googleApiKey}"
            logger.debug("[Abstract] Appended Google API Key to Google Books request URL.")

        startTime = time.perf_counter()
        try:
            res = await client.get(url)
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)

            if res.status_code == 200:
                data = res.json()
                items = data.get("items")
                if isinstance(items, list) and len(items) > 0:
                    volumeInfo = items[0].get("volumeInfo")
                    if isinstance(volumeInfo, dict):
                        desc = volumeInfo.get("description")
                        if desc:
                            logger.info(f"[Abstract] [Google Books] Found description for ISBN '{isbn}' ({len(desc)} chars) ({elapsedMs}ms)")
                            return desc
                        else:
                            logger.info(f"[Abstract] [Google Books] Volume found for ISBN '{isbn}' but lacks description field ({elapsedMs}ms)")
                            return None
                
                logger.info(f"[Abstract] [Google Books] Zero volumes matched ISBN '{isbn}' (totalItems={data.get('totalItems', 0)}) ({elapsedMs}ms)")
            else:
                logger.warning(f"[Abstract] [Google Books] HTTP {res.status_code} response for ISBN '{isbn}' ({elapsedMs}ms)")
                
        except httpx.HTTPError as e:
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            logger.warning(f"[Abstract] [Google Books] Request failed for ISBN '{isbn}' ({elapsedMs}ms): {e}")

        except Exception as e:
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            logger.error(f"[Abstract] [Google Books] Unexpected error parsing response for ISBN '{isbn}' ({elapsedMs}ms): {e}", exc_info=True)
            
        return None
    

    async def _fetchFromOpenLibrary(self, client: httpx.AsyncClient, isbn: str) -> Optional[str]:
        startTime = time.perf_counter()
        try:
            # get work key via ISBN endpoint
            isbnUrl = f"https://openlibrary.org/isbn/{isbn}.json"
            res = await client.get(isbnUrl, follow_redirects=True)
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)

            if res.status_code != 200:
                logger.info(f"[Abstract] [Open Library] ISBN lookup returned HTTP {res.status_code} for ISBN '{isbn}' ({elapsedMs}ms)")
                return None

            data = res.json()
            works = data.get("works", [])
            if not works:
                logger.info(f"[Abstract] [Open Library] No linked works array found in edition metadata for ISBN '{isbn}' ({elapsedMs}ms)")
                return None

            workKey = works[0].get("key")  # e.g. "/works/OL45804W"
            if not workKey:
                logger.warning(f"[Abstract] [Open Library] Work entry missing 'key' property for ISBN '{isbn}' ({elapsedMs}ms)")
                return None

            logger.debug(f"[Abstract] [Open Library] Resolved work key '{workKey}' for ISBN '{isbn}'. Requesting work details...")

            # get work details
            workUrl = f"https://openlibrary.org{workKey}.json"
            workStartTime = time.perf_counter()
            workRes = await client.get(workUrl)
            workElapsedMs = round((time.perf_counter() - workStartTime) * 1000, 2)

            if workRes.status_code == 200:
                workData = workRes.json()
                descField = workData.get("description")
                
                # Open Library description can be str or dict {"type": "...", "value": "..."}
                resultDesc = None
                if isinstance(descField, str):
                    resultDesc = descField
                elif isinstance(descField, dict):
                    resultDesc = descField.get("value")

                if resultDesc:
                    logger.info(f"[Abstract] [Open Library] Found description via workKey '{workKey}' for ISBN '{isbn}' ({len(resultDesc)} chars) ({workElapsedMs}ms)")
                    return resultDesc
                else:
                    logger.info(f"[Abstract] [Open Library] Work '{workKey}' found for ISBN '{isbn}' but contains no description ({workElapsedMs}ms)")
            else:
                logger.warning(f"[Abstract] [Open Library] Work details request for '{workKey}' failed with HTTP {workRes.status_code} ({workElapsedMs}ms)")

        except httpx.HTTPError as e:
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            logger.warning(f"[Abstract] [Open Library] Request failed for ISBN '{isbn}' ({elapsedMs}ms): {e}")

        except Exception as e:
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            logger.error(f"[Abstract] [Open Library] Unexpected error parsing response for ISBN '{isbn}' ({elapsedMs}ms): {e}", exc_info=True)

        return None