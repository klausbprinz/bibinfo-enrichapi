# run with "fastapi dev main.py"

from .handlers import baseFetchOeNB
from .dataModels import OeNB, EnrichmentRequest
from .responseModels import EnrichmentResponse, LibraryResponse

from fastapi import FastAPI, HTTPException

app = FastAPI()


# registry: map the input class to handler function
ENRICHMENT_STRATEGIES = {
    OeNB: baseFetchOeNB,
    # could add eg: LibraryOfCongress: baseFetchLOC,
}


@app.post("/enrich", response_model=EnrichmentResponse)
async def enrichData(request: EnrichmentRequest):
    # level 3: Check category (e.g. "bib")
    if request.iType == "bib":
        # level 2: Get the institution input data (e.g., the OeNB instance)
        instInput = request.institution
        
        # level 1: Look up the strategy based on the class type
        handler = ENRICHMENT_STRATEGIES.get(type(instInput))
        
        if not handler:
            raise HTTPException(status_code=400, detail="Institution handler not found")
            
        # Execute handler and wrap it in the top-level LibraryResponse
        result = await handler(instInput)
        return LibraryResponse(result=result)

    raise HTTPException(status_code=400, detail="Unsupported record type")