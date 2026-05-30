from typing import Literal
from pydantic import BaseModel, Field

class Marc21MD_Title(BaseModel):

    titleMain: str = Field(description="Title (245a NR)")
    titleRemainder: str | None = Field(default=None, description="Remainder of title (245b NR)")
    titlePartNumber: list[str] = Field(default=[], description="Number of part/section of a work (245n R)")
    titlePartName: list[str] = Field(default=[], description="Name of part/section of a work (245p R)")

class Marc21MD_MainEntry(BaseModel):

    name: str | None = Field(default=None, description="Name (100/110/111a NR)")
    nameType: Literal["personal", "corporate", "meeting"] | None = Field(default=None, description="Type of name in main entry")
    relator: list[str] = Field(default=[], description="Codes for relationship between a name and a work (100/110/1114 R)")
    gndIdentifier: str | None = Field(default=None, description="GND-ID (100/110/1110 NR)")

class Marc21MD_AddedEntry(BaseModel):

    name: str | None = Field(default=None, description="Name (700/710/711a NR)")
    nameType: Literal["personal", "corporate", "meeting"] | None = Field(default=None, description="Type of name in added entry")
    relator: list[str] = Field(default=[], description="Codes for relationship between a name and a work (700/710/7114 R)")
    gndIdentifier: str | None = Field(default=None, description="GND-ID (700/710/7110 NR)")

class Marc21MD_PhysDescription(BaseModel):

    extent: str | None = Field(default=None, description="Number of physical pages, volumes, cassettes, total playing time, etc., of each type of unit (300a NR)")
    otherPhysDetails: str | None = Field(default=None, description="Other physical details (300b NR)")
    dimensions: str | None = Field(default=None, description="Dimensions (300c NR)")

class Marc21MD_PublicationNotice(BaseModel):

    pnType: Literal["current", "other"] = Field(default="other", description="Indicators 31 mark current, rest is others (simplification)")
    dating: str | None = Field(default=None, description="OBV specific, marks specific publication history, only periodicals (2643 NR)")
    places: list[str] = Field(default=[], description="Places of publication (264a R)")
    names: list[str] = Field(default=[], description="Names of publishers (264b R)")
    dates: list[str] = Field(default=[], description="Dates of publication (264c R)")

class Marc21MD_ClassificationNumber(BaseModel):

    classificationType: str = Field(default="other", description="if 082a: DDC, if 084a: value from $$2")
    classificationNumber: str | None = Field(default=None, description="082a/084a NR")

class Marc21MD_Identifier(BaseModel):
    
    identifier: str | None = Field(default=None, description="Identifier")
    marcOriginField: Literal["035", "020", "022", "024"] = Field(description="Marc21 origin field")
    prefix: str | None = Field(default=None, description="Prefix of Identifier, e.g. '(AT-OBV)' in 035a")
    additionalInfos: list[str] = Field(default=[], description="Explanatory information, e.g. ISBN (024q R)")

class Marc21MD_HoldingInfos(BaseModel):

    libraryCode: str | None = Field(default=None, description="Library Code (AVAb NR)")
    libraryLabel: str | None = Field(default=None, description="Library Label (AVAc NR)")
    locationCode: str | None = Field(default=None, description="Location Code (AVAj NR)")
    locationLabel: str | None = Field(default=None, description="Location Label (AVAq NR)")
    callNumber: str | None = Field(default=None, description="Call Number (AVAd NR)")
    

class BasicMarc21MD(BaseModel):

    title: Marc21MD_Title = Field(description="Title information (245abnp NR)")
    mainEntry: Marc21MD_MainEntry = Field(description="Main entry information (100/110/111a40 NR)")
    addedEntries: list[Marc21MD_AddedEntry] = Field(default=[], description="List of added entry information (700/710/711a40 R)")
    languageCodes: list[str] = Field(default=[], description="Language codes of text/sound track or separate title (041a R)")
    languageCodesOriginal: list[str] = Field(default=[], description="Language codes of original (041h R)")
    publicationCountryCodes: list[str] = Field(default=[], description="Country of Publishing/Producing Entity Code ISO (044c R)")
    edition: str | None = Field(default=None, description="Edition Statement (250a NR)")
    physicalDescriptions: list[Marc21MD_PhysDescription] = Field(default=[], description="Physical Description (300 R)")
    publicationNotices : list[Marc21MD_PublicationNotice] = Field(default=[], description="Publication Notice (264 R)")
    genreForms: list[str] = Field(default=[], description="Index Term-Genre/Form ( 655#7a R)")
    subjectHeadings: list[str] = Field(default=[], description="Subject Headings from 650a, 653a, 689a (second indicator != #)")
    classifications: list[Marc21MD_ClassificationNumber] = Field(default=[], description="Classification Number: DDC or other (082/084)")
    bibMaterialType: str = Field(default="other", description="Mapping from leader")
    bibResourceType: str = Field(default="other", description="Mapping from leader and 008")
    fullTextURLs: list[str] = Field(default=[], description="Full text URLs (856u if 8563 == 'Volltext')")
    abstracts: list[str] = Field(default=[], description="Summary, etc. 520a")
    tableOfContentURLs: list[str] = Field(default=[], description="Table of content URLs (856u if 8563 == 'Inhaltsverzeichnis')")
    identifier: list[Marc21MD_Identifier] = Field(default=[], description="Identifier and additional infos (035a, 020a, 022a, 024a)")
    holdingInfos: list[Marc21MD_HoldingInfos] = Field(default=[], description="Holding Information: Lib, Loc, CN (AVA R)")
