from typing import Literal

def getMarc21MaterialType(
    ldr: str | None, 
    lang: Literal["en", "de", "both"] = "en"
) -> str | tuple[str, str]:
    r"""
    Evaluates MARC21 Leader (LDR) positions 06 and 07 to determine broad material type.

    Executes an ordered suite of metadata rules against character slices in MARC21 leader 
    positions 06 (Type of record) and 07 (Bibliographic level) to map the record to a 
    broad format category (e.g., Book, Journal, Music, Map).

    ### Args
    * **ldr** (`str` or `None`): The 24-character MARC21 Leader string (e.g., `"01234nam a2200301 a 4500"`).
    * **lang** (`Literal["en", "de", "both"]`, *optional*): Specifies the language of the returned label.
        - `"en"`: Returns English string label.
        - `"de"`: Returns German string label.
        - `"both"`: Returns a tuple `(englishLabel, germanLabel)`.
        Defaults to `"en"`.

    ### Returns
    * **materialType** (`str` or `tuple[str, str]`): The resolved human-readable material type label 
        in the requested language format, or `"Book [default]"` / `"Buch [default]"` if no rules match. 
        Returns `"Undefined"` / `"Nicht definiert"` for invalid or missing inputs.

    ### Examples
    ```python
    # basic usage - english default
    res = libtoolkit.getMarc21MaterialType("00000cam a22000004a 4500")
    print(res)
    # output: 'Book (BK)'

    # bilingual tuple output
    resTuple = libtoolkit.getMarc21MaterialType("00000cas a22000004a 4500", lang="both")
    print(resTuple)
    # output: ('Journal (CR)', 'Zeitschrift')
    ```
    """

    # guard against invalid or missing input
    if not isinstance(ldr, str) or len(ldr) < 8:
        if lang == "both":
            return ("Undefined", "Nicht definiert")
        return "Nicht definiert" if lang == "de" else "Undefined"

    # extract relevant ldr positions
    l6 = ldr[6]
    l7 = ldr[7]

    # define evaluation rules as a list of tuples: (condition_fn, english_label, german_label)
    RULES = [
        (lambda: l6 == "t", "Book (BK)", "Buch"),
        (lambda: l6 == "m", "Computer File (CF)", "Computerdatei"),
        (lambda: l6 == "p", "Mixed Material (MX)", "Gemischtes Material"),
        (lambda: l6 in {"c", "d", "i", "j"}, "Music (MU)", "Musik"),
        (lambda: l6 in {"e", "f"}, "Map (MP)", "Karte"),
        (lambda: l6 in {"g", "k", "r", "o"}, "Visual Material (VM)", "Bildmaterial"),
        (lambda: l6 == "a" and l7 in {"a", "c", "d", "m"}, "Book (BK)", "Buch"),
        (lambda: l6 == "a" and l7 in {"b", "i", "s"}, "Journal (CR)", "Zeitschrift")
    ]

    # evaluate rules sequentially; return matching label(s) on first True match
    for condition, engLabel, gerLabel in RULES:
        if condition():
            if lang == "both":
                return (engLabel, gerLabel)
            return gerLabel if lang == "de" else engLabel

    # default fallback
    if lang == "both":
        return ("Book [default]", "Buch [default]")
    return "Buch [default]" if lang == "de" else "Book [default]"


def getMarc21ResourceType(
    ldr: str | None,
    cf008: str | None,
    lang: Literal["en", "de", "both"] = "en"
) -> str | tuple[str, str]:
    r"""
    Evaluates MARC21 Leader (LDR) and Control Field 008 (cf008) strings to classify resource types.

    Executes an ordered suite of metadata rules against character slices in MARC21 leader 
    positions 06 (Type of record) and 07 (Bibliographic level), combined with position-specific 
    field 008 descriptors (Form of item, Format of music, Type of serial, etc.). 

    ### Args
    * **ldr** (`str` or `None`): The 24-character MARC21 Leader string (e.g., `"01234nam a2200301 a 4500"`).
    * **cf008** (`str` or `None`): The 40-character MARC21 Control Field 008 fixed-length data element string.
    * **lang** (`Literal["en", "de", "both"]`, *optional*): Specifies the language of the returned label.
        - `"en"`: Returns English string label.
        - `"de"`: Returns German string label.
        - `"both"`: Returns a tuple `(englishLabel, germanLabel)`.
        Defaults to `"en"`.

    ### Returns
    * **resourceType** (`str` or `tuple[str, str]`): The resolved human-readable resource type label 
        in the requested language format, or `"Undefined"` / `"Nicht definiert"` if no rules match.

    ### Examples
    ```python
    # basic usage - english default
    res = libtoolkit.getMarc21ResourceType("00000cam a22000004a 4500", "000000s2023    xx a   o     000 0 eng d")
    print(res)
    # output: 'Book - Electronic'

    # bilingual tuple output
    resTuple = libtoolkit.getMarc21ResourceType("00000cam a22000004a 4500", "000000s2023    xx a   o     000 0 eng d", lang="both")
    print(resTuple)
    # output: ('Book - Physical', 'Buch - Physisch')
    ```
    """
    # guard against invalid or missing input
    if not isinstance(ldr, str) or len(ldr) < 8:
        if lang == "both":
            return ("Undefined", "Nicht definiert")
        return "Nicht definiert" if lang == "de" else "Undefined"

    # extract common variables to simplify rule evaluation
    l6, l7 = ldr[6], ldr[7]
    c6  = cf008[6]  if isinstance(cf008, str) and len(cf008) > 6  else ""
    c21 = cf008[21] if isinstance(cf008, str) and len(cf008) > 21 else ""
    c23 = cf008[23] if isinstance(cf008, str) and len(cf008) > 23 else ""
    c25 = cf008[25] if isinstance(cf008, str) and len(cf008) > 25 else ""
    c29 = cf008[29] if isinstance(cf008, str) and len(cf008) > 29 else ""
    c33 = cf008[33] if isinstance(cf008, str) and len(cf008) > 33 else ""

    # common indicator sets
    ELECTRONIC_CODES = {"o", "q", "s"}
    FORM_EXCLUSIONS = {"a", "b", "c", "o", "f", "q", "s"}

    # format: (conditionFunction, englishLabel, germanLabel)
    RULES = [
        # =========================================================================
        # 1. SPECIAL COLLECTIONS & GENERIC LDR OVERRIDES
        # =========================================================================
        (lambda: l6 == "m", "Other material - Electronic", "Anderes Material - Elektronisch"),
        (lambda: l6 == "p" and l7 == "c", "Mixed Materials", "Gemischte Materialien"),
        (lambda: l6 != "p" and l7 == "c", "Collection", "Sammlung"),

        # =========================================================================
        # 2. BOOKS & MONOGRAPHS
        # =========================================================================
        (lambda: l6 == "a" and l7 == "m" and c23 == "f", "Braille Book - Physical", "Blindenschrift-Buch - Physisch"),
        (lambda: l6 == "a" and l7 == "m" and c23 in ELECTRONIC_CODES, "Book - Electronic", "Buch - Elektronisch"),
        (lambda: l6 == "a" and l7 == "m" and c23 not in FORM_EXCLUSIONS, "Book - Physical", "Buch - Physisch"),

        # =========================================================================
        # 3. MAPS & ATLASES
        # =========================================================================
        (lambda: l6 == "e" and l7 == "a", "Map - Component Part", "Karte - Komponententeil"),
        (lambda: l6 == "e" and l7 == "m" and c29 == "f", "Braille Map - Physical", "Blindenschrift-Karte - Physisch"),
        # Atlases (c25 == "e")
        (lambda: l6 == "e" and l7 == "m" and c25 == "e" and c29 in ELECTRONIC_CODES, "Atlas - Electronic", "Atlas - Elektronisch"),
        (lambda: l6 == "e" and l7 in {"m", "s"} and c25 == "e" and c29 == "a", "Atlas - Microfilm", "Atlas - Mikrofilm"),
        (lambda: l6 == "e" and l7 in {"m", "s"} and c25 == "e" and c29 == "b", "Atlas - Microfiche", "Atlas - Microfiche"),
        (lambda: l6 == "e" and l7 in {"m", "s"} and c25 == "e" and c29 == "c", "Atlas - Microopaque", "Atlas - Mikro-Opak"),
        (lambda: l6 == "e" and l7 == "m" and c25 == "e" and c29 not in FORM_EXCLUSIONS, "Atlas - Physical", "Atlas - Physisch"),
        # Maps (c25 != "e")
        (lambda: l6 == "e" and l7 == "m" and c25 != "e" and c29 in ELECTRONIC_CODES, "Map - Electronic", "Karte - Elektronisch"),
        (lambda: l6 == "e" and l7 in {"m", "s"} and c25 != "e" and c29 == "a", "Map - Microfilm", "Karte - Mikrofilm"),
        (lambda: l6 == "e" and l7 in {"m", "s"} and c25 != "e" and c29 == "b", "Map - Microfiche", "Karte - Mikrofiche"),
        (lambda: l6 == "e" and l7 in {"m", "s"} and c25 != "e" and c29 == "c", "Map - Microopaque", "Karte - Mikro-Opak"),
        (lambda: l6 == "e" and l7 in {"m", "s"} and c25 != "e" and c29 not in FORM_EXCLUSIONS, "Map - Physical", "Karte - Physisch"),

        # =========================================================================
        # 4. SERIALS (NEWSPAPERS, JOURNALS, PERIODICALS)
        # =========================================================================
        (lambda: l6 == "a" and l7 in {"i", "s"} and c23 == "f", "Braille Serial - Physical", "Blindenschrift-Zeitschrift - Physisch"),
        # Newspapers (c21 == "n")
        (lambda: l6 == "a" and l7 in {"i", "s"} and c21 == "n" and c6 != "d" and c23 in ELECTRONIC_CODES, "Newspaper - Electronic", "Zeitung - Elektronisch"),
        (lambda: l6 == "a" and l7 in {"i", "s"} and c21 == "n" and c6 == "d" and c23 in ELECTRONIC_CODES, "Newspaper (Ceased publication) - Electronic", "Zeitung (eingestellte Veröffentlichung) - Elektronisch"),
        (lambda: l6 == "a" and l7 in {"i", "s"} and c21 == "n" and c6 != "d" and c23 not in FORM_EXCLUSIONS, "Newspaper - Physical", "Zeitung - Physisch"),
        (lambda: l6 == "a" and l7 in {"i", "s"} and c21 == "n" and c6 == "d" and c23 not in FORM_EXCLUSIONS, "Newspaper (Ceased publication) - Physical", "Zeitung (eingestellte Veröffentlichung) - Physisch"),
        # Journals (c21 == "p")
        (lambda: l6 == "a" and l7 in {"i", "s"} and c21 == "p" and c6 != "d" and c23 in ELECTRONIC_CODES, "Journal - Electronic", "Zeitschrift - Elektronisch"),
        (lambda: l6 == "a" and l7 in {"i", "s"} and c21 == "p" and c6 == "d" and c23 in ELECTRONIC_CODES, "Journal (Ceased publication) - Electronic", "Zeitschrift (eingestellte Veröffentlichung) - Elektronisch"),
        (lambda: l6 == "a" and l7 in {"i", "s"} and c21 == "p" and c6 != "d" and c23 not in FORM_EXCLUSIONS, "Journal - Physical", "Zeitschrift - Physisch"),
        (lambda: l6 == "a" and l7 in {"i", "s"} and c21 == "p" and c6 == "d" and c23 not in FORM_EXCLUSIONS, "Journal (Ceased publication) - Physical", "Zeitschrift (eingestellte Veröffentlichung) - Physisch"),
        # Other Serials
        (lambda: l6 == "a" and l7 in {"i", "s"} and c21 not in {"n", "p"} and c6 != "d" and c23 in ELECTRONIC_CODES, "Other Serial - Electronic", "Andere Zeitschrift - Elektronisch"),
        (lambda: l6 == "a" and l7 in {"i", "s"} and c21 not in {"n", "p"} and c6 == "d" and c23 in ELECTRONIC_CODES, "Other Serial (Ceased publication) - Electronic", "Andere Zeitschrift (eingestellte Veröffentlichung) - Elektronisch"),
        (lambda: l6 == "a" and l7 in {"i", "s"} and c21 not in {"n", "p"} and c6 != "d" and c23 not in FORM_EXCLUSIONS, "Other Serial - Physical", "Andere Zeitschrift - Physisch"),
        (lambda: l6 == "a" and l7 in {"i", "s"} and c21 not in {"n", "p"} and c6 == "d" and c23 not in FORM_EXCLUSIONS, "Other Serial (Ceased publication) - Physical", "Andere Zeitschrift (eingestellte Veröffentlichung) - Physisch"),

        # =========================================================================
        # 5. COMPONENT PARTS (ARTICLES, SECTIONS, ANALYTICS)
        # =========================================================================
        (lambda: l6 == "a" and l7 == "a" and c23 in ELECTRONIC_CODES, "Monographic component part - Electronic", "Monografischer Komponententeil - Elektronisch"),
        (lambda: l6 == "a" and l7 == "a" and c23 not in FORM_EXCLUSIONS, "Monographic component part - Physical", "Monografischer Komponententeil - Physisch"),
        (lambda: l6 == "a" and l7 == "b" and c23 in {"o", "f", "q", "s"}, "Serial component part - Electronic", "Fortlaufender Komponententeil - Elektronisch"),
        (lambda: l6 == "a" and l7 == "b" and c23 not in FORM_EXCLUSIONS, "Serial component part - Physical", "Fortlaufender Komponententeil - Physisch"),

        # =========================================================================
        # 6. MANUSCRIPTS
        # =========================================================================
        (lambda: l6 == "f" and l7 == "a", "Manuscript - Component Part", "Manuskript - Komponententeil"),
        (lambda: l6 in {"d", "t"} and l7 == "m" and c23 in ELECTRONIC_CODES, "Manuscripts - Electronic", "Manuskripte - Elektronisch"),
        (lambda: l6 == "f" and l7 == "m" and c29 in ELECTRONIC_CODES, "Manuscripts - Electronic", "Manuskripte - Elektronisch"),
        (lambda: l6 in {"d", "t"} and l7 == "m" and c23 not in FORM_EXCLUSIONS, "Manuscripts - Physical", "Manuskripte - Physisch"),
        (lambda: l6 == "f" and l7 == "m" and c29 not in FORM_EXCLUSIONS, "Manuscripts - Physical", "Manuskripte - Physisch"),

        # =========================================================================
        # 7. MUSIC & NOTATION
        # =========================================================================
        (lambda: l6 in {"c", "d", "j"} and l7 == "a", "Music - Component Part", "Musik - Komponententeil"),
        (lambda: l6 == "c" and l7 == "m" and c23 == "f", "Braille Music - Physical", "Blindenschrift-Noten - Physisch"),
        (lambda: l6 == "c" and l7 == "m" and c23 in ELECTRONIC_CODES, "Notated music - Electronic", "Notierte Musik - Elektronisch"),
        (lambda: l6 == "c" and l7 == "m" and c23 not in FORM_EXCLUSIONS, "Notated music - Physical", "Notierte Musik - Physisch"),

        # =========================================================================
        # 8. AUDIO RECORDINGS
        # =========================================================================
        (lambda: l6 == "i" and l7 == "a", "Audio nonmusical - Component Part", "Audio - Nicht-Musik - Komponententeil"),
        # Musical Audio (l6 == "j")
        (lambda: l6 == "j" and l7 == "m" and c23 in ELECTRONIC_CODES, "Audio musical - Electronic", "Audiomusik - Elektronisch"),
        (lambda: l6 == "j" and l7 == "m" and c23 not in FORM_EXCLUSIONS, "Audio musical - Physical", "Audiomusik - Physisch"),
        # Non-Musical Audio (l6 == "i")
        (lambda: l6 == "i" and l7 == "m" and c23 in ELECTRONIC_CODES, "Audio nonmusical - Electronic", "Audio - Nichtmusik - Elektronisch"),
        (lambda: l6 == "i" and l7 == "m" and c23 not in FORM_EXCLUSIONS, "Audio nonmusical - Physical", "Audio - Nichtmusik - Physisch"),

        # =========================================================================
        # 9. VISUAL MEDIA, GRAPHICS & KITS
        # =========================================================================
        (lambda: l6 == "g" and l7 == "a", "Projected media - Component Part", "Projizierte Medien - Komponententeil"),
        (lambda: l6 == "k" and l7 == "a", "2D non-projectable graphic - Component Part", "Nicht projizierbare 2D-Grafik - Komponententeil"),
        (lambda: l6 == "o" and l7 == "a", "Kit - Component Part", "Satz - Komponententeil"),
        # Projected Media
        (lambda: l6 == "g" and l7 == "m" and c33 in {"d", "f", "i", "m", "p", "s", "t", "v"} and c29 in ELECTRONIC_CODES, "Projected medium - Electronic", "Projiziertes Medium - Elektronisch"),
        (lambda: l6 == "g" and l7 == "m" and c33 in {"d", "f", "i", "m", "p", "s", "t", "v"} and c29 not in FORM_EXCLUSIONS, "Projected medium - Physical", "Projiziertes Medium - Physisch"),
        # 2D Graphics
        (lambda: l6 == "k" and l7 == "m" and c33 in {"a", "c", "i", "k", "l", "n", "o"} and c29 in ELECTRONIC_CODES, "2D non-projectable graphic - Electronic", "2D nicht-projizierbare Grafik - Elektronisch"),
        (lambda: l6 == "k" and l7 == "m" and c33 in {"a", "c", "i", "k", "l", "n", "o"} and c29 not in FORM_EXCLUSIONS, "2D non-projectable graphic - Physical", "2D nicht-projizierbare Grafik - Physisch"),
        # Kits & 3D Artifacts
        (lambda: l6 == "o" and c33 == "b" and c29 not in FORM_EXCLUSIONS, "Kit - Physical", "Satz - Physisch"),
        (lambda: l6 == "r" and c33 in {"r", "w"} and c29 not in ELECTRONIC_CODES, "3D artifact - Physical", "3D-Artefakt - Physisch"),

        # =========================================================================
        # 10. MICROFORMS FALLBACK
        # =========================================================================
        (lambda: l6 != "e" and c23 in {"a", "b", "c"}, "Microforms", "Mikroformen"),
    ]

    # iterate through rules in order of precedence
    for conditionFn, engLabel, gerLabel in RULES:
        try:
            if conditionFn():
                if lang == "both":
                    return (engLabel, gerLabel)
                return gerLabel if lang == "de" else engLabel
        except IndexError:
            continue

    # default fallback
    if lang == "both":
        return ("Undefined", "Nicht definiert")
    return "Nicht definiert" if lang == "de" else "Undefined"