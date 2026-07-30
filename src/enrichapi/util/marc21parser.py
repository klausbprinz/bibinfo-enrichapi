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
    return [e.text for e in elems if e.text]


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




