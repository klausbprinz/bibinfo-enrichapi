# run with "fastapi dev main.py"

from typing import Annotated, List, Literal
from pydantic import BaseModel, Field
from fastapi import FastAPI, Path

from lxml import etree
import requests

app = FastAPI()


# very basic response data model
class ResponseData(BaseModel):
    
    id: str = Field(description="The ID value")
    idType: Literal["barcode", "callNumber", "acNumber"] = Field(description="The ID type")
    title245: str | None = Field(default=None, description="The title of the resource identified with the ID, extracted from MARC21 field 245_a/b")
    author100: str | None = Field(default=None, description="The author of the resource identified with the ID, extracted from MARC21 field 100_a - if there otherwise null")
    gndID: str | None = Field(default=None, description="The GND-ID of the author of the resource identified with the ID, extracted from MARC21 field 100_0 - if there otherwise null")
    titlesGND: List[str] = Field(default=[], description="Works by the author - fetched via GND-ID via the lobid API")


def getPrimaryDataSRU(resData: ResponseData) -> ResponseData:

    idTypeSearchIndexDict = {
        "barcode": "alma.barcode",
        "callNumber": "alma.PermanentCallNumber",
        "acNumber": "alma.local_control_field_009"
    }

    ns = {"srw": "http://www.loc.gov/zing/srw/", "marc": "http://www.loc.gov/MARC21/slim"}

    url = f'https://obv-at-oenb.alma.exlibrisgroup.com/view/sru/43ACC_ONB?version=1.2&query={idTypeSearchIndexDict[resData.idType]}="{resData.id}"&operation=searchRetrieve'

    res = requests.get(url)
    res.raise_for_status()

    sruRoot = etree.fromstring(res.content)

    recordElemList = sruRoot.findall(".//srw:record", namespaces=ns)

    if len(recordElemList) == 1:
        marcRecordElem = recordElemList[0].find("srw:recordData/marc:record", namespaces=ns)

        title245a = marcRecordElem.find('marc:datafield[@tag="245"]/marc:subfield[@code="a"]', namespaces=ns).text
        title245b = marcRecordElem.find('marc:datafield[@tag="245"]/marc:subfield[@code="b"]', namespaces=ns).text if marcRecordElem.find('marc:datafield[@tag="245"]/marc:subfield[@code="b"]', namespaces=ns) is not None and marcRecordElem.find('marc:datafield[@tag="245"]/marc:subfield[@code="b"]', namespaces=ns).text is not None else ""

        resData.title245 = title245a + title245b
        resData.author100 = marcRecordElem.find('marc:datafield[@tag="100"]/marc:subfield[@code="a"]', namespaces=ns).text if marcRecordElem.find('marc:datafield[@tag="100"]/marc:subfield[@code="a"]', namespaces=ns) is not None and marcRecordElem.find('marc:datafield[@tag="100"]/marc:subfield[@code="a"]', namespaces=ns).text is not None else ""
        resData.gndID = marcRecordElem.find('marc:datafield[@tag="100"]/marc:subfield[@code="0"]', namespaces=ns).text if marcRecordElem.find('marc:datafield[@tag="100"]/marc:subfield[@code="0"]', namespaces=ns) is not None and marcRecordElem.find('marc:datafield[@tag="100"]/marc:subfield[@code="0"]', namespaces=ns).text is not None else ""

    return resData


def getSecondaryDataLobid(resData: ResponseData) -> ResponseData:

    url = f'https://lobid.org/gnd/{resData.gndID.replace("(DE-588)", "")}.json'
    
    res = requests.get(url)
    res.raise_for_status()
    
    resDict = res.json()

    resData.titlesGND = resDict["publication"]

    return resData


# TODO: removed async from async def -> if doing this for real use httpx!

@app.get("/barcode/{barcode}", response_model=ResponseData)
def processBarcode(barcode: Annotated[str, Path(title="Barcode of item", pattern=r"Z\d{5,7}0[X\d]")]):

    resData = ResponseData(id=barcode, idType="barcode") 
    resData = getPrimaryDataSRU(resData)

    if resData.gndID is not None:
        resData = getSecondaryDataLobid(resData)

    return resData

@app.get("/callNumber/{callNumber}", response_model=ResponseData)
def processCallNumber(callNumber: Annotated[str, Path(title="Call number of holdings record")]):         # no validation for now
    
    resData = ResponseData(id=callNumber, idType="callNumber")    
    resData = getPrimaryDataSRU(resData)

    if resData.gndID is not None:
        resData = getSecondaryDataLobid(resData)

    return resData

@app.get("/acNumber/{acNumber}", response_model=ResponseData)
def processAcNumber(acNumber: Annotated[str, Path(title="AC number of bibliographic record", pattern=r"AC\d{8}")]):
    
    resData = ResponseData(id=acNumber, idType="acNumber") 
    resData = getPrimaryDataSRU(resData)

    if resData.gndID is not None:
        resData = getSecondaryDataLobid(resData)

    return resData


