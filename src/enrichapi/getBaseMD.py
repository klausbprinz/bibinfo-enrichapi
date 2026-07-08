from .responseModels import BasicBibMetadata
from lxml import etree
from httpx import AsyncClient

async def getBaseMetadataOeNB(barcode: str) -> BasicBibMetadata:

    md = BasicBibMetadata()

    ns = {"srw": "http://www.loc.gov/zing/srw/", "marc": "http://www.loc.gov/MARC21/slim"}

    url = f'https://obv-at-oenb.alma.exlibrisgroup.com/view/sru/43ACC_ONB?version=1.2&query=alma.barcode="{barcode}"&operation=searchRetrieve'

    async with AsyncClient() as client:

        res = await client.get(url)
        res.raise_for_status()

        sruRoot = etree.fromstring(res.content)

        recordElemList = sruRoot.findall(".//srw:record", namespaces=ns)

        if len(recordElemList) == 1:
            marcRecordElem = recordElemList[0].find("srw:recordData/marc:record", namespaces=ns)

            title245a = marcRecordElem.find('marc:datafield[@tag="245"]/marc:subfield[@code="a"]', namespaces=ns).text
            title245b = marcRecordElem.find('marc:datafield[@tag="245"]/marc:subfield[@code="b"]', namespaces=ns).text if marcRecordElem.find('marc:datafield[@tag="245"]/marc:subfield[@code="b"]', namespaces=ns) is not None and marcRecordElem.find('marc:datafield[@tag="245"]/marc:subfield[@code="b"]', namespaces=ns).text is not None else ""

            md.title245 = title245a + title245b
            md.author100 = marcRecordElem.find('marc:datafield[@tag="100"]/marc:subfield[@code="a"]', namespaces=ns).text if marcRecordElem.find('marc:datafield[@tag="100"]/marc:subfield[@code="a"]', namespaces=ns) is not None and marcRecordElem.find('marc:datafield[@tag="100"]/marc:subfield[@code="a"]', namespaces=ns).text is not None else ""
            md.gndID = marcRecordElem.find('marc:datafield[@tag="100"]/marc:subfield[@code="0"]', namespaces=ns).text if marcRecordElem.find('marc:datafield[@tag="100"]/marc:subfield[@code="0"]', namespaces=ns) is not None and marcRecordElem.find('marc:datafield[@tag="100"]/marc:subfield[@code="0"]', namespaces=ns).text is not None else ""

    return md