import logging
from typing import Any
from httpx import AsyncClient, HTTPError
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
            logger.warning("Neither wikidataId nor gndId was provided to WikidataService.")
            return None

        # build SPARQL query
        query = self._buildSparqlQuery(wikidataId, gndId)

        try:
            response = await self.client.get(
                WIKIDATA_SPARQL_URL,
                params={"query": query, "format": "json"},
                headers=HEADERS,
                timeout=10.0,
            )
            response.raise_for_status()
            sparqlData = response.json()

        except HTTPError as e:
            logger.error(f"Failed to query Wikidata SPARQL endpoint: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing Wikidata SPARQL response: {e}")
            return None

        bindings = sparqlData.get("results", {}).get("bindings", [])
        if not bindings:
            logger.info(f"No Wikidata entry found for Q-ID='{wikidataId}' / GND='{gndId}'")
            return None

        # extract resolved Q-ID and group properties into lists
        resolvedQid, rawClaims = self._parseSparqlBindings(bindings)

        # inject MARC21 nameType if present so resolveWikidataType routes directly
        if nameType:
            rawClaims["wikidataType"] = nameType

        try:
            return DataWikidata(
                wikidataId=resolvedQid,
                wikidataInformation=rawClaims,
            )
        except Exception as e:
            logger.error(f"Pydantic validation error constructing DataWikidata: {e}")
            return None

    def _buildSparqlQuery(self, wikidataId: str | None, gndId: str | None) -> str:
        """Constructs a targeted SPARQL SELECT query."""
        if wikidataId:
            qidURI = f"wd:{wikidataId}" if not wikidataId.startswith("http") else f"<{wikidataId}>"
            subjectClause = f"BIND({qidURI} AS ?item)"
        else:
            subjectClause = f'?item wdt:P227 "{gndId}" .'

        return f"""
        SELECT ?item ?property ?value WHERE {{
          {subjectClause}
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

    def _parseSparqlBindings(self, bindings: list[dict[str, Any]]) -> tuple[str, dict[str, list[str]]]:
        """Group flat SPARQL binding rows into property lists mapped by P-ID (e.g. 'P31')."""
        claims: dict[str, list[str]] = {}
        resolvedQid = ""

        for row in bindings:
            # extract Q-ID from entity URI (e.g., http://www.wikidata.org/entity/Q1035 -> Q1035)
            if not resolvedQid and "item" in row:
                itemUri = row["item"]["value"]
                resolvedQid = itemUri.rsplit("/", 1)[-1]

            propUri = row.get("property", {}).get("value", "")
            propPid = propUri.rsplit("/", 1)[-1]  # Extracts 'P31', 'P106', etc.

            valNode = row.get("value", {})
            val = valNode.get("value", "")

            # if the value URI is a Wikidata entity, extract label/Q-ID cleanly
            if val.startswith("http://www.wikidata.org/entity/"):
                val = val.rsplit("/", 1)[-1]

            if propPid and val:
                claims.setdefault(propPid, [])
                if val not in claims[propPid]:
                    claims[propPid].append(val)

        return resolvedQid or "UNKNOWN", claims