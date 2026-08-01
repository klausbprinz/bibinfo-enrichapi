def getBibMaterialType(ldrStr):

    mt_eng = "Book [default]"
    mt_ger = "Buch [default]"

    if ldrStr is not None:

        if ldrStr[6] == "a" and ldrStr[7] in ["a", "c", "d", "m"]:
            mt_eng = "Book (BK)"
            mt_ger = "Buch"

        elif ldrStr[6] == "t":
            mt_eng = "Book (BK)"
            mt_ger = "Buch"

        elif ldrStr[6] == "a" and ldrStr[7] in ["b", "i", "s"]:
            mt_eng = "Journal (CR)"
            mt_ger = "Zeitschrift"

        elif ldrStr[6] in ["c", "d", "i", "j"]:
            mt_eng = "Music (MU)"
            mt_ger = "Musik"

        elif ldrStr[6] in ["e", "f"]:
            mt_eng = "Map (MP)"
            mt_ger = "Karte"

        elif ldrStr[6] in ["g", "k", "r", "o"]:
            mt_eng = "Visual Material (VM)"
            mt_ger = "Bildmaterial"

        elif ldrStr[6] == "m":
            mt_eng = "Computer File (CF)"
            mt_ger = "Computerdatei"

        elif ldrStr[6] == "p":
            mt_eng = "Mixed Material (MX)"
            mt_ger = "Gemischtes Material"

    return mt_eng#, mt_ger


def getResourceType(ldr, cf008):

    resType_eng = "Undefined"
    resType_ger = "Nicht definiert"

    try:

        if ldr is not None:

            if ldr[6] == "m":
                resType_eng = "Other material - Electronic"
                resType_ger = "Anderes Material - Elektronisch"

            elif ldr[6] == "p" and ldr[7] == "c":
                resType_eng = "Mixed Materials"
                resType_ger = "Gemischte Materialien"

            elif ldr[6] != "p" and ldr[7] == "c":
                resType_eng = "Collection"
                resType_ger = "Sammlung"

            elif ldr[6] in ["c", "d", "j"] and ldr[7] == "a":
                resType_eng = "Music - Component Part"
                resType_ger = "Musik - Komponententeil"

            elif ldr[6] == "e" and ldr[7] == "a":
                resType_eng = "Map - Component Part"
                resType_ger = "Karte - Komponententeil"

            elif ldr[6] == "f" and ldr[7] == "a":
                resType_eng = "Manuscript - Component Part"
                resType_ger = "Manuskript - Komponententeil"

            elif ldr[6] == "g" and ldr[7] == "a":
                resType_eng = "Projected media - Component Part"
                resType_ger = "Projizierte Medien - Komponententeil"

            elif ldr[6] == "i" and ldr[7] == "a":
                resType_eng = "Audio nonmusical - Component Part"
                resType_ger = "Audio - Nicht-Musik - Komponententeil"

            elif ldr[6] == "k" and ldr[7] == "a":
                resType_eng = "2D non-projectable graphic - Component Part"
                resType_ger = "Nicht projizierbare 2D-Grafik - Komponententeil"

            elif ldr[6] == "o" and ldr[7] == "a":
                resType_eng = "Kit - Component Part"
                resType_ger = "Satz - Komponententeil"

        if ldr is not None and cf008 is not None:

            if ldr[6] == "a" and ldr[7] == "m" and cf008[23] not in ["a", "b", "c", "o", "f", "q", "s"]:
                resType_eng = "Book - Physical"
                resType_ger = "Buch - Physisch"

            elif ldr[6] == "a" and ldr[7] == "m" and cf008[23] in ["o", "q", "s"]:
                resType_eng = "Book - Electronic"
                resType_ger = "Buch - Elektronisch"

            elif ldr[6] == "e" and ldr[7] in ["m", "s"] and cf008[29] == "a" and cf008[25] != "e":
                resType_eng = "Map - Microfilm"
                resType_ger = "Karte - Mikrofilm"

            elif ldr[6] == "e" and ldr[7] in ["m", "s"] and cf008[29] == "b" and cf008[25] != "e":
                resType_eng = "Map - Microfiche"
                resType_ger = "Karte - Mikrofiche"

            elif ldr[6] == "e" and ldr[7] in ["m", "s"] and cf008[29] not in ["a", "b", "c", "o", "f", "q", "s"] and cf008[25] != "e":
                resType_eng = "Map - Physical"
                resType_ger = "Karte - Physisch"

            elif ldr[6] == "e" and ldr[7] in ["m", "s"] and cf008[29] == "c" and cf008[25] != "e":
                resType_eng = "Map - Microopaque"
                resType_ger = "Karte - Mikro-Opak"

            elif ldr[6] != "e" and cf008[23] in ["a", "b", "c"]:
                resType_eng = "Microforms"
                resType_ger = "Mikroformen"

            elif ldr[6] == "a" and ldr[7] == "m" and cf008[23] == "f":
                resType_eng = "Braille Book - Physical"
                resType_ger = "Blindenschrift-Buch - Physisch"

            elif ldr[6] == "a" and ldr[7] == "m" and cf008[23] == "f":
                resType_eng = "Braille Book - Physical"
                resType_ger = "Blindenschrift-Buch - Physisch"

            elif ldr[6] == "a" and ldr[7] in ["i", "s"] and cf008[23] == "f":
                resType_eng = "Braille Serial - Physical"
                resType_ger = "Blindenschrift-Zeitschrift - Physisch"

            elif ldr[6] == "e" and ldr[7] == "m" and cf008[29] == "f":
                resType_eng = "Braille Map - Physical"
                resType_ger = "Blindenschrift-Karte - Physisch"

            elif ldr[6] == "c" and ldr[7] == "m" and cf008[23] == "f":
                resType_eng = "Braille Music - Physical"
                resType_ger = "Blindenschrift-Noten - Physisch"

            elif ldr[6] == "e" and ldr[7] == "m" and cf008[29] not in ["a", "b", "c", "o", "f", "q", "s"] and cf008[25] == "e":
                resType_eng = "Atlas - Physical"
                resType_ger = "Atlas - Physisch"

            elif ldr[6] == "e" and ldr[7] == "m" and cf008[29] in ["o", "s", "q"] and cf008[25] == "e":
                resType_eng = "Atlas - Electronic"
                resType_ger = "Atlas - Elektronisch"

            elif ldr[6] == "e" and ldr[7] in ["m", "s"] and cf008[29] == "a" and cf008[25] == "e":
                resType_eng = "Atlas - Microfilm"
                resType_ger = "Atlas - Mikrofilm"

            elif ldr[6] == "e" and ldr[7] in ["m", "s"] and cf008[29] == "b" and cf008[25] == "e":
                resType_eng = "Atlas - Microfiche"
                resType_ger = "Atlas - Microfiche"

            elif ldr[6] == "e" and ldr[7] in ["m", "s"] and cf008[29] == "c" and cf008[25] == "e":
                resType_eng = "Atlas - Microopaque"
                resType_ger = "Atlas - Mikro-Opak"

            elif ldr[6] == "e" and ldr[7] == "m" and cf008[29] in ["o", "s", "q"] and cf008[25] != "e":
                resType_eng = "Map - Electronic"
                resType_ger = "Karte - Elektronisch"

            elif ldr[6] == "a" and ldr[7] in ["i", "s"] and cf008[6] != "d" and cf008[21] == "n" and cf008[23] not in ["a", "b", "c", "o", "f", "q", "s"]:
                resType_eng = "Newspaper - Physical"
                resType_ger = "Zeitung - Physisch"

            elif ldr[6] == "a" and ldr[7] in ["i", "s"] and cf008[6] == "d" and cf008[21] == "n" and cf008[23] not in ["a", "b", "c", "o", "f", "q", "s"]:
                resType_eng = "Newspaper (Ceased publication) - Physical"
                resType_ger = "Zeitung (eingestellte Veröffentlichung) - Physisch"

            elif ldr[6] == "a" and ldr[7] in ["i", "s"] and cf008[6] != "d" and cf008[21] == "n" and cf008[23] in ["o", "q", "s"]:
                resType_eng = "Newspaper - Electronic"
                resType_ger = "Zeitung - Elektronisch"

            elif ldr[6] == "a" and ldr[7] in ["i", "s"] and cf008[6] == "d" and cf008[21] == "n" and cf008[23] in ["o", "q", "s"]:
                resType_eng = "Newspaper (Ceased publication) - Electronic"
                resType_ger = "Zeitung (eingestellte Veröffentlichung) - Elektronisch"

            elif ldr[6] == "a" and ldr[7] in ["i", "s"] and cf008[6] != "d" and cf008[21] == "p" and cf008[23] not in ["a", "b", "c", "o", "f", "q", "s"]:
                resType_eng = "Journal - Physical"
                resType_ger = "Zeitschrift - Physisch"

            elif ldr[6] == "a" and ldr[7] in ["i", "s"] and cf008[6] == "d" and cf008[21] == "p" and cf008[23] not in ["a", "b", "c", "o", "f", "q", "s"]:
                resType_eng = "Journal (Ceased publication) - Physical"
                resType_ger = "Zeitschrift (eingestellte Veröffentlichung) - Physisch"

            elif ldr[6] == "a" and ldr[7] in ["i", "s"] and cf008[6] != "d" and cf008[21] == "p" and cf008[23] in ["o", "q", "s"]:
                resType_eng = "Journal - Electronic"
                resType_ger = "Zeitschrift - Elektronisch"

            elif ldr[6] == "a" and ldr[7] in ["i", "s"] and cf008[6] == "d" and cf008[21] == "p" and cf008[23] in ["o", "q", "s"]:
                resType_eng = "Journal (Ceased publication) - Electronic"
                resType_ger = "Zeitschrift (eingestellte Veröffentlichung) - Elektronisch"

            elif ldr[6] == "a" and ldr[7] in ["i", "s"] and cf008[6] != "d" and cf008[21] not in ["n", "p"] and cf008[23] not in ["a", "b", "c", "o", "f", "q", "s"]:
                resType_eng = "Other Serial - Physical"
                resType_ger = "Andere Zeitschrift - Physisch"

            elif ldr[6] == "a" and ldr[7] in ["i", "s"] and cf008[6] == "d" and cf008[21] not in ["n", "p"] and cf008[23] not in ["a", "b", "c", "o", "f", "q", "s"]:
                resType_eng = "Other Serial (Ceased publication) - Physical"
                resType_ger = "Andere Zeitschrift (eingestellte Veröffentlichung) - Physisch"

            elif ldr[6] == "a" and ldr[7] in ["i", "s"] and cf008[6] != "d" and cf008[21] not in ["n", "p"] and cf008[23] in ["o", "q", "s"]:
                resType_eng = "Other Serial - Electronic"
                resType_ger = "Andere Zeitschrift - Elektronisch"

            elif ldr[6] == "a" and ldr[7] in ["i", "s"] and cf008[6] == "d" and cf008[21] not in ["n", "p"] and cf008[23] in ["o", "q", "s"]:
                resType_eng = "Other Serial (Ceased publication) - Electronic"
                resType_ger = "Andere Zeitschrift (eingestellte Veröffentlichung) - Elektronisch"

            elif ldr[6] == "a" and ldr[7] == "b" and cf008[23] not in ["a", "b", "c", "o", "f", "q", "s"]:
                resType_eng = "Serial component part - Physical"
                resType_ger = "Fortlaufender Komponententeil - Physisch"

            elif ldr[6] == "a" and ldr[7] == "b" and cf008[23] in ["o", "f", "q", "s"]:
                resType_eng = "Serial component part - Electronic"
                resType_ger = "Fortlaufender Komponententeil - Elektronisch"

            elif ldr[6] in ["d", "t"] and ldr[7] == "m" and cf008[23] not in ["a", "b", "c", "o", "f", "q", "s"]:
                resType_eng = "Manuscripts - Physical"
                resType_ger = "Manuskripte - Physisch"

            elif ldr[6] == "f" and ldr[7] == "m" and cf008[29] not in ["a", "b", "c", "o", "f", "q", "s"]:
                resType_eng = "Manuscripts - Physical"
                resType_ger = "Manuskripte - Physisch"

            elif ldr[6] in ["d", "t"] and ldr[7] == "m" and cf008[23] in ["o", "q", "s"]:
                resType_eng = "Manuscripts - Electronic"
                resType_ger = "Manuskripte - Elektronisch"

            elif ldr[6] == "f" and ldr[7] == "m" and cf008[29] in ["o", "q", "s"]:
                resType_eng = "Manuscripts - Electronic"
                resType_ger = "Manuskripte - Elektronisch"

            elif ldr[6] == "c" and ldr[7] == "m" and cf008[23] not in ["a", "b", "c", "o", "f", "q", "s"]:
                resType_eng = "Notated music - Physical"
                resType_ger = "Notierte Musik - Physisch"

            elif ldr[6] == "c" and ldr[7] == "m" and cf008[23] in ["o", "q", "s"]:
                resType_eng = "Notated music - Electronic"
                resType_ger = "Notierte Musik - Elektronisch"

            elif ldr[6] == "j" and ldr[7] == "m" and cf008[23] not in ["a", "b", "c", "o", "f", "q", "s"]:
                resType_eng = "Audio musical - Physical"
                resType_ger = "Audiomusik - Physisch"

            elif ldr[6] == "j" and ldr[7] == "m" and cf008[23] in ["o", "q", "s"]:
                resType_eng = "Audio musical - Electronic"
                resType_ger = "Audiomusik - Elektronisch"

            elif ldr[6] == "i" and ldr[7] == "m" and cf008[23] not in ["a", "b", "c", "o", "f", "q", "s"]:
                resType_eng = "Audio nonmusical - Physical"
                resType_ger = "Audio - Nichtmusik - Physisch"

            elif ldr[6] == "i" and ldr[7] == "m" and cf008[23] in ["o", "q", "s"]:
                resType_eng = "Audio nonmusical - Electronic"
                resType_ger = "Audio - Nichtmusik - Elektronisch"

            elif ldr[6] == "g" and ldr[7] == "m" and cf008[33] in ["d", "f", "i", "m", "p", "s", "t", "v"] and cf008[29] not in ["a", "b", "c", "o", "f", "q", "s"]:
                resType_eng = "Projected medium - Physical"
                resType_ger = "Projiziertes Medium - Physisch"

            elif ldr[6] == "g" and ldr[7] == "m" and cf008[33] in ["d", "f", "i", "m", "p", "s", "t", "v"] and cf008[29] in ["o", "q", "s"]:
                resType_eng = "Projected medium - Electronic"
                resType_ger = "Projiziertes Medium - Elektronisch"

            elif ldr[6] == "k" and ldr[7] == "m" and cf008[33] in ["a", "c", "i", "k", "l", "n", "o"] and cf008[29] not in ["a", "b", "c", "o", "f", "q", "s"]:
                resType_eng = "2D non-projectable graphic - Physical"
                resType_ger = "2D nicht-projizierbare Grafik - Physisch"

            elif ldr[6] == "k" and ldr[7] == "m" and cf008[33] in ["a", "c", "i", "k", "l", "n", "o"] and cf008[29] in ["o", "q", "s"]:
                resType_eng = "2D non-projectable graphic - Electronic"
                resType_ger = "2D nicht-projizierbare Grafik - Elektronisch"

            elif ldr[6] == "o" and cf008[33] == "b" and cf008[29] not in ["a", "b", "c", "o", "f", "q", "s"]:
                resType_eng = "Kit - Physical"
                resType_ger = "Satz - Physisch"

            elif ldr[6] == "r" and cf008[33] in ["r", "w"] and  cf008[29] not in ["o", "q", "s"]:
                resType_eng = "3D artifact - Physical"
                resType_ger = "3D-Artefakt - Physisch"

            elif ldr[6] == "a" and ldr[7] == "a" and cf008[23] not in ["a", "b", "c", "o", "f", "q", "s"]:
                resType_eng = "Monographic component part - Physical"
                resType_ger = "Monografischer Komponententeil - Physisch"

            elif ldr[6] == "a" and ldr[7] == "a" and cf008[23] in ["o", "q", "s"]:
                resType_eng = "Monographic component part - Electronic"
                resType_ger = "Monografischer Komponententeil - Elektronisch"

    except Exception as ex:
        resType_eng = "Undefined"
        resType_ger = "Nicht definiert"

    return resType_eng#, resType_ger