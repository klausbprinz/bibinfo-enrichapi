import asyncio
from httpx import AsyncClient
from .models.request import OeNBRequestData
from .models.response import OenbResponse

# TODO: implement other services
from .services.sruService import SruService
from .services.lobidService import LobidService
from .services.wikidataService import WikidataService


async def baseFetchOeNB(data: OeNBRequestData) -> OenbResponse:
    
    async with AsyncClient() as client:
        
        # initialize helper pipeline services
        sruService = SruService(client)
        lobidService = LobidService(client)
        wikidataService = WikidataService(client)
        
        extractedGnd: str | None = data.gndId
        extractedWikidata: str | None = data.wikidataId
        
        marcData = None

        # gather core identifiers sequentially
        if data.fetchMarc21MD:
            marcXml = await sruService.fetchRecord(data.identifier, data.identifierType)
            if marcXml is not None:
                marcData = sruService.extractMarc21Metadata(marcXml)
                
                if not extractedGnd and marcData.mainEntry:
                    extractedGnd = marcData.mainEntry.gndIdentifier


        # spin up all background tasks in parallel
        tasks = []
        taskMappings = {}

        # subsidiary query task in parallel worker pool
        if marcData and (data.fetchSimilarByAuthor or data.fetchSimilarBySubject or data.fetchSimilarByClassification):
            tasks.append(sruService.fetchAdditionalRecords(marcData, data))
            taskMappings["similarRecs"] = len(tasks) - 1

        if data.fetchLobidGND and extractedGnd:
            tasks.append(lobidService.fetchGndData(extractedGnd))
            taskMappings["lobid"] = len(tasks) - 1
            
        if data.fetchWikidata and (extractedWikidata or extractedGnd):
            tasks.append(wikidataService.fetchWikidata(extractedWikidata, extractedGnd))
            taskMappings["wikidata"] = len(tasks) - 1

        # fire concurrent requests simultaneously
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # safe dynamic result mapping
        additionalRecs = (
            results[taskMappings["similarRecs"]] 
            if "similarRecs" in taskMappings and not isinstance(results[taskMappings["similarRecs"]], Exception) 
            else None
        )
        lobidRes = (
            results[taskMappings["lobid"]] 
            if "lobid" in taskMappings and not isinstance(results[taskMappings["lobid"]], Exception) 
            else None
        )
        wikidataRes = (
            results[taskMappings["wikidata"]] 
            if "wikidata" in taskMappings and not isinstance(results[taskMappings["wikidata"]], Exception) 
            else None
        )

        return OenbResponse(
            identifier=data.identifier,
            identifierType=data.identifierType,
            basicMarc21MD=marcData,
            additionalRecsSRU=additionalRecs,
            gndInfoLobid=lobidRes,
            wikidataData=wikidataRes
        )