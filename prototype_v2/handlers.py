from dataModels import OeNB
from responseModels import OeNBResponse

from getBaseMD import getBaseMetadataOeNB

from util import getSecondaryDataLobid

async def baseFetchOeNB(data: OeNB) -> OeNBResponse:

    # fetch base metadata first
    fetchedMetadata = await getBaseMetadataOeNB(data.barcode)

    # then initialize response object with required fields
    resData = OeNBResponse(
        barcode=data.barcode,
        metadata=fetchedMetadata
    )

    if resData.metadata.gndID:
        resData = await getSecondaryDataLobid(resData)

    return resData