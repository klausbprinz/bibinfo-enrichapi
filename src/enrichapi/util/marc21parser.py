from lxml import etree

from .almaType import getBibMaterialType, getResourceType

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

def extractIdentifier(marcRecord: etree._Element) -> list[dict]:
    fieldDataList = []

    xpathQuery = (
        'marc:datafield[@tag="020" or @tag="022" or @tag="024" or @tag="035"] | '
        'marc:controlfield[@tag="001" or @tag="009"]'
    )

    for idElem in marcRecord.xpath(xpathQuery, namespaces=nsMap):
        identifier = None
        idType = None
        prefix = None
        additionalInfos = []
        tag = idElem.attrib.get("tag", "")

        if idElem.tag.endswith("datafield"):
            sfa = idElem.find('marc:subfield[@code="a"]', namespaces=nsMap)
            identifier = sfa.text.strip() if (sfa is not None and sfa.text) else None

            if not identifier:
                continue

            if tag == "020":
                idType = "isbn"
                sfqElems = idElem.findall('marc:subfield[@code="q"]', namespaces=nsMap)
                additionalInfos = [sfqElem.text for sfqElem in sfqElems if sfqElem.text]  
            elif tag == "022":
                idType = "issn"
            elif tag == "024":
                idType = "other"
                sfq2Elems = idElem.xpath('marc:subfield[@code="q" or @code="2"]', namespaces=nsMap)
                additionalInfos = [sfq2Elem.text for sfq2Elem in sfq2Elems if sfq2Elem.text]  
            elif tag == "035":
                idType = "systemId"
                if ")" in identifier:
                    prefixPart, mainPart = identifier.split(")", 1)
                    prefix = prefixPart + ")"
                    identifier = mainPart.strip()

        elif idElem.tag.endswith("controlfield"):
            identifier = idElem.text.strip() if idElem.text else None
            
            if not identifier:
                continue

            if tag == "001":
                idType = "almaBib"
            elif tag == "009":
                idType = "primaryBib"

        if identifier and idType:
            fieldDataList.append({
                "value": identifier,
                "idType": idType,
                "prefix": prefix,
                "additionalInfos": additionalInfos
            })

    return fieldDataList

def extractHoldingInfos(marcRecord: etree._Element) -> list[dict]:
    holdingsList = []

    # parse AVA fields
    for dfAVA in marcRecord.findall('marc:datafield[@tag="AVA"]', namespaces=nsMap):
        
        # helper to extract text cleanly inline
        def getAvaSubfieldText(code: str) -> str | None:
            elem = dfAVA.find(f'marc:subfield[@code="{code}"]', namespaces=nsMap)
            return elem.text.strip() if (elem is not None and elem.text) else None

        # extract fields
        libCode = getAvaSubfieldText("b")
        libLabel = getAvaSubfieldText("q")
        callNum = getAvaSubfieldText("d")
        avail = getAvaSubfieldText("e")
        numItemsStr = getAvaSubfieldText("f")
        locCode = getAvaSubfieldText("j")
        locLabel = getAvaSubfieldText("c")

        # safely convert numOfItems to int
        numItems = int(numItemsStr) if (numItemsStr and numItemsStr.isdigit()) else None

        # build dict mimicking nested Pydantic structure
        holdingDict = {
            "libraryCode": libCode,
            "libraryLabel": libLabel,
            "locationCode": locCode,
            "locationLabel": locLabel,
            "callNumber": callNum,
            "itemInfos": {
                "numOfItems": numItems,
                "availability": avail
            }
        }

        # guard: only append if at least some core holding identifier exists
        if libCode or callNum or locCode:
            holdingsList.append(holdingDict)

    return holdingsList


def extractBibMaterialType(marcRecord: etree._Element) -> str | None:

    ldrElem = marcRecord.find('marc:leader', namespaces=nsMap)
    ldrStr = ldrElem.text if (ldrElem is not None and ldrElem.text) else None

    return getBibMaterialType(ldrStr)


def extractBibResourceType(marcRecord: etree._Element) -> str | None:

    ldrElem = marcRecord.find('marc:leader', namespaces=nsMap)
    ldrStr = ldrElem.text if (ldrElem is not None and ldrElem.text) else None

    cf008Elem = marcRecord.find('marc:controlfield[@tag="008"]', namespaces=nsMap)
    cf008Str = cf008Elem.text if (cf008Elem is not None and cf008Elem.text) else None

    return getResourceType(ldrStr, cf008Str)


def extractAdditionalRecData(marcRecord: etree._Element) -> dict:
    """Extracts minimal identifier data (AC number, call numbers, ISBNs, ISSNs) for subsidiary records."""
    
    # AC Number (System Control Number from 009 or 035 $a with (AT-OBV) / AC prefix)
    acNumber = None
    
    # check 009 first (Control Number in OBV)
    df009 = marcRecord.find('marc:controlfield[@tag="009"]', namespaces=nsMap)
    if df009 is not None and df009.text:
        acNumber = df009.text.strip()
    
    # fallback to 035 $a if 009 isn't present
    if not acNumber:
        for df035 in marcRecord.findall('marc:datafield[@tag="035"]/marc:subfield[@code="a"]', namespaces=nsMap):
            if df035.text and "AC" in df035.text:
                txt = df035.text.strip()
                acNumber = txt.split(")")[-1] if ")" in txt else txt
                break

    # titleMain
    titleMain = extractSubfield(marcRecord, "245", "a")

    # call Numbers (AVA $d subfields or 084/090/050 $a)
    callNumbers = extractSubfieldsList(marcRecord, "AVA", "d")

    # ISBNs (020 $a)
    rawIsbns = extractSubfieldsList(marcRecord, "020", "a")
    # clean ISBNs (take only the raw digits/X part before any space or qualifier)
    isbns = [isbn.split()[0] for isbn in rawIsbns]

    # ISSNs (022 $a)
    rawIssns = extractSubfieldsList(marcRecord, "022", "a")
    issns = [issn.split()[0] for issn in rawIssns]

    return {
        "ac": acNumber or "UNKNOWN",
        "titleMain": titleMain,
        "callNumbers": list(dict.fromkeys(callNumbers)),
        "isbns": list(dict.fromkeys(isbns)),
        "issns": list(dict.fromkeys(issns))
    }