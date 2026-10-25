import logging
import time
from typing import Any
from httpx import AsyncClient, HTTPError, TimeoutException
from ..models.wikidata import DataWikidata

logger = logging.getLogger(__name__)

WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"

# user-agent is required by wikidata's api policy, otherwise requests get blocked (403/429)
HEADERS = {
    "User-Agent": "enrichapi/1.0 (mailto:klaus_prinz@gmx.net)",
    "Accept": "application/sparql-results+json",
}


class WikidataService:
    def __init__(self, client: AsyncClient):
        self.client = client

    async def fetchWikidata(
        self,
        wikidataId: str | None,
        gndId: str | None,
        nameType: str | None = None,
    ) -> dict[str, Any]:
        """
        Fetches Wikidata entity claims using either a direct Q-ID or a GND ID lookup.
        Returns a standardized EnrichmentEnvelope dictionary containing 
        status, diagnostic message, and payload data.
        """
        
        # phase 1: pre-flight check - ensure at least one identifier is available
        if not wikidataId and not gndId:
            logger.debug("[Wikidata] Skipped Wikidata lookup: Neither wikidataId nor gndId provided")
            return {
                "status": "skipped",
                "message": "No wikidataId or gndId available for SPARQL lookup",
                "data": None
            }

        cleanQid = wikidataId.strip() if wikidataId else None
        cleanGnd = gndId.strip() if gndId else None

        logger.info(
            f"[Wikidata] Initiating entity fetch | qid='{cleanQid}' gndId='{cleanGnd}' nameType='{nameType}'"
        )

        # construct strict german sparql query
        query = self._buildSparqlQuery(cleanQid, cleanGnd)
        logger.debug(f"[Wikidata] Constructed SPARQL Query:\n{query}")

        startTime = time.perf_counter()

        try:
            # phase 2: execute async GET request against wikidata SPARQL endpoint
            response = await self.client.get(
                WIKIDATA_SPARQL_URL,
                params={"query": query, "format": "json"},
                headers=HEADERS,
                timeout=4.0,
            )
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            response.raise_for_status()
            logger.debug(f"[Wikidata] HTTP {response.status_code} received from SPARQL endpoint ({elapsedMs}ms)")
            
            sparqlData = response.json()

        except TimeoutException:
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            errorMsg = f"Timeout after {elapsedMs}ms querying Wikidata SPARQL endpoint"
            logger.error(f"[Wikidata] {errorMsg} for Q-ID='{cleanQid}' / GND='{cleanGnd}'")
            return {
                "status": "error",
                "message": errorMsg,
                "data": None
            }
            
        except HTTPError as e:
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            status = e.response.status_code if hasattr(e, "response") and e.response is not None else "N/A"
            errorMsg = f"HTTP error {status} querying Wikidata SPARQL endpoint: {e}"
            logger.error(
                f"[Wikidata] {errorMsg} for Q-ID='{cleanQid}' / GND='{cleanGnd}' ({elapsedMs}ms)",
                exc_info=True
            )
            return {
                "status": "error",
                "message": errorMsg,
                "data": None
            }
            
        except Exception as e:
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            errorMsg = f"Unexpected error querying Wikidata SPARQL endpoint: {e}"
            logger.error(
                f"[Wikidata] {errorMsg} for Q-ID='{cleanQid}' / GND='{cleanGnd}' ({elapsedMs}ms)",
                exc_info=True
            )
            return {
                "status": "error",
                "message": errorMsg,
                "data": None
            }

        # phase 3: parse binding rows and verify returned bindings exist
        bindings = sparqlData.get("results", {}).get("bindings", [])
        if not bindings:
            logger.info(f"[Wikidata] No Wikidata bindings/entry found for Q-ID='{cleanQid}' / GND='{cleanGnd}' ({elapsedMs}ms)")
            return {
                "status": "not_found",
                "message": f"No entity record found in Wikidata for Q-ID='{cleanQid}' or GND='{cleanGnd}'",
                "data": None
            }

        logger.debug(f"[Wikidata] Received {len(bindings)} SPARQL binding row(s) from endpoint ({elapsedMs}ms)")

        # extract resolved q-id and group properties into lists
        resolvedQid, rawClaims = self._parseSparqlBindings(bindings)
        logger.info(
            f"[Wikidata] Resolved entity Q-ID='{resolvedQid}' with {len(rawClaims)} property claim category/categories"
        )

        # inject marc21 nametype if present so resolvewikidata type routes directly
        if nameType:
            rawClaims["wikidataType"] = nameType
            logger.debug(f"[Wikidata] Injected explicit MARC21 nameType '{nameType}' into claims map")

        try:
            # phase 4: validate payload into Pydantic model
            validatedModel = DataWikidata(
                wikidataId=resolvedQid,
                wikidataInformation=rawClaims,
            )
            logger.info(f"[Wikidata] Successfully validated DataWikidata model for Q-ID='{resolvedQid}' ({elapsedMs}ms)")
            return {
                "status": "success",
                "message": f"Successfully retrieved Wikidata entity for Q-ID '{resolvedQid}'",
                "data": validatedModel
            }
            
        except Exception as e:
            errorMsg = f"Pydantic validation error constructing DataWikidata for Q-ID='{resolvedQid}': {e}"
            logger.error(f"[Wikidata] {errorMsg}", exc_info=True)
            return {
                "status": "error",
                "message": errorMsg,
                "data": None
            }


    def _buildSparqlQuery(self, wikidataId: str | None, gndId: str | None) -> str:
        """Constructs a targeted SPARQL query using the official Wikidata label service for german results."""
        if wikidataId:
            qidURI = f"wd:{wikidataId}" if not wikidataId.startswith("http") else f"<{wikidataId}>"
            subjectClause = f"BIND({qidURI} AS ?item)"
        else:
            subjectClause = f'?item wdt:P227 "{gndId}" .'

        return f"""
        SELECT ?item ?itemLabel ?property ?value ?valueLabel WHERE {{
          {subjectClause}

          ?item ?p ?statement .
          ?statement ?ps ?rawVal .
          
          ?property wikibase:claim ?p .
          ?property wikibase:statementProperty ?ps .
          
          # bind raw value for label service resolution
          BIND(?rawVal AS ?value)

          # wikibase label service automatically fetches german labels (with english fallback) 
          # for ?item and any entity referenced in ?value
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "de,en". }}
        }}
        """


    def _parseSparqlBindings(self, bindings: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
        """Group flat SPARQL binding rows into property lists mapped by P-ID (e.g. 'P31') and label."""
        claims: dict[str, Any] = {}
        resolvedQid = ""

        for row in bindings:
            # extract q-id from entity uri (e.g., http://www.wikidata.org/entity/Q1035 -> Q1035)
            if not resolvedQid and "item" in row:
                itemUri = row["item"]["value"]
                resolvedQid = itemUri.rsplit("/", 1)[-1]

            # extract primary entity label provided by the label service
            if "label" not in claims and "itemLabel" in row:
                lbl = row["itemLabel"].get("value", "").strip()
                if lbl:
                    claims["label"] = lbl

            # extract property p-id from uri
            propUri = row.get("property", {}).get("value", "")
            propPid = propUri.rsplit("/", 1)[-1]

            # prefer valueLabel if resolved by label service, otherwise fallback to value node
            valNode = row.get("valueLabel", {}) or row.get("value", {})
            val = valNode.get("value", "").strip()

            # if valueLabel returned a raw Q-ID URL instead of a text label, extract the short Q-ID
            if val.startswith("http://www.wikidata.org/entity/"):
                val = val.rsplit("/", 1)[-1]

            # append value to corresponding property list safely
            if propPid and val:
                claims.setdefault(propPid, [])
                if val not in claims[propPid]:
                    claims[propPid].append(val)

        return resolvedQid or "UNKNOWN", claims