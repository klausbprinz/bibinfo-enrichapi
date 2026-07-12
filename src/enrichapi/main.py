# run with "fastapi dev main.py"

from .handlers import baseFetchOeNB
from .models.request import OeNBRequestData, EnrichmentRequest
from .models.response import RootApiResponse, BibliographicLibraryResponse

from fastapi import FastAPI, HTTPException

app = FastAPI()


# registry: map the input class to handler function
ENRICHMENT_STRATEGIES = {
    OeNBRequestData: baseFetchOeNB,
    # could add eg: LibraryOfCongress: baseFetchLOC,
}


@app.post("/enrich", response_model=RootApiResponse)    # using the nested master wrapper
async def enrichData(request: EnrichmentRequest):
    if request.iType == "bib":
        instInput = request.institution
        handler = ENRICHMENT_STRATEGIES.get(type(instInput))
        
        if not handler:
            raise HTTPException(status_code=400, detail="Institution handler not found")
            
        result = await handler(instInput)
        
        # build the exact multi-tier envelope back up matching production layout
        return RootApiResponse(
            response=BibliographicLibraryResponse(result=result)
        )