---
projectName: "bibinfo-enrichapi"
author: "Klaus Prinz"
domain: "software"
status: "active"
createdDate: "2026-06-03"
ttags: [fastapi, pydantic, lxml, marcxml, gnd, lobid, json, json schema, swagger, sparql, httpx, async, asyncio, wikidata, containerfile, pdoc, unit test, pytest, polymorphic, sru, pica, status envelope]
requester: "bibinfo"
ticketId: ""
---

# bibinfo-enrichapi

> **Quick Summary:** A modular FastAPI service designed to fetch, parse, and asynchronously enrich library MARC21 bibliographic records across multiple institutional union catalogs (**ÖNB** and **GBV / K10plus**) with linked data authority files (Lobid GND), knowledge graphs (Wikidata SPARQL), and waterfall-modelled book covers and descriptions.

---

## Quick Start & How to Run

### Local Setup & Execution

1. **Clone the repository and navigate into the root:**
```bash
git clone <repository-url>
cd bibinfo-enrichapi
```
2. **Create and activate Conda environment:**
```bash
conda env create -f environment.yaml
conda activate enrichapi
```
3. **Install the package in editable mode with development dependencies:**
```bash
pip install -e .[dev]
```
4. **Launch the development server:**
```bash
fastapi dev src/enrichapi/main.py
```
- Access the interactive Swagger UI docs at `http://127.0.0.1:8000/docs`.
- Access the Redoc UI at `http://127.0.0.1:8000/redoc`.

### Running via Container (Podman/Docker)
You can build and run the service using the `Containerfile` located in `container/`:

1. **Build the container image (run from project root):**
```bash
podman build -f container/Containerfile -t enrichapi:latest .
```
2. **Run the container:**
```bash
podman run -d -p 8000:8000 --name enrichapi enrichapi:latest
```
3. **Open `http://localhost:8000/docs` in your browser.**

---

## Example usage
Start the API server, open `notebooks/exampleUsage.ipynb` or `notebooks/testPipeline.ipynb`, and run all cells.

---


## Context & Objectives
`bibinfo-enrichapi` provides a unified JSON endpoint (`POST /enrich`) for fetching and augmenting MARC21 bibliographic data from multiple library networks using a polymorphic service architecture (`BaseSruService` with `OenbSruService` and `GbvSruService` overrides) and Pydantic generic envelopes (`EnrichmentEnvelope[T]`).

- **Sequential Phase 1 (Core Retrieval)**: Queries institutional SRU servers (ÖNB / Alma or GBV K10plus / PICA) by system identifiers (AC-Number, PPN), Barcodes, or ISBNs (`identifierType: "isbn"`) to retrieve raw MARC21 XML, parsed into structured Pydantic models.
- **Parallel Phase 2 (Async Concurrent Enrichment)**: Uses non-blocking `asyncio.gather` with `httpx` to concurrently fetch:
    - **Lobid GND API**: Authority record information for authors, entities, and events.
    - **Wikidata SPARQL**: Structured graph metadata using GND identifiers or Wikidata QIDs.
    - **Multi-Tier Waterfall Cover Retrieval (`CoverService`)**:
        1. **DNB Cover Endpoint** (Fast lookup for German/Austrian titles via HEAD request)
        2. **Google Books Volumes API** (Fast global lookup with optional API key)
        3. **Open Library Books API** (JSON metadata lookup for Cover ID)
        4. **Open Library Direct Cover Endpoint** (HEAD request fallback)
    - **Multi-Tier Waterfall Description Retrieval (`AbstractService`)**:
        1. **Google Books API** (Fast ISBN lookup with optional API key & strict timeout)
        2. **Open Library Works API** (ISBN $\rightarrow$ Work key $\rightarrow$ Description fallback)
    - **Subsidiary SRU Discovery**: Related books matched by person name (`pica.per` / ÖNB indexes), subject headings, or classification codes (RVK, BKL, DDC) with self-exclusion guardrails.
    - **Direct ID Bypasses**: Support for direct lookup using known GND IDs, Wikidata QIDs, or ISBNs without needing prior SRU discovery.
---

## Project Layout
```text
bibinfo-enrichapi/
├── container/                  # Container deployment files
│   └── Containerfile           # Docker/Podman container definition
├── data/                       # Sample test datasets & conceptual diagrams
│   ├── conceptual/             # Architecture overview diagrams
│   └── test-data/              # Sample MARC21 XML SRU files
├── docs/                       # Project documentation
│   ├── api/                    # Generated pdoc HTML API documentation
│   └── schemas/                # Exported Pydantic JSON Schemas
├── notebooks/                  # Playground & pipeline exploration notebooks
├── scripts/                    # Automation scripts
│   └── buildDocs.py            # Combined JSON Schema & pdoc HTML build script
├── src/                        # Main application package source
│   └── enrichapi/
│       ├── handlers/           # Institution-specific enrichment strategies (oenb, gbv)
│       ├── models/             # Pydantic request & response models
│       ├── services/           # Async HTTP services
│       ├── utils/              # Domain helpers
│       └── main.py             # FastAPI entrypoint and router definitions
├── tests/                      # Unit & integration test suite (not updated)
├── environment.yaml            # Conda environment definition
├── pyproject.toml              # Build backend, dependencies, and tool settings
└── README.md                   # Project landing documentation
```

---

## Testing & Documentation Automation

### Running Tests & Code Coverage
The test suite utilizes `pytest` with `pytest-cov` to verify endpoint validation, MARC21 XML parsing, and async strategy execution:
```bash
# run tests with terminal & HTML coverage report
pytest
```
Another (simpler) option is to lauch the development server, open `notebooks/testPipeline.ipynb`, and run all cells.

### Rebuilding Documentation & Schemas
Regenerate both the JSON Schemas (`docs/schemas/`) and static HTML API documentation (`docs/api/`) in a single step:
```bash
python scripts/buildDocs.py
```
---

## Dependencies & Requirements
- Python: `>= 3.10`
- Core Framework: `fastapi`, `uvicorn[standard]`
- Data Validation: `pydantic` (with generic type support)
- Environment Configuration: `python-dotenv` (for API key management)
- Async I/O & Parsing: `httpx`, `lxml`
- Development & Testing: `pytest`, `pytest-cov`, `pdoc`

---

## Notes & Future TODOs
Not now.

---