---
projectName: "bibinfo-enrichapi"
author: "Klaus Prinz"
domain: "software"
status: "active"
createdDate: "2026-06-03"
tags: [fastapi, pydantic, lxml, marcxml, json, json schema, swagger, sparql, httpx, async, asyncio, wikidata, containerfile, pdoc, unit test, pytest]
requester: "bibinfo"
ticketId: ""
---

# bibinfo-enrichapi

> **Quick Summary:** A modular FastAPI service designed to fetch, parse, and asynchronously enrich library MARC21 bibliographic records (ÖNB/SRU) with linked data authority files (Lobid GND), knowledge graphs (Wikidata SPARQL), Open Library book covers, and Google Books abstracts.

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

### Example usage
Start the API server, open `notebooks/exampleUsage.ipynb`, and run all cells.

---


## Context & Objectives
`bibinfo-enrichapi` provides a unified JSON endpoint (`POST /enrich`) for fetching and augmenting MARC21 bibliographic data with external authority services.

- Sequential Phase 1 (Core Retrieval): Queries institutional SRU servers (such as the ÖNB - Austrian National Library) by AC-Number or Barcode to retrieve raw MARC21 XML, which is parsed into structured Pydantic models.
- Parallel Phase 2 (Async Concurrent Enrichment): Uses non-blocking `asyncio.gather` with `httpx` to concurrently fetch:
    - Lobid GND API: Authority record information for authors, entities, and events.
    - Wikidata SPARQL: Structured graph metadata using GND identifiers or Wikidata QIDs.
    - Book Covers & Abstracts: Cover images (Open Library) and descriptions (Google Books / Open Library).
    - Subsidiary SRU Discovery: Related books matched by author name, subject headings, or classification codes.
- Direct ID Bypasses: Support for direct lookup using known GND IDs, Wikidata QIDs, or ISBNs without needing prior SRU discovery.
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
│   └── build_docs.py           # Combined JSON Schema & pdoc HTML build script
├── src/                        # Main application package source
│   └── enrichapi/
│       ├── models/             # Pydantic request & response models
│       ├── services/           # Async HTTP services (SRU, Lobid, Wikidata, etc.)
│       ├── utils/              # Pure domain helpers (MARC21 XML parser)
│       ├── handlers.py         # Enrichment strategy execution pipeline
│       └── main.py             # FastAPI entrypoint and router definitions
├── tests/                      # Unit & integration test suite
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
python scripts/build_docs.py
```
---

## Dependencies & Requirements
- Python: `>= 3.10`
- Core Framework: `fastapi`, `uvicorn[standard]`
- Data Validation: `pydantic`
- Async I/O & Parsing: `httpx`, `lxml`
- Development & Testing: `pytest`, `pytest-cov`, `pdoc`

---

## Notes & Future TODOs
Not now.

---