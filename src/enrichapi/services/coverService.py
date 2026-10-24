import logging
from httpx import AsyncClient
from ..models.cover import BookCoverData
from ..models.envelope import EnrichmentEnvelope

logger = logging.getLogger(__name__)

class CoverService:
    def __init__(self, client: AsyncClient, googleApiKey: str | None = None):
        self.client = client
        self.googleApiKey = googleApiKey

    async def fetchCover(self, basicMarcMd: dict, bypassIsbn: str | None = None, imageSize: str = "M") -> EnrichmentEnvelope[BookCoverData]:
        """
        Executes a robust waterfall cover retrieval strategy:
        1. DNB (HEAD request)
        2. Google Books Volumes API (Fast global lookup with optional API key)
        3. Open Library Books API (JSON metadata lookup for Cover ID)
        4. Open Library Direct Cover Endpoint (HEAD request fallback)
        5. Exhausted
        """
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

        # tier 1: DNB Cover endpoint (fast for german/austrian titles)
        dnbUrl = f"https://portal.dnb.de/opac/mvb/cover?isbn={cleanIsbn}&size={sizeUpper.lower()}"
        try:
            res = await self.client.head(dnbUrl, timeout=2.0, follow_redirects=True)
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

        # tier 2: Google Books Volumes API (fast global hit, API key protected)
        googleUrl = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{cleanIsbn}"
        if self.googleApiKey:
            googleUrl += f"&key={self.googleApiKey}"
            logger.debug("[CoverService] Appended Google API Key to Google Books cover request.")

        try:
            res = await self.client.get(googleUrl, timeout=2.0)
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

        # tier 3: Open Library Books API (metadata -> cover ID)
        olBooksUrl = f"https://openlibrary.org/api/books?bibkeys=ISBN:{cleanIsbn}&format=json&jscmd=viewapi"
        try:
            res = await self.client.get(olBooksUrl, timeout=2.5)
            if res.status_code == 200:
                data = res.json()
                key = f"ISBN:{cleanIsbn}"
                if key in data and "thumbnail_url" in data[key]:
                    rawThumbUrl = data[key]["thumbnail_url"]
                    targetSuffix = f"-{sizeUpper}.jpg"
                    for s in ["-S.jpg", "-M.jpg", "-L.jpg"]:
                        if s in rawThumbUrl:
                            rawThumbUrl = rawThumbUrl.replace(s, targetSuffix)
                            break

                    logger.info(f"[CoverService] Success via Open Library Books API for ISBN '{cleanIsbn}'")
                    return EnrichmentEnvelope(
                        status="success",
                        message=f"Cover successfully retrieved from Open Library for ISBN '{cleanIsbn}'",
                        data=BookCoverData(
                            isbn=cleanIsbn,
                            imageSize=sizeUpper, # type: ignore
                            coverURL=rawThumbUrl,
                            source="open_library"
                        )
                    )
        except Exception as e:
            logger.debug(f"[CoverService] Open Library Books API check failed for ISBN '{cleanIsbn}': {e}")

        # tier 4: Open Library direct cover lookup (HEAD request fallback)
        olDirectUrl = f"https://covers.openlibrary.org/b/isbn/{cleanIsbn}-{sizeUpper}.jpg?default=false"
        try:
            res = await self.client.head(olDirectUrl, timeout=2.0, follow_redirects=False)
            if res.status_code in (200, 302, 303, 307):
                # If it redirected, use the location header. If it returned 200 OK directly, 
                # use the clean base URL (stripping our ?default=false query param).
                targetUrl = res.headers.get("location")
                if not targetUrl and res.status_code == 200:
                    targetUrl = f"https://covers.openlibrary.org/b/isbn/{cleanIsbn}-{sizeUpper}.jpg"

                if targetUrl:
                    logger.info(f"[CoverService] Fast success via Open Library Direct for ISBN '{cleanIsbn}'")
                    return EnrichmentEnvelope(
                        status="success",
                        message=f"Cover successfully retrieved from Open Library for ISBN '{cleanIsbn}'",
                        data=BookCoverData(
                            isbn=cleanIsbn,
                            imageSize=sizeUpper, # type: ignore
                            coverURL=targetUrl,
                            source="open_library"
                        )
                    )
        except Exception as e:
            logger.debug(f"[CoverService] Open Library Direct check failed: {e}")

        # tier 5: exhausted
        logger.info(f"[CoverService] Not found: No cover available for ISBN '{cleanIsbn}' across all providers.")
        return EnrichmentEnvelope(
            status="not_found",
            message=f"No cover image found for ISBN '{cleanIsbn}' across configured providers",
            data=None
        )

    def _extractIsbn(self, basicMarcMd: dict) -> str | None:
        identifiers = basicMarcMd.get("identifier", [])
        for item in identifiers:
            idType = item.get("idType") if isinstance(item, dict) else getattr(item, "idType", None)
            val = item.get("value") if isinstance(item, dict) else getattr(item, "value", None)
            if idType == "isbn" and val:
                return val
        return None