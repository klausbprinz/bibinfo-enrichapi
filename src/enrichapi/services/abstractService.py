import httpx
import logging
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
        if not targetIsbn and basicMarcMd:
            identifiers = basicMarcMd.get("identifier", [])
            for item in identifiers:
                if isinstance(item, dict) and item.get("idType") == "isbn":
                    targetIsbn = item.get("value")
                    if targetIsbn:
                        break

        if not targetIsbn:
            return None

        cleanIsbn = targetIsbn.replace("-", "").replace(" ", "")
        client = self._client or httpx.AsyncClient(timeout=7.0)
        shouldClose = self._client is None

        try:
            # primary Strategy: Google Books API
            description = await self._fetchFromGoogleBooks(client, cleanIsbn)
            
            # fallback strategy: Open Library API (if Google returns nothing)
            if not description:
                description = await self._fetchFromOpenLibrary(client, cleanIsbn)

            if description:
                return DescriptionGoogleBooks(description=description)
            return None

        finally:
            if shouldClose:
                await client.aclose()

    async def _fetchFromGoogleBooks(self, client: httpx.AsyncClient, isbn: str) -> Optional[str]:
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
        if self.googleApiKey:
            url += f"&key={self.googleApiKey}"

        try:
            res = await client.get(url)
            if res.status_code == 200:
                data = res.json()
                items = data.get("items")
                if isinstance(items, list) and len(items) > 0:
                    volumeInfo = items[0].get("volumeInfo")
                    if isinstance(volumeInfo, dict):
                        return volumeInfo.get("description")
                
        except httpx.HTTPError as e:
            logger.warning(f"Google Books request failed for ISBN {isbn}: {e}")

        except Exception as e:
            logger.error(f"Unexpected error parsing Google Books response for ISBN {isbn}: {e}")
            
        return None
    

    async def _fetchFromOpenLibrary(self, client: httpx.AsyncClient, isbn: str) -> Optional[str]:
        try:
            # get work key via ISBN endpoint
            isbnUrl = f"https://openlibrary.org/isbn/{isbn}.json"
            res = await client.get(isbnUrl, follow_redirects=True)
            if res.status_code != 200:
                return None

            data = res.json()
            works = data.get("works", [])
            if not works:
                return None

            workKey = works[0].get("key")  # e.g. "/works/OL45804W"
            if not workKey:
                return None

            # get work details
            workUrl = f"https://openlibrary.org{workKey}.json"
            workRes = await client.get(workUrl)
            if workRes.status_code == 200:
                workData = workRes.json()
                descField = workData.get("description")
                
                # Open Library description can be str or dict {"type": "...", "value": "..."}
                if isinstance(descField, str):
                    return descField
                elif isinstance(descField, dict):
                    return descField.get("value")

        except httpx.HTTPError as e:
            logger.warning(f"Open Library request failed for ISBN {isbn}: {e}")

        except Exception as e:
            logger.error(f"Unexpected error parsing Open Library response for ISBN {isbn}: {e}")

        return None