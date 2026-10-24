# run with "fastapi dev src/enrichapi/main.py"

import os
import logging
from dotenv import load_dotenv

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status

from .handlers import baseFetchOeNB
from .models.request import OeNBRequestData, EnrichmentRequest
from .models.response import RootApiResponse, BibliographicLibraryResponse

# configure central logging format for the entire application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logging.getLogger("httpx").setLevel(logging.WARNING)

# load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# fetch and validate Google API Key (filter out placeholders/dummies)
rawApiKey = os.getenv("GOOGLE_API_KEY")
GOOGLE_API_KEY = None

if rawApiKey:
    # check if its a placeholder or a real key structure (Google keys start with 'AIza')
    isPlaceholder = any(p in rawApiKey.lower() for p in ["your_api_key", "insert_key", "placeholder", "dummy", "xxx"])
    if not isPlaceholder and rawApiKey.startswith("AIza"):
        GOOGLE_API_KEY = rawApiKey
        logger.info("[Startup] Valid Google API Key detected and loaded successfully.")
    else:
        logger.warning("[Startup] GOOGLE_API_KEY found, but it looks like a placeholder/invalid format. Running in anonymous, rate-limited mode.")
else:
    logger.warning("[Startup] No GOOGLE_API_KEY found in .env. Google Books will run in anonymous, rate-limited mode.")

    
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown logging/events."""
    logger.info("=== Starting Bibliographic Metadata Enrichment API ===")
    yield
    logger.info("=== Shutting down Bibliographic Metadata Enrichment API ===")


app = FastAPI(
    title="Bibliographic Metadata Enrichment API",
    version="1.0.0",
    lifespan=lifespan,
)


# Registry: map the input class to handler function
ENRICHMENT_STRATEGIES = {
    OeNBRequestData: baseFetchOeNB,
    # could add eg: LibraryOfCongress: baseFetchLOC,
}


@app.post(
    "/enrich", 
    response_model=RootApiResponse, 
    response_model_by_alias=False,
    summary="Enrich bibliographic records and institutional metadata",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Record not found in the library catalog",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Record with identifier 'AC00000000' not found in catalog."
                    }
                }
            },
        },
        # HTTP 300 multiple choices for ISBN ambiguity
        300: {
            "description": "Multiple records found for the provided ISBN",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ambiguous_isbn",
                        "isbn": "9783161484100",
                        "totalMatches": 2,
                        "candidates": [
                            {"bibId": "AC12345678", "title": "Example Book (1st Ed)", "author": "John Doe", "publishers": ["Academic Press"], "dates": ["2010"]},
                            {"bibId": "AC12345679", "title": "Example Book (2nd Ed)", "author": "John Doe", "publisher": ["Academic Press"], "dates": ["2015"]}
                        ]
                    }
                }
            }
        }
    }
)    # using the nested master wrapper and ensure pydantic field names are used
async def enrichData(request: EnrichmentRequest):
    startTime = time.perf_counter()
    iType = request.iType
    inputType = type(request.institution).__name__
    
    logger.info(f"[API] Incoming POST /enrich request | iType='{iType}' institutionPayload='{inputType}'")

    if iType == "bib":
        instInput = request.institution
        handler = ENRICHMENT_STRATEGIES.get(type(instInput))
        
        if not handler:
            logger.error(f"[API] No handler registered for institution strategy '{inputType}'")
            raise HTTPException(status_code=400, detail=f"Institution handler not found for strategy '{inputType}'")
            
        logger.debug(f"[API] Routing request to handler '{handler.__name__}'")
        
        try:
            result = await handler(instInput)
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            
            logger.info(f"[API] Successfully processed /enrich request in {elapsedMs}ms")
            
            # build the exact multi-tier envelope back up matching production layout
            return RootApiResponse(
                response=BibliographicLibraryResponse(result=result)
            )

        except HTTPException:
            # re-raise explicit HTTP exceptions without redundant logging
            raise
        except Exception as e:
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            logger.error(f"[API] Unhandled error during /enrich processing ({elapsedMs}ms): {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error during metadata enrichment processing")

    logger.warning(f"[API] Unsupported request iType='{iType}'")
    raise HTTPException(status_code=400, detail=f"Unsupported iType: '{iType}'")