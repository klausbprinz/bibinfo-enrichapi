import asyncio
import logging
from httpx import AsyncClient
from .models.request import OeNBRequestData
from .models.response import OenbResponse

from .services.sruService import SruService
from .services.lobidService import LobidService
from .services.wikidataService import WikidataService
from .services.coverService import CoverService
from .services.abstractService import AbstractService

logger = logging.getLogger(__name__)

async def baseFetchOeNB(data: OeNBRequestData) -> OenbResponse:
    
    async with AsyncClient() as client:
        
        # initialize helper pipeline services sharing the active client connection
        sruService = SruService(client)
        lobidService = LobidService(client)
        wikidataService = WikidataService(client)
        coverService = CoverService(client)
        abstractService = AbstractService(client)
        
        extractedGnd: str | None = data.gndId
        extractedWikidata: str | None = data.wikidataId
        
        marcData = None

        # fetch core MARC21 record sequentially if requested and identifiers exist
        if data.fetchMarc21MD and data.identifier and data.identifierType:
            try:
                marcXml = await sruService.fetchRecord(data.identifier, data.identifierType)
                if marcXml is not None:
                    marcData = sruService.extractMarc21Metadata(marcXml)
                    
                    # extract GND ID from mainEntry if not explicitly provided in request
                    if not extractedGnd and marcData and marcData.mainEntry:
                        extractedGnd = marcData.mainEntry.gndIdentifier

            except Exception as e:
                logger.error(f"Error processing SRU MARC21 record: {e}")

        # extract nameType from mainEntry (person, corporate, conferenceOrEvent)
        nameType = marcData.mainEntry.nameType if (marcData and marcData.mainEntry) else None

        # convert MARC21 record model to dictionary format expected by cover/abstract services
        marcDict = marcData.model_dump() if marcData else {}

        # spin up all background tasks in parallel
        tasks = []
        taskMappings = {}

        # subsidiary SRU query task in parallel worker pool
        if marcData and (data.fetchSimilarByAuthor or data.fetchSimilarBySubject or data.fetchSimilarByClassification):
            tasks.append(sruService.fetchAdditionalRecords(marcData, data))
            taskMappings["similarRecs"] = len(tasks) - 1

        # Lobid GND task
        if data.fetchLobidGND and extractedGnd:
            tasks.append(lobidService.fetchGndData(extractedGnd))
            taskMappings["lobid"] = len(tasks) - 1

        # Wikidata task
        if data.fetchWikidata and (extractedWikidata or extractedGnd):
            tasks.append(
                wikidataService.fetchWikidata(
                    wikidataId=extractedWikidata,
                    gndId=extractedGnd,
                    nameType=nameType,
                )
            )
            taskMappings["wikidata"] = len(tasks) - 1

        # Open Library Book Cover task
        if data.fetchCover:
            tasks.append(
                coverService.fetchCover(
                    basicMarcMd=marcDict,
                    bypassIsbn=data.isbn
                )
            )
            taskMappings["cover"] = len(tasks) - 1

        # Google Books / Open Library Description task
        if data.fetchDescription:
            tasks.append(
                abstractService.fetchDescription(
                    basicMarcMd=marcDict,
                    bypassIsbn=data.isbn
                )
            )
            taskMappings["description"] = len(tasks) - 1

        # fire concurrent requests simultaneously if any tasks exist
        results = await asyncio.gather(*tasks, return_exceptions=True) if tasks else []

        # safe dynamic result mapping
        def getResult(key):
            if key in taskMappings:
                res = results[taskMappings[key]]
                if not isinstance(res, Exception):
                    return res
                logger.error(f"Task '{key}' raised an exception: {res}")
            return None

        additionalRecs = getResult("similarRecs")
        lobidRes = getResult("lobid")
        wikidataRes = getResult("wikidata")
        coverRes = getResult("cover")
        descriptionRes = getResult("description")

        return OenbResponse(
            identifier=data.identifier,
            identifierType=data.identifierType,
            basicMarc21MD=marcData,
            additionalRecsSRU=additionalRecs,
            gndInfoLobid=lobidRes,
            wikidataData=wikidataRes,
            bookCover=coverRes,
            bookDescription=descriptionRes
        )