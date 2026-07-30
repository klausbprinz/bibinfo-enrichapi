from lxml import etree

nsMap = {"marc": "http://www.loc.gov/MARC21/slim"}

def extractSubfield(record: etree._Element, tag: str | None, code: str, ind1: str = None, ind2: str = None) -> str | None:
    """Extracts a single subfield text value cleanly."""
    if not tag:
        return None
        
    query = f'marc:datafield[@tag="{tag}"]'
    if ind1: query += f'[@ind1="{ind1}"]'
    if ind2: query += f'[@ind2="{ind2}"]'
    query += f'/marc:subfield[@code="{code}"]'
    
    elem = record.find(query, namespaces=nsMap)
    return elem.text.strip() if (elem is not None and elem.text) else None


def extractSubfieldsList(record: etree._Element, tag: str, code: str) -> list[str]:
    """Extracts all matching subfields across repeating datafields (e.g. Subject Headings 650$a)."""
    elems = record.findall(f'marc:datafield[@tag="{tag}"]/marc:subfield[@code="{code}"]', namespaces=nsMap)
    return [e.text.strip() for e in elems if e.text and e.text.strip()]


def extractTitleData(marcRecord: etree._Element) -> tuple[str | None, str | None, list[str], list[str]]:

    return (
        extractSubfield(marcRecord, "245", "a"),
        extractSubfield(marcRecord, "245", "b"),
        extractSubfieldsList(marcRecord, "245", "n"),
        extractSubfieldsList(marcRecord, "245", "p")
    )

def extractEntryData(field: etree._Element) -> dict | None:
    """Parses raw text and GND IDs from a single 1xx or 7xx datafield element."""
    sfa = field.find('marc:subfield[@code="a"]', namespaces=nsMap)
    name = sfa.text.strip() if (sfa is not None and sfa.text) else None
    
    if not name:
        return None

    relatorElems = field.findall('marc:subfield[@code="4"]', namespaces=nsMap)
    relators = [e.text.strip() for e in relatorElems if e.text]

    gndElem = field.find('marc:subfield[@code="0"]', namespaces=nsMap)
    gndRaw = gndElem.text if (gndElem is not None and gndElem.text) else None
    gndClean = gndRaw.replace("(DE-588)", "").strip() if gndRaw else None

    return {
        "name": name,
        "relator": relators,
        "gndIdentifier": gndClean
    }

def extractLanguageCodes(marcRecord: etree._Element) -> list[str]:
    return extractSubfieldsList(marcRecord, "041", "a")

def extractLanguageCodesOriginal(marcRecord: etree._Element) -> list[str]:
    return extractSubfieldsList(marcRecord, "041", "h")

def extractPublicationCountryCodes(marcRecord: etree._Element) -> list[str]:
    return extractSubfieldsList(marcRecord, "044", "c")

def extractEdition(marcRecord: etree._Element) -> str | None:
    return extractSubfield(marcRecord, "250", "a")

def extractPhysicalDescriptions(marcRecord: etree._Element) -> list[dict]:

    fieldDataList = []

    for df300 in marcRecord.findall('marc:datafield[@tag="300"]', namespaces=nsMap):
        sfa = df300.find('marc:subfield[@code="a"]', namespaces=nsMap)
        sfb = df300.find('marc:subfield[@code="b"]', namespaces=nsMap)
        sfc = df300.find('marc:subfield[@code="c"]', namespaces=nsMap)

        physDescDict = {
            "extent": sfa.text.strip() if (sfa is not None and sfa.text) else None,
            "otherPhysDetails": sfb.text.strip() if (sfb is not None and sfb.text) else None,
            "dimensions": sfc.text.strip() if (sfc is not None and sfc.text) else None,
        }

        # only append if at least one field has actual data
        if any(physDescDict.values()):
            fieldDataList.append(physDescDict)

    return fieldDataList

def extractPublicationNotices(marcRecord: etree._Element) -> list[dict]:

    fieldDataList = []

    for df264 in marcRecord.findall('marc:datafield[@tag="264"]', namespaces=nsMap):
        ind1 = df264.attrib.get("ind1", " ")
        ind2 = df264.attrib.get("ind2", " ")
        sf3 = df264.find('marc:subfield[@code="3"]', namespaces=nsMap)
        sfaElemList = df264.findall('marc:subfield[@code="a"]', namespaces=nsMap)
        sfbElemList = df264.findall('marc:subfield[@code="b"]', namespaces=nsMap)
        sfcElemList = df264.findall('marc:subfield[@code="c"]', namespaces=nsMap)

        pubNoteDict = {
            "pnType": "current" if (ind1 == "3" and ind2 == "1") else "other",
            "dating": sf3.text.strip() if (sf3 is not None and sf3.text) else None,
            "places": [e.text.strip() for e in sfaElemList if e.text and e.text.strip()],
            "names": [e.text.strip() for e in sfbElemList if e.text and e.text.strip()],
            "dates": [e.text.strip() for e in sfcElemList if e.text and e.text.strip()]
        }

        # guard against appending empty structures
        if pubNoteDict["dating"] or pubNoteDict["places"] or pubNoteDict["names"] or pubNoteDict["dates"]:
            fieldDataList.append(pubNoteDict)

    return fieldDataList
    

