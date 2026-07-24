#####################################
# fetchInfoSRU                      #
#####################################
import re
import uuid

from requests import Session
from lxml import etree
from typing import Literal
from datetime import time


def _validateParseSpec(fieldSpec: str) -> dict:
    """
    Validates a MARC field specification string using Regex.
    Returns a dictionary of parsed components if valid, or raises a ValueError.
    """
    # Pattern breakdown:
    # ^(LDR|AVA|AVE|\d{3})          -> Matches exactly 'LDR' or a 3-digit tag (like 245 or 001)
    # (_([0-9#]{2}|noIndSpec))?     -> Optional: matches indicators like 10, ##, or noIndSpec
    # (_([a-z0-9\[\]]+))?           -> Optional: matches subfields like abc, efg, or [all]
    # (_(text|detailed|noDelim))?$  -> Optional: matches output options
    pattern = r"^(LDR|AVA|AVE|\d{3})(_([0-9#]{2}|noIndSpec))?(_([a-z0-9\[\]]+))?(_(text|detailed|noDelim))?$"
    
    match = re.match(pattern, fieldSpec.strip())
    
    if not match:
        raise ValueError(
            f"Invalid field specification format: '{fieldSpec}'. "
            f"Expected format: Tag_Indicators_Subfields_Option (e.g., '245_10_abc_noDelim')"
        )
        
    # if valid, extract components using groups, fallback to defaults if None
    return {
        "field": match.group(1),
        "indicators": match.group(3) if match.group(3) else "noIndSpec",
        "subfields": match.group(5) if match.group(5) else "[all]",
        "option": match.group(7) if match.group(7) else "detailed"
    }

def _getFieldSubfieldInfos(recordElem, fieldTag, indicators, subfieldCodes, returnCode, ns):
    """
    Extracts field data with formatting configurations.
    """
    # build indicator query element
    if indicators == "noIndSpec":
        indQuery = ""
    else:
        i1 = " " if indicators[0] == "#" else indicators[0]
        i2 = " " if indicators[1] == "#" else indicators[1]
        indQuery = f'[@ind1="{i1}"][@ind2="{i2}"]'

    tagQuery = f'marc:datafield[@tag="{fieldTag}"]{indQuery}'
    fieldElemList = recordElem.findall(tagQuery, namespaces=ns)
    
    if not fieldElemList:
        return None

    fieldStrings = []

    for fieldElem in fieldElemList:
        subfieldStrings = []
        
        # format indicators
        indStr = ""
        if returnCode in ["detailed", "noDelim"]:
            i1 = fieldElem.attrib.get("ind1", " ").replace(" ", "#")
            i2 = fieldElem.attrib.get("ind2", " ").replace(" ", "#")
            # for 'noDelim', don't append trailing pipes to indicator block
            indSeparator = "_" if returnCode == "noDelim" else "_ | "
            indStr = f"_Ind: {i1}{i2}{indSeparator}"

        # collect targeted subfields
        # literal strings like "all" will look for sf 'a', 'l', 'l'.
        if subfieldCodes == "[all]":
            subfields = fieldElem.findall(f'marc:subfield', namespaces=ns)
        else:
            subfields = []
            for code in subfieldCodes:
                subfields.extend(fieldElem.findall(f'marc:subfield[@code="{code}"]', namespaces=ns))

        # dynamic formatting loop
        for subelem in subfields:
            code = subelem.attrib.get('code', '')
            val = subelem.text if subelem.text is not None else ""
            
            if returnCode in ["detailed", "noDelim"]:
                sfPrefix = " $$" if returnCode == "noDelim" else "$$"
                subfieldStrings.append(f"{sfPrefix}{code} {val}")
            else:
                # retained structural tagging logic for special fields
                if fieldTag == "AVA":
                    label_map = {"d": "CN: ", "b": "Lib: ", "j": "Loc: ", "f": "Count: "}
                    subfieldStrings.append(f"{label_map.get(code, '')}{val}")
                elif fieldTag == "AVE":
                    label_map = {"8": "portfolioID: ", "c": "collectionID: ", "e": "status: ", "m": "name: ", "s": "coverage: "}
                    subfieldStrings.append(f"{label_map.get(code, '')}{val}")
                else:
                    subfieldStrings.append(val)

        # build output fields if data matches criteria
        if subfieldStrings:
            if returnCode == "noDelim":
                subfield_delimiter = ""
            else:
                subfield_delimiter = " " if fieldTag in ["AVA", "AVE"] else " | "
                
            fieldStrings.append(f"{indStr}{subfield_delimiter.join(subfieldStrings)}")
        elif indStr: 
            fieldStrings.append(indStr.rstrip(" | "))

    return " || ".join(fieldStrings) if fieldStrings else None


def fetchInfoSRU(searchstring: str, fieldSpecList: list[str], scope: Literal["iz", "nz"] | None, expectedRecordNum: None | int = None, baseUrl: None | str = None) -> dict:
    r"""
    Executes harvest of MarcXML records from an Ex Libris Alma SRU interface.

    Validates and processes a list of custom MARC field specifications, orchestrates paginated 
    `searchRetrieve` server requests, and extracts specified data elements record by record. 
    The function isolates individual record syntax corruptions and network-level dropouts, 
    guaranteeing that any parsed data collected up to the moment of a failure is preserved and 
    returned within a structured dictionary metadata wrapper.

    ### Args
    * **searchstring** (`str`): A valid CQL (Contextual Query Language) string used to filter the SRU dataset.
    * **fieldSpecList** (`list[str]`): A collection of parsing directives defining targeted tags, indicators, 
        and subfields (e.g., `['245_10_abc_noDelim', '001', 'AVA__d_text']`). Invalid entries are skipped inline.
    * **scope** (`Literal["iz", "nz"]` or `None`): The targeted Alma environment shortcut. Use `"iz"` for the 
        Institution Zone or `"nz"` for the Network Zone. Can be `None` if an explicit `baseUrl` is provided.
    * **expectedRecordNum** (`int` or `None`, *optional*): An expected total record count profile used for execution 
        sanity checks. Results are evaluated and logged inside the output payload metadata. Defaults to `None`.
    * **baseUrl** (`str` or `None`, *optional*): A custom SRU endpoint URL path. Overrides the default shortcut 
        dictionary if explicit alternative routing is needed. Defaults to `None`.

    ### Returns
    * **resultDict** (`dict`): A structured harvest payload collection containing the following metadata keys:
        - `"timestamp"` (*str*): The ISO-8601 formatted GMT generation timestamp.
        - `"url"` (*str*): The target endpoint URL used for active requests.
        - `"searchstring"` (*str*): The query string processed during the harvest run.
        - `"numberOfRecords"` (*int or None*): The total matching hit count declared by the remote server.
        - `"originalFieldSpecList"` (*list[str]*): The pristine list of input specifications provided by the caller.
        - `"processedFieldSpecList"` (*list[str]*): The validated and compiled dictionary keys extracted by the engine.
        - `"expectedRecordNum"` (*int or None*): The baseline target count passed into the execution query.
        - `"expectedRecordNumInfo"` (*str or None*): A generated audit phrase evaluating expected vs. found metrics.
        - `"recordInfos"` (*dict*): The core datastore mapping distinct record control keys (MMSIDs or generated UUID fallbacks) 
          to inner dictionaries containing the string-formatted results of parsed field specs.

    ### Examples
    ```python
    from requests import Session

    fieldTargets = ["001", "245_10_abc_detailed", "AVA_dbjf_text"]
    
    harvestResults = libtoolkit.fetchInfoSRU(
        searchstring='alma.title="Python Programming"',
        fieldSpecList=fieldTargets,
        scope="iz",
        expectedRecordNum=12
    )

    print(f"Successfully tracked down {harvestResults['numberOfRecords']} total records.")
    for mmsid, fields in harvestResults["recordInfos"].items():
        print(f"MMSID: {mmsid} -> Title Metadata: {fields.get('DF245_10_abc_detailed')}")
    ```
    """
    startRecord = 1
    callCounter = 1
    session = Session()

    if scope not in ["iz", "nz"] and baseUrl is None:
        raise ValueError('Invalid definition of scope. Please provide either a scope ("iz" | "nz") or an alternative baseUrl.')

    # parse, normalize, and validate fieldSpecs
    parsedSpecs = {}

    for spec in fieldSpecList:
        try:
            # parse and validate immediately
            parsed = _validateParseSpec(spec)

        except ValueError as e:
            print(f"Skipping invalid input. {e}")
            continue # skip this column and move on, or halt execution
            
        field = parsed["field"]
        inds = parsed["indicators"]
        subs = parsed["subfields"]
        ret = parsed["option"]

        # determine column family classification prefixes
        if field == "LDR":
            colName = "LDR"
        elif field.startswith("00"):
            colName = f"CF{field}"
        elif field in ["AVA", "AVE"]:
            # no prefix for special holding blocks
            colName = f"{field}_{inds}_{subs}_{ret}"
        else:
            # unified column names for data fields
            colName = f"DF{field}_{inds}_{subs}_{ret}"

        parsedSpecs[colName] = (field, inds, subs, ret)

    # iz and nz sru baseurls
    baseUrlDict = {
        "iz": "https://obv-at-oenb.alma.exlibrisgroup.com/view/sru/43ACC_ONB",
        "nz": "https://obv-at-obvsg.alma.exlibrisgroup.com/view/sru/43ACC_NETWORK"
    }

    # sru namespaces
    nsMap = {
        "srw": "http://www.loc.gov/zing/srw/",
        "marc": "http://www.loc.gov/MARC21/slim"
    }

    # this will be returned
    resultDict = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "url": baseUrl if baseUrl is not None else baseUrlDict[scope],
        "searchstring": searchstring,
        "numberOfRecords": None,
        "originalFieldSpecList": fieldSpecList,
        "processedFieldSpecList": list(parsedSpecs),
        "expectedRecordNum": expectedRecordNum,
        "expectedRecordNumInfo": None,
        "recordInfos": {}
    }

    # if another baseurl was provided
    if baseUrl is None:
        baseUrl = baseUrlDict[scope]

    # for request
    params = {
        "version": "1.2",
        "operation": "searchRetrieve",
        "maximumRecords": "50",
        "recordSchema": "marcxml",
        "startRecord": startRecord,
        "query": searchstring
    }


    try:
        while True:    
            print(f"SRU call {callCounter} for searchstring '{searchstring}'.")
            
            # isolate network drops or server timeouts
            try:
                res = session.get(baseUrl, params=params, timeout=30)
                res.raise_for_status()
                resRoot = etree.fromstring(res.content)

            except Exception as netEx:
                print(f"Aborting harvest: Network or server error on call {callCounter}: {netEx}")
                break       # exit loop cleanly to return whatever data captured up to this point

            if resultDict["numberOfRecords"] is None:
                numRecords = int(resRoot.find("srw:numberOfRecords", namespaces=nsMap).text or 0)
                resultDict["numberOfRecords"] = numRecords
                print(f"Found {numRecords} records.")
                
                if expectedRecordNum is not None:
                    matched = "Success." if numRecords == expectedRecordNum else "Failure."
                    resultDict["expectedRecordNumInfo"] = f"{numRecords} records found - expected record number {'matched' if numRecords == expectedRecordNum else 'not matched'}. {matched}"

            records = resRoot.findall(".//marc:record", namespaces=nsMap)
            if not records:
                break

            print(f"Processing records {params['startRecord']} to {params['startRecord'] + len(records) - 1}")

            for recordElem in records:

                # isolate individual record corruption
                try:
                    cf001 = recordElem.find('marc:controlfield[@tag="001"]', namespaces=nsMap)
                    
                    # keep UUID as string so the dict keys stay predictable strings
                    mmsid = cf001.text if (cf001 is not None and cf001.text) else f"MISSING_{uuid.uuid4()}"
                    
                    resultDict["recordInfos"][mmsid] = {}

                    # core execution engine Loop                
                    for field, valTuple in parsedSpecs.items():

                        if field == "LDR":
                            elem = recordElem.find(f"marc:leader", namespaces=nsMap)
                            resultDict["recordInfos"][mmsid]["LDR"] = elem.text if elem is not None else None
                            
                        elif field.startswith("CF00"): 
                            elems = recordElem.findall(f'marc:controlfield[@tag="{valTuple[0]}"]', namespaces=nsMap)
                            if not elems:
                                resultDict["recordInfos"][mmsid][field] = None
                            elif field == "007":
                                resultDict["recordInfos"][mmsid][field] = " ][ ".join([el.text for el in elems if el.text])
                            else:
                                resultDict["recordInfos"][mmsid][field] = elems[0].text if elems[0].text else None
                                
                        else: 
                            resultDict["recordInfos"][mmsid][field] = _getFieldSubfieldInfos(
                            recordElem, valTuple[0], valTuple[1], valTuple[2], valTuple[3], nsMap
                        )

                except Exception as recordEx:
                    
                    # if one single MARC record is corrupt, log it and keep going
                    print(f"Skipping corrupt record in batch (Start Record {params['startRecord']}): {recordEx}")
                    continue

            # advance pagination
            params["startRecord"] += len(records)
            if params["startRecord"] > resultDict["numberOfRecords"]:
                break
                
            callCounter += 1

    except Exception as e:
        print(f"CRITICAL CRASH: Pipeline failed unexpectedly: {e}")
        print("Returning partial data collected up to this point.")
    
    return resultDict