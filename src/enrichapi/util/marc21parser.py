from lxml import etree

nsMap = {"marc": "http://www.loc.gov/MARC21/slim"}

def extractSubfield(
    record: etree._Element, 
    tag: str | None, 
    code: str, 
    ind1: str | None = None, 
    ind2: str | None = None    
) -> str | None:
    """Extracts a single subfield text value cleanly."""
    if not tag:
        return None
        
    query = f'marc:datafield[@tag="{tag}"]'
    if ind1 is not None: 
        query += f'[@ind1="{ind1}"]'
    if ind2 is not None: 
        query += f'[@ind2="{ind2}"]'
    query += f'/marc:subfield[@code="{code}"]'
    
    elem = record.find(query, namespaces=nsMap)
    return elem.text.strip() if (elem is not None and elem.text) else None


def extractSubfieldsList(
    record: etree._Element, 
    tag: str, 
    code: str, 
    ind1: str | None = None, 
    ind2: str | None = None
) -> list[str]:
    """Extracts all matching subfields across repeating datafields, with optional indicator filtering."""
    if not tag:
        return []
        
    query = f'marc:datafield[@tag="{tag}"]'
    if ind1 is not None:
        query += f'[@ind1="{ind1}"]'
    if ind2 is not None:
        query += f'[@ind2="{ind2}"]'
    query += f'/marc:subfield[@code="{code}"]'

    elems = record.findall(query, namespaces=nsMap)
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

def extractGenreForms(marcRecord: etree._Element) -> list[str]:
    return extractSubfieldsList(marcRecord, "655", "a", ind1=" ", ind2="7")

def extractSubjectHeadings(marcRecord: etree._Element) -> list[str]:
    # extract all 650 $a
    sh650 = extractSubfieldsList(marcRecord, "650", "a")
    
    # extract 689 $a only where ind2 is not " "
    sh689Elems = marcRecord.xpath(
        'marc:datafield[@tag="689" and (@ind2 and @ind2!=" ")]/marc:subfield[@code="a"]',
        namespaces=nsMap
    )
    sh689 = [e.text.strip() for e in sh689Elems if e.text and e.text.strip()]
    
    # combine and deduplicate while preserving order
    return list(dict.fromkeys(sh650 + sh689))


def extractClassificationNumbers(marcRecord: etree._Element) -> list[dict]:
    fieldDataList = []

    for classElem in marcRecord.xpath('marc:datafield[@tag="082" or @tag="084"]', namespaces=nsMap):
        sfa = classElem.find('marc:subfield[@code="a"]', namespaces=nsMap)
        classNum = sfa.text.strip() if (sfa is not None and sfa.text) else None

        # proceed only if extracted classification number
        if not classNum:
            continue

        tag = classElem.attrib.get("tag", "")
        if tag == "082":
            classType = "ddc"
        else:
            sf2 = classElem.find('marc:subfield[@code="2"]', namespaces=nsMap)
            classType = sf2.text.strip() if (sf2 is not None and sf2.text) else "other"

        fieldDataList.append({
            "classificationType": classType,
            "classificationNumber": classNum
        })

    return fieldDataList

def extractFullTextURLs(marcRecord: etree._Element) -> list[str]:
    ftuList = []

    for df856Elem in marcRecord.findall('marc:datafield[@tag="856"]', namespaces=nsMap):
        sf3 = df856Elem.find('marc:subfield[@code="3"]', namespaces=nsMap)
        sfu = df856Elem.find('marc:subfield[@code="u"]', namespaces=nsMap)

        if sfu is None or not sfu.text or not sfu.text.strip():
            continue

        # clean text values
        sf3Text = sf3.text.strip() if (sf3 is not None and sf3.text) else ""
        url = sfu.text.strip()

        # check for 'Volltext' in subfield $3 (case-insensitive & whitespace trimmed)
        if "volltext" in sf3Text.lower():
            ftuList.append(url)

    # return deduplicated list while preserving order
    return list(dict.fromkeys(ftuList))

def extractAbstracts(marcRecord: etree._Element) -> list[str]:
    return extractSubfieldsList(marcRecord, "520", "a")

def extractTableOfContentURLs(marcRecord: etree._Element) -> list[str]:
    tocList = []

    for df856Elem in marcRecord.findall('marc:datafield[@tag="856"]', namespaces=nsMap):
        sf3 = df856Elem.find('marc:subfield[@code="3"]', namespaces=nsMap)
        sfu = df856Elem.find('marc:subfield[@code="u"]', namespaces=nsMap)

        if sfu is None or not sfu.text or not sfu.text.strip():
            continue

        # clean text values
        sf3Text = sf3.text.strip() if (sf3 is not None and sf3.text) else ""
        url = sfu.text.strip()

        # check for 'Inhaltsverzeichnis' in subfield $3 (case-insensitive & whitespace trimmed)
        if "inhaltsverzeichnis" in sf3Text.lower():
            tocList.append(url)

    # return deduplicated list while preserving order
    return list(dict.fromkeys(tocList))

