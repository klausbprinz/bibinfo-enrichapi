import asyncio
import logging
import time
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
    pipelineStartTime = time.perf_counter()
    
    logger.info(
        f"[Handler] Pipeline started | identifier='{data.identifier}' identifierType='{data.identifierType}' "
        f"gndId='{data.gndId}' wikidataId='{data.wikidataId}' isbn='{data.isbn}'"
    )

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
            logger.info(
                f"[Handler] Phase 1: Fetching core MARC21 record sequentially via SRU "
                f"({data.identifierType}='{data.identifier}')..."
            )
            marcStartTime = time.perf_counter()
            try:
                marcXml = await sruService.fetchRecord(data.identifier, data.identifierType)
                if marcXml is not None:
                    marcData = sruService.extractMarc21Metadata(marcXml)
                    
                    # extract GND ID from mainEntry if not explicitly provided in request
                    if not extractedGnd and marcData and marcData.mainEntry:
                        extractedGnd = marcData.mainEntry.gndIdentifier
                        if extractedGnd:
                            logger.info(f"[Handler] Dynamically extracted GND ID '{extractedGnd}' from MARC21 mainEntry")

                marcElapsedMs = round((time.perf_counter() - marcStartTime) * 1000, 2)
                if marcData:
                    logger.info(f"[Handler] Phase 1 Complete: MARC21 record fetched and parsed ({marcElapsedMs}ms)")
                else:
                    logger.warning(f"[Handler] Phase 1 Warning: SRU query succeeded but yielded no MARC21 data ({marcElapsedMs}ms)")

            except Exception as e:
                marcElapsedMs = round((time.perf_counter() - marcStartTime) * 1000, 2)
                logger.error(f"[Handler] Phase 1 Error: Failed processing SRU MARC21 record ({marcElapsedMs}ms): {e}", exc_info=True)
        else:
            logger.debug("[Handler] Phase 1 Skipped: fetchMarc21MD is False or identifier credentials missing")

        # extract nameType from mainEntry (person, corporate, conferenceOrEvent)
        nameType = marcData.mainEntry.nameType if (marcData and marcData.mainEntry) else None
        if nameType:
            logger.debug(f"[Handler] Extracted nameType '{nameType}' from MARC21 mainEntry")

        # convert MARC21 record model to dictionary format expected by cover/abstract services
        marcDict = marcData.model_dump() if marcData else {}

        # spin up all background tasks in parallel
        tasks = []
        taskMappings = {}

        logger.info("[Handler] Phase 2: Assembling parallel background tasks...")

        # subsidiary SRU query task in parallel worker pool
        if marcData and (data.fetchSimilarByAuthor or data.fetchSimilarBySubject or data.fetchSimilarByClassification):
            tasks.append(sruService.fetchAdditionalRecords(marcData, data))
            taskMappings["similarRecs"] = len(tasks) - 1
            logger.debug("[Handler] Enqueued Task: Similar Records (SRU)")

        # Lobid GND task
        if data.fetchLobidGND and extractedGnd:
            tasks.append(lobidService.fetchGndData(extractedGnd))
            taskMappings["lobid"] = len(tasks) - 1
            logger.debug(f"[Handler] Enqueued Task: Lobid GND ('{extractedGnd}')")

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
            logger.debug(f"[Handler] Enqueued Task: Wikidata (qid='{extractedWikidata}', gnd='{extractedGnd}')")

        # Open Library Book Cover task
        if data.fetchCover:
            tasks.append(
                coverService.fetchCover(
                    basicMarcMd=marcDict,
                    bypassIsbn=data.isbn
                )
            )
            taskMappings["cover"] = len(tasks) - 1
            logger.debug("[Handler] Enqueued Task: Book Cover")

        # Google Books / Open Library Description task
        if data.fetchDescription:
            tasks.append(
                abstractService.fetchDescription(
                    basicMarcMd=marcDict,
                    bypassIsbn=data.isbn
                )
            )
            taskMappings["description"] = len(tasks) - 1
            logger.debug("[Handler] Enqueued Task: Book Description")

        # fire concurrent requests simultaneously if any tasks exist
        parallelStartTime = time.perf_counter()
        if tasks:
            logger.info(f"[Handler] Executing {len(tasks)} tasks concurrently via asyncio.gather...")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            parallelElapsedMs = round((time.perf_counter() - parallelStartTime) * 1000, 2)
            logger.info(f"[Handler] Phase 2 Complete: All parallel tasks finished ({parallelElapsedMs}ms)")
        else:
            results = []
            logger.info("[Handler] Phase 2 Skipped: No parallel tasks were queued")

        # safe dynamic result mapping
        def getResult(key):
            if key in taskMappings:
                res = results[taskMappings[key]]
                if isinstance(res, Exception):
                    logger.error(f"[Handler] Task '{key}' failed with exception: {res}", exc_info=res)
                    return None
                status = "SUCCESS" if res is not None else "EMPTY"
                logger.debug(f"[Handler] Result for task '{key}': {status}")
                return res
            return None

        additionalRecs = getResult("similarRecs")
        lobidRes = getResult("lobid")
        wikidataRes = getResult("wikidata")
        coverRes = getResult("cover")
        descriptionRes = getResult("description")

        totalPipelineMs = round((time.perf_counter() - pipelineStartTime) * 1000, 2)
        logger.info(
            f"[Handler] Pipeline successfully completed in {totalPipelineMs}ms | "
            f"Results Summary: MARC21={'YES' if marcData else 'NO'}, "
            f"SimilarRecs={'YES' if additionalRecs else 'NO'}, "
            f"Lobid={'YES' if lobidRes else 'NO'}, "
            f"Wikidata={'YES' if wikidataRes else 'NO'}, "
            f"Cover={'YES' if coverRes else 'NO'}, "
            f"Description={'YES' if descriptionRes else 'NO'}"
        )

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