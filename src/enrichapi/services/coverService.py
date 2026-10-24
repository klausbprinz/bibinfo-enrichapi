import logging
from httpx import AsyncClient
from ..models.cover import BookCoverData
from ..models.envelope import EnrichmentEnvelope

logger = logging.getLogger(__name__)

class CoverService:
    def __init__(self, client: AsyncClient):
        self.client = client

    async def fetchCover(self, basicMarcMd: dict, bypassIsbn: str | None = None, imageSize: str = "M") -> EnrichmentEnvelope[BookCoverData]:
        """
        Executes a robust 3-tier waterfall cover retrieval strategy:
        1. Explicit bypassIsbn (if provided by request) or DNB lookup
        2. Open Library Books API (via Cover ID extraction)
        3. Google Books Volumes API (guarded final fallback)
        """
        # determine ISBN: prioritize explicit bypassIsbn, otherwise extract from MARC metadata
        isbn = bypassIsbn or self._extractIsbn(basicMarcMd)
        if not isbn:
            logger.info("[CoverService] Skipped: No valid ISBN provided or found in MARC metadata.")
            return EnrichmentEnvelope(
                status="skipped",
                message="No valid ISBN provided or found in MARC metadata for cover lookup",
                data=None
            )

        cleanIsbn = isbn.replace("-", "").replace(" ", "").strip()
        sizeUpper = imageSize.upper()

        # tier 1: DNB cover endpoint (HEAD request for speed)
        dnbUrl = f"https://portal.dnb.de/opac/mvb/cover?isbn={cleanIsbn}&size={sizeUpper.lower()}"
        try:
            res = await self.client.head(dnbUrl, timeout=2.5, follow_redirects=True)
            if res.status_code == 200 and "image" in res.headers.get("content-type", ""):
                logger.info(f"[CoverService] Success via DNB for ISBN '{cleanIsbn}'")
                return EnrichmentEnvelope(
                    status="success",
                    message=f"Cover successfully retrieved from DNB for ISBN '{cleanIsbn}'",
                    data=BookCoverData(
                        isbn=cleanIsbn,
                        imageSize=sizeUpper, # type: ignore
                        coverURL=str(res.url),
                        source="dnb"
                    )
                )
        except Exception as e:
            logger.debug(f"[CoverService] DNB check failed for ISBN '{cleanIsbn}': {e}")

        # tier 2: Open Library Books API (extracts cover id to bypass rate limits)
        olBooksUrl = f"https://openlibrary.org/api/books?bibkeys=ISBN:{cleanIsbn}&format=json&jscmd=viewapi"
        try:
            res = await self.client.get(olBooksUrl, timeout=3.0)
            if res.status_code == 200:
                data = res.json()
                key = f"ISBN:{cleanIsbn}"
                if key in data and "thumbnail_url" in data[key]:
                    rawThumbUrl = data[key]["thumbnail_url"]
                    # Open Library returns URLs like .../b/id/12345-S.jpg
                    # swap the size suffix to match requested size (-S, -M, -L)
                    targetSuffix = f"-{sizeUpper}.jpg"
                    if "-S.jpg" in rawThumbUrl:
                        coverUrl = rawThumbUrl.replace("-S.jpg", targetSuffix)
                    elif "-M.jpg" in rawThumbUrl:
                        coverUrl = rawThumbUrl.replace("-M.jpg", targetSuffix)
                    elif "-L.jpg" in rawThumbUrl:
                        coverUrl = rawThumbUrl.replace("-L.jpg", targetSuffix)
                    else:
                        coverUrl = rawThumbUrl

                    logger.info(f"[CoverService] Success via Open Library for ISBN '{cleanIsbn}'")
                    return EnrichmentEnvelope(
                        status="success",
                        message=f"Cover successfully retrieved from Open Library for ISBN '{cleanIsbn}'",
                        data=BookCoverData(
                            isbn=cleanIsbn,
                            imageSize=sizeUpper, # type: ignore
                            coverURL=coverUrl,
                            source="open_library"
                        )
                    )
        except Exception as e:
            logger.debug(f"[CoverService] Open Library check failed for ISBN '{cleanIsbn}': {e}")

        # tier 3: Google Books Volumes API (guarded tertiary fallback)
        googleUrl = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{cleanIsbn}"
        try:
            res = await self.client.get(googleUrl, timeout=2.5)
            if res.status_code == 200:
                data = res.json()
                items = data.get("items", [])
                if items:
                    volume_info = items[0].get("volumeInfo", {})
                    image_links = volume_info.get("imageLinks", {})
                    imgUrl = image_links.get("thumbnail") or image_links.get("smallThumbnail")
                    if imgUrl:
                        if imgUrl.startswith("http://"):
                            imgUrl = imgUrl.replace("http://", "https://", 1)
                            
                        logger.info(f"[CoverService] Success via Google Books for ISBN '{cleanIsbn}'")
                        return EnrichmentEnvelope(
                            status="success",
                            message=f"Cover successfully retrieved from Google Books for ISBN '{cleanIsbn}'",
                            data=BookCoverData(
                                isbn=cleanIsbn,
                                imageSize=sizeUpper, # type: ignore
                                coverURL=imgUrl,
                                source="google_books"
                            )
                        )
        except Exception as e:
            logger.debug(f"[CoverService] Google Books check skipped/failed for ISBN '{cleanIsbn}': {e}")

        # step 4: all providers exhausted
        logger.info(f"[CoverService] Not found: No cover available for ISBN '{cleanIsbn}' across all providers.")
        return EnrichmentEnvelope(
            status="not_found",
            message=f"No cover image found for ISBN '{cleanIsbn}' across configured providers",
            data=None
        )

    def _extractIsbn(self, basicMarcMd: dict) -> str | None:
        """Helper to find the first valid ISBN from the MARC identifiers list."""
        identifiers = basicMarcMd.get("identifier", [])
        for item in identifiers:
            idType = item.get("idType") if isinstance(item, dict) else getattr(item, "idType", None)
            val = item.get("value") if isinstance(item, dict) else getattr(item, "value", None)
            
            if idType == "isbn" and val:
                return val
        return None