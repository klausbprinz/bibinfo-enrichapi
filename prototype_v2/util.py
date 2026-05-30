import httpx

from responseModels import OeNBResponse

async def getSecondaryDataLobid(resData: OeNBResponse) -> OeNBResponse:

    url = f'https://lobid.org/gnd/{resData.metadata.gndID.replace("(DE-588)", "")}.json'
    
    async with httpx.AsyncClient() as client:

        res = await client.get(url)
        res.raise_for_status()
        
        resDict = res.json()

        resData.metadata.titlesGND = resDict.get("publication", [])

    return resData