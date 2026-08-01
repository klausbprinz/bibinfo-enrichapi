# run with "fastapi dev main.py"

import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request

from .handlers import baseFetchOeNB
from .models.request import OeNBRequestData, EnrichmentRequest
from .models.response import RootApiResponse, BibliographicLibraryResponse

# configure central logging format for the entire application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


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
    response_model_by_alias=False
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
            # Re-raise explicit HTTP exceptions without redundant logging
            raise
        except Exception as e:
            elapsedMs = round((time.perf_counter() - startTime) * 1000, 2)
            logger.error(f"[API] Unhandled error during /enrich processing ({elapsedMs}ms): {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error during metadata enrichment processing")

    logger.warning(f"[API] Unsupported request iType='{iType}'")
    raise HTTPException(status_code=400, detail=f"Unsupported iType: '{iType}'")