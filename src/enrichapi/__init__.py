"""
# Bibliographic Metadata Enrichment API (`enrichapi`)

`enrichapi` is a modular FastAPI service designed to fetch, parse, and asynchronously 
enrich bibliographic records from institutional providers like the Austrian National 
Library (**ÖNB**).

---

## Core Capabilities

### Primary Identifier & Bypass Lookup
* **Flexible Identification**: Search via ÖNB record identifiers (**AC-Number**) or **Barcode**.
* **Direct Identifier Bypasses**: Allows immediate enrichment using known **GND IDs**, **Wikidata QIDs**, or **ISBNs**, bypassing preliminary searches.

### Multi-Source Asynchronous Enrichment
* **MARC21 SRU Core**: Sequential extraction and parsing of core bibliographic MARC21 XML records.
* **Lobid GND API**: Fetches authority data for authors, corporate entities, and events.
* **Wikidata SPARQL**: Queries structured knowledge graphs using GND or Wikidata QIDs.
* **Cover Art & Descriptions**: Fetches book covers (via Open Library) and abstracts/descriptions (via Google Books / Open Library).

### Granular Subsidiary SRU Discovery
Find related bibliographic records using targeted subsidiary SRU strategies:
* **By Author Name** (`fetchSimilarByAuthor`)
* **By Subject Headings** (`fetchSimilarBySubject`)
* **By Classification System** (`fetchSimilarByClassification`)
* Control output volume per strategy using configurable limit bounds (`maxRecs`).

---

## Architectural Overview

Requests are dispatched dynamically using a **two-tier polymorphic discriminator**:
1. **Category level** (`iType`): e.g., `"bib"` (Bibliographic Category)
2. **Institution level** (`iName`): e.g., `"oenb"` (Austrian National Library)

Incoming payloads are validated via Pydantic (`EnrichmentRequest`) and processed concurrently via `asyncio.gather` for minimal response latency.
"""

__version__ = "0.1.0"