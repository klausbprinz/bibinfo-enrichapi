import logging
from httpx import AsyncClient
from ..models.abstract import BookDescriptionData
from ..models.envelope import EnrichmentEnvelope

logger = logging.getLogger(__name__)

class AbstractService:
    def __init__(self, client: AsyncClient, googleApiKey: str | None = None):
        self.client = client
        self.googleApiKey = googleApiKey

    async def fetchDescription(self, basicMarcMd: dict, bypassIsbn: str | None = None) -> EnrichmentEnvelope[BookDescriptionData]:
        """
        Executes a robust, time-bounded multi-source waterfall description retrieval strategy:
        1. Google Books API (Fast ISBN lookup with optional API key & strict timeout)
        2. Open Library Works API (ISBN -> Work key -> Description with strict timeout)
        3. Wikipedia REST API (Fallback using Title from MARC21 metadata against german wikipedia)
        4. Exhausted
        """
        isbn = bypassIsbn or self._extractIsbn(basicMarcMd)
        cleanIsbn = isbn.replace("-", "").replace(" ", "").strip() if isbn else None

        logger.info(f"[AbstractService] Initiating description lookup | isbn='{cleanIsbn}'")

        # tier 1: Google Books API (ISBN lookup)
        if cleanIsbn:
            googleUrl = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{cleanIsbn}"
            if self.googleApiKey:
                googleUrl += f"&key={self.googleApiKey}"
                logger.debug("[AbstractService] Appended Google API Key to Google Books description request.")

            try:
                res = await self.client.get(googleUrl, timeout=2.0)
                if res.status_code == 200:
                    data = res.json()
                    items = data.get("items", [])
                    if items:
                        desc = items[0].get("volumeInfo", {}).get("description")
                        if desc:
                            logger.info(f"[AbstractService] Success via Google Books for ISBN '{cleanIsbn}'")
                            return EnrichmentEnvelope(
                                status="success",
                                message=f"Description successfully retrieved from Google Books for ISBN '{cleanIsbn}'",
                                data=BookDescriptionData(
                                    isbn=cleanIsbn,
                                    description=desc,
                                    source="google_books"
                                )
                            )
                else:
                    logger.debug(f"[AbstractService] Google Books returned HTTP {res.status_code} for ISBN '{cleanIsbn}'")
            except Exception as e:
                logger.debug(f"[AbstractService] Google Books description check failed/timed out: {e}")

        # tier 2: Open Library Works API (ISBN -> work key -> description)
        if cleanIsbn:
            try:
                isbnUrl = f"https://openlibrary.org/isbn/{cleanIsbn}.json"
                res = await self.client.get(isbnUrl, timeout=2.0, follow_redirects=True)
                if res.status_code == 200:
                    works = res.json().get("works", [])
                    if works and "key" in works[0]:
                        workKey = works[0]["key"] # e.g. /works/OL45804W
                        workUrl = f"https://openlibrary.org{workKey}.json"
                        workRes = await self.client.get(workUrl, timeout=2.0)
                        if workRes.status_code == 200:
                            descField = workRes.json().get("description")
                            desc = descField.get("value") if isinstance(descField, dict) else descField
                            if desc:
                                logger.info(f"[AbstractService] Success via Open Library for ISBN '{cleanIsbn}'")
                                return EnrichmentEnvelope(
                                    status="success",
                                    message=f"Description successfully retrieved from Open Library for ISBN '{cleanIsbn}'",
                                    data=BookDescriptionData(
                                        isbn=cleanIsbn,
                                        description=desc,
                                        source="open_library"
                                    )
                                )
            except Exception as e:
                logger.debug(f"[AbstractService] Open Library description check failed/timed out: {e}")

        # tier 3: Wikipedia REST API (fallback using title from marc21md - german wikipedia)
        title = self._extractTitle(basicMarcMd)

        if title:
            wikiQuery = title.strip()
            headers = {
                "User-Agent": "BibliographicEnrichmentAPI/1.0 (https://github.com/klausbprinz/bibinfo-enrichapi; klaus_prinz@gmx.net)"
            }
            try:
                searchUrl = f"https://de.wikipedia.org/w/api.php?action=opensearch&search={wikiQuery}&limit=1&namespace=0&format=json"
                searchRes = await self.client.get(searchUrl, headers=headers, timeout=2.0)
                
                if searchRes.status_code == 200:
                    jsonRes = searchRes.json()
                    titles = jsonRes[1] if len(jsonRes) > 1 else []
                    if titles:
                        pageTitle = titles[0]
                        summaryUrl = f"https://de.wikipedia.org/api/rest_v1/page/summary/{pageTitle}"
                        summaryRes = await self.client.get(summaryUrl, headers=headers, timeout=2.0)
                        
                        if summaryRes.status_code == 200:
                            extract = summaryRes.json().get("extract")
                            if extract:
                                logger.info(f"[AbstractService] Success via Wikipedia for query '{wikiQuery}' (Page: '{pageTitle}')")
                                return EnrichmentEnvelope(
                                    status="success",
                                    message=f"Description successfully retrieved from Wikipedia for '{pageTitle}'",
                                    data=BookDescriptionData(
                                        isbn=cleanIsbn,
                                        description=extract,
                                        source="wikipedia"
                                    )
                                )
            except Exception as e:
                logger.debug(f"[AbstractService] Wikipedia description check failed/timed out: {e}")

        # tier 4: exhausted
        logger.info(f"[AbstractService] Not found: No description available across providers.")
        return EnrichmentEnvelope(
            status="not_found",
            message="No book description found across configured providers",
            data=None
        )

    def _extractIsbn(self, basicMarcMd: dict) -> str | None:
        for item in basicMarcMd.get("identifier", []):
            if isinstance(item, dict) and item.get("idType") == "isbn" and item.get("value"):
                return item["value"]
        return None

    def _extractTitle(self, basicMarcMd: dict) -> str | None:
        titleObj = basicMarcMd.get("title", {})
        return titleObj.get("titleMain") if isinstance(titleObj, dict) else None

    def _extractAuthor(self, basicMarcMd: dict) -> str | None:
        mainEntry = basicMarcMd.get("mainEntry", {})
        return mainEntry.get("name") if isinstance(mainEntry, dict) else None