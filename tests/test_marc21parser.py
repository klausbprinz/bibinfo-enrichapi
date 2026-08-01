from pathlib import Path
import pytest
from lxml import etree

from enrichapi.utils import marc21parser as parse

# Define MARC21 XML namespace mapping for test setup
NS_MAP = {"marc": "http://www.loc.gov/MARC21/slim"}


@pytest.fixture
def rawXmlRoot() -> etree._Element:
    """Fixture that loads and parses the Kant sample SRU XML file into an lxml element tree."""
    samplePath = Path("data/test-data/marcxml-testrecord-oenbsru.xml")
    assert samplePath.exists(), f"Sample test XML missing at: {samplePath.resolve()}"
    
    tree = etree.parse(str(samplePath))
    return tree.getroot()


@pytest.fixture
def marcRecord(rawXmlRoot: etree._Element) -> etree._Element:
    """Fixture that extracts the first MARC21 <record> element from the sample XML."""
    # find the first record element using MARC namespace or local name fallback
    record = rawXmlRoot.find(".//marc:record", namespaces=NS_MAP)
    if record is None:
        # fallback in case namespace prefix isn't bound on <record> in the root
        record = rawXmlRoot.find(".//{http://www.loc.gov/MARC21/slim}record")
    
    assert record is not None, "Could not find a <record> element in the sample test XML file."
    return record


# individual parser unit tests
def testExtractTitleData(marcRecord: etree._Element):
    """Verify title data extraction (245 $a, $b, $n, $p)."""
    titleMain, titleRem, partNums, partNames = parse.extractTitleData(marcRecord)
    
    assert titleMain is not None, "Main title should not be None"
    assert isinstance(titleMain, str)
    assert len(titleMain) > 0
    assert isinstance(partNums, list)
    assert isinstance(partNames, list)


def testExtractLanguageCodes(marcRecord: etree._Element):
    """Verify language code extraction (041 $a)."""
    langCodes = parse.extractLanguageCodes(marcRecord)
    assert isinstance(langCodes, list)


def testExtractPublicationNotices(marcRecord: etree._Element):
    """Verify 264 field extraction for publisher and dating info."""
    notices = parse.extractPublicationNotices(marcRecord)
    assert isinstance(notices, list)
    
    if len(notices) > 0:
        firstNotice = notices[0]
        assert "pnType" in firstNotice
        assert "places" in firstNotice
        assert "names" in firstNotice
        assert "dates" in firstNotice


def testExtractIdentifier(marcRecord: etree._Element):
    """Verify extraction of IDs (ISBN, Alma, Control Numbers, etc.)."""
    identifiers = parse.extractIdentifier(marcRecord)
    assert isinstance(identifiers, list)
    assert len(identifiers) > 0, "Record should contain at least one identifier (e.g., 001/020/035)"
    
    # ensure each identifier dict contains required schema keys
    firstId = identifiers[0]
    assert "value" in firstId
    assert "idType" in firstId


def testExtractSubjectHeadingsDeduplication(marcRecord: etree._Element):
    """Verify subject heading extraction and order-preserving deduplication (650 & 689)."""
    subjects = parse.extractSubjectHeadings(marcRecord)
    assert isinstance(subjects, list)
    # check that duplicates were eliminated
    assert len(subjects) == len(set(subjects))



# edge case / error handling tests
def testExtractSubfieldReturnsNoneOnMissingTag(marcRecord: etree._Element):
    """Ensure extractSubfield returns None gracefully when tag is missing or non-existent."""
    assert parse.extractSubfield(marcRecord, None, "a") is None
    assert parse.extractSubfield(marcRecord, "99999", "a") is None


def testExtractEntryDataReturnsNoneWhenSubfieldaMissing():
    """Ensure extractEntryData returns None if there is no subfield $a name."""
    xmlSnippet = etree.fromstring(
        '<marc:datafield xmlns:marc="http://www.loc.gov/MARC21/slim" tag="100" ind1="1" ind2=" "/>'
    )
    result = parse.extractEntryData(xmlSnippet)
    assert result is None