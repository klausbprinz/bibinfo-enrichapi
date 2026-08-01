import httpx
from typing import Dict, Any, Optional
from ..models.otherAPIs import BookCoverOpenLibrary


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
        
        if not targetIsbn and basicMarcMd:
            identifiers = basicMarcMd.get("identifier", [])
            for item in identifiers:
                if isinstance(item, dict) and item.get("idType") == "isbn":
                    targetIsbn = item.get("value")
                    if targetIsbn:
                        break

        if not targetIsbn:
            return None

        # build model instance to compute candidate URL
        coverModel = BookCoverOpenLibrary(isbn=targetIsbn, imageSize=imageSize)
        
        if not coverModel.coverURL:
            return None

        # validate image presence via async HEAD request (Open Library returns 404 if missing)
        client = self._client or httpx.AsyncClient(timeout=5.0)
        shouldClose = self._client is None
        
        try:
            response = await client.head(coverModel.coverURL, follow_redirects=True)
            if response.status_code == 200:
                return coverModel
            return None
        
        except httpx.RequestError:
            return None

        finally:
            if shouldClose:
                await client.aclose()