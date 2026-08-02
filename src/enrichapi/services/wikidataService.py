import logging
import time
from typing import Any
from httpx import AsyncClient, HTTPError, TimeoutException
from ..models.wikidata import DataWikidata

logger = logging.getLogger(__name__)

WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"

# User-Agent is required by Wikidata's API policy, otherwise requests get blocked (403/429)
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
    ) -> DataWikidata | None:
        """
        Fetches Wikidata entity claims using either a direct Q-ID or a GND ID lookup.
        """
        if not wikidataId and not gndId:
            logger.warning("[Wikidata] Neither wikidataId nor gndId was provided to WikidataService.")
            return None

        cleanQid = wikidataId.strip() if wikidataId else None
        cleanGnd = gndId.strip() if gndId else None

        logger.info(
            f"[Wikidata] Initiating entity fetch | qid='{cleanQid}' gndId='{cleanGnd}' nameType='{nameType}'"
        )

        # build SPARQL query
        query = self._buildSparqlQuery(cleanQid, cleanGnd)
        logger.debug(f"[Wikidata] Constructed SPARQL Query:\n{query}")

        startTime = time.perf_counter()

        try:
            response = await self.client.get(
                WIKIDATA_SPARQL_URL,
                params={"query": query, "format": "json"},
                headers=HEADERS,
                timeout=10.0,
            )
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            response.raise_for_status()
            logger.debug(f"[Wikidata] HTTP {response.status_code} received from SPARQL endpoint ({elapsedMs}ms)")
            
            sparqlData = response.json()

        except TimeoutException:
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            logger.error(f"[Wikidata] Timeout after {elapsedMs}ms querying SPARQL endpoint for Q-ID='{cleanQid}' / GND='{cleanGnd}'")
            return None
        except HTTPError as e:
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            status = e.response.status_code if hasattr(e, "response") and e.response is not None else "N/A"
            logger.error(
                f"[Wikidata] Failed to query Wikidata SPARQL endpoint (HTTP {status}) "
                f"for Q-ID='{cleanQid}' / GND='{cleanGnd}' ({elapsedMs}ms): {e}",
                exc_info=True
            )
            return None
        except Exception as e:
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            logger.error(
                f"[Wikidata] Unexpected error parsing Wikidata SPARQL response "
                f"for Q-ID='{cleanQid}' / GND='{cleanGnd}' ({elapsedMs}ms): {e}",
                exc_info=True
            )
            return None

        bindings = sparqlData.get("results", {}).get("bindings", [])
        if not bindings:
            logger.info(f"[Wikidata] No Wikidata bindings/entry found for Q-ID='{cleanQid}' / GND='{cleanGnd}' ({elapsedMs}ms)")
            return None

        logger.debug(f"[Wikidata] Received {len(bindings)} SPARQL binding row(s) from endpoint ({elapsedMs}ms)")

        # extract resolved Q-ID and group properties into lists
        resolvedQid, rawClaims = self._parseSparqlBindings(bindings)
        logger.info(
            f"[Wikidata] Resolved entity Q-ID='{resolvedQid}' with {len(rawClaims)} property claim category/categories"
        )

        # inject MARC21 nameType if present so resolveWikidataType routes directly
        if nameType:
            rawClaims["wikidataType"] = nameType
            logger.debug(f"[Wikidata] Injected explicit MARC21 nameType '{nameType}' into claims map")

        try:
            validatedModel = DataWikidata(
                wikidataId=resolvedQid,
                wikidataInformation=rawClaims,
            )
            logger.info(f"[Wikidata] Successfully validated DataWikidata model for Q-ID='{resolvedQid}' ({elapsedMs}ms)")
            return validatedModel
        except Exception as e:
            logger.error(f"[Wikidata] Pydantic validation error constructing DataWikidata for Q-ID='{resolvedQid}': {e}", exc_info=True)
            return None


    def _buildSparqlQuery(self, wikidataId: str | None, gndId: str | None) -> str:
        """Constructs a targeted SPARQL SELECT query with clean label extraction."""
        if wikidataId:
            qidURI = f"wd:{wikidataId}" if not wikidataId.startswith("http") else f"<{wikidataId}>"
            subjectClause = f"BIND({qidURI} AS ?item)"
        else:
            subjectClause = f'?item wdt:P227 "{gndId}" .'

        return f"""
        SELECT ?item ?itemLabel ?property ?value WHERE {{
          {subjectClause}
          
          # Explicitly grab DE label, fallback to EN label (no row multiplication)
          OPTIONAL {{ ?item rdfs:label ?labelDe . FILTER(LANG(?labelDe) = "de") }}
          OPTIONAL {{ ?item rdfs:label ?labelEn . FILTER(LANG(?labelEn) = "en") }}
          BIND(COALESCE(?labelDe, ?labelEn, "") AS ?itemLabel)

          ?item ?p ?statement .
          ?statement ?ps ?rawVal .
          
          ?property wikibase:claim ?p .
          ?property wikibase:statementProperty ?ps .
          
          OPTIONAL {{
            ?rawVal rdfs:label ?valueLabel .
            FILTER(LANG(?valueLabel) IN ("de", "en"))
          }}
          BIND(COALESCE(?valueLabel, ?rawVal) AS ?value)
        }}
        """


    def _parseSparqlBindings(self, bindings: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
        """Group flat SPARQL binding rows into property lists mapped by P-ID (e.g. 'P31') and label."""
        claims: dict[str, Any] = {}
        resolvedQid = ""

        for row in bindings:
            # extract Q-ID from entity URI (e.g., http://www.wikidata.org/entity/Q1035 -> Q1035)
            if not resolvedQid and "item" in row:
                itemUri = row["item"]["value"]
                resolvedQid = itemUri.rsplit("/", 1)[-1]

            # extract primary entity label if available and not yet set
            if "label" not in claims and "itemLabel" in row:
                lbl = row["itemLabel"].get("value", "").strip()
                if lbl:
                    claims["label"] = lbl

            propUri = row.get("property", {}).get("value", "")
            propPid = propUri.rsplit("/", 1)[-1]  # Extracts 'P31', 'P106', etc.

            valNode = row.get("value", {})
            val = valNode.get("value", "")

            if val.startswith("http://www.wikidata.org/entity/"):
                val = val.rsplit("/", 1)[-1]

            if propPid and val:
                claims.setdefault(propPid, [])
                if val not in claims[propPid]:
                    claims[propPid].append(val)

        return resolvedQid or "UNKNOWN", claims