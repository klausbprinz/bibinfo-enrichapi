from typing import Literal, Union, Annotated, Any
from pydantic import (
    BaseModel,
    Field,
    Discriminator,
    Tag,
    ConfigDict,
    field_validator,
)


class WikidataBaseInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    label: str | None = Field(default=None, description="Primary entity label/name")
    instanceOf: list[str] = Field(default_factory=list, alias="P31", description="Instance of (P31)")
    image: list[str] = Field(default_factory=list, alias="P18", description="Image (P18)")

    @field_validator("*", mode="before")
    @classmethod
    def ensureStringList(cls, rawVal: Any, info) -> Any:
        # pass non-list scalar fields straight through after unpacking lists
        if info.field_name in ("wikidataType", "label"):
            if isinstance(rawVal, list):
                return rawVal[0] if rawVal else None
            return rawVal

        if rawVal is None:
            return []
        if isinstance(rawVal, list):
            return [
                item.get("value") or item.get("label") if isinstance(item, dict) else str(item)
                for item in rawVal
                if item is not None
            ]
        if isinstance(rawVal, dict):
            val = rawVal.get("value") or rawVal.get("label") or str(rawVal)
            return [val]
        return [str(rawVal)]
    

class WikidataPerson(WikidataBaseInfo):
    wikidataType: Literal["person"] = "person"

    countryOfCitizenship: list[str] = Field(default_factory=list, alias="P27", description="P27")
    occupation: list[str] = Field(default_factory=list, alias="P106", description="P106")
    fieldOfWork: list[str] = Field(default_factory=list, alias="P101", description="P101")
    employer: list[str] = Field(default_factory=list, alias="P108", description="P108")
    educatedAt: list[str] = Field(default_factory=list, alias="P69", description="P69")
    participantIn: list[str] = Field(default_factory=list, alias="P1344", description="P1344")
    residence: list[str] = Field(default_factory=list, alias="P551", description="P551")
    notableWork: list[str] = Field(default_factory=list, alias="P800", description="P800")
    memberOf: list[str] = Field(default_factory=list, alias="P463", description="P463")
    describedAtURL: list[str] = Field(default_factory=list, alias="P973", description="P973")
    movement: list[str] = Field(default_factory=list, alias="P135", description="P135")
    influencedBy: list[str] = Field(default_factory=list, alias="P737", description="P737")
    timePeriod: list[str] = Field(default_factory=list, alias="P2348", description="P2348")
    describedBySource: list[str] = Field(default_factory=list, alias="P1343", description="P1343")


class WikidataCorporate(WikidataBaseInfo):
    wikidataType: Literal["corporate"] = "corporate"

    industry: list[str] = Field(default_factory=list, alias="P452", description="P452")
    inception: list[str] = Field(default_factory=list, alias="P571", description="P571")
    nativeLabel: list[str] = Field(default_factory=list, alias="P1705", description="P1705")
    affiliation: list[str] = Field(default_factory=list, alias="P1416", description="P1416")
    officialName: list[str] = Field(default_factory=list, alias="P1448", description="P1448")
    fieldOfWork: list[str] = Field(default_factory=list, alias="P101", description="P101")
    founder: list[str] = Field(default_factory=list, alias="P112", description="P112")
    country: list[str] = Field(default_factory=list, alias="P17", description="P17")
    location: list[str] = Field(default_factory=list, alias="P276", description="P276")
    legalForm: list[str] = Field(default_factory=list, alias="P1454", description="P1454")
    officialWebsite: list[str] = Field(default_factory=list, alias="P856", description="P856")


class WikidataConferenceEvent(WikidataBaseInfo):
    wikidataType: Literal["conferenceOrEvent"] = "conferenceOrEvent"

    title: list[str] = Field(default_factory=list, alias="P1476", description="P1476")
    shortName: list[str] = Field(default_factory=list, alias="P1813", description="P1813")
    country: list[str] = Field(default_factory=list, alias="P17", description="P17")
    location: list[str] = Field(default_factory=list, alias="P276", description="P276")
    partOfTheSeries: list[str] = Field(default_factory=list, alias="P179", description="P179")
    hasParts: list[str] = Field(default_factory=list, alias="P527", description="P527")
    mainSubject: list[str] = Field(default_factory=list, alias="P921", description="P921")
    languageUsed: list[str] = Field(default_factory=list, alias="P2936", description="P2936")
    startTime: list[str] = Field(default_factory=list, alias="P580", description="P580")
    endTime: list[str] = Field(default_factory=list, alias="P585", description="P585")
    organizer: list[str] = Field(default_factory=list, alias="P664", description="P664")
    officialWebsite: list[str] = Field(default_factory=list, alias="P856", description="P856")


# slim fallback model
class DefaultWikidata(WikidataBaseInfo):
    wikidataType: Literal["default"] = "default"


def resolveWikidataType(v: Any) -> str:
    """
    Discriminator reading explicit entity type passed down from MARC21 nameType.
    Falls back to checking P31 (instanceOf) or 'default' if omitted.
    """
    targetType = None

    if isinstance(v, BaseModel):
        targetType = getattr(v, "wikidataType", None)
    elif isinstance(v, dict):
        targetType = v.get("wikidataType") or v.get("entityType")

    # primary route: explicit type passed from MARC21 nameType
    if targetType in ("person", "corporate", "conferenceOrEvent"):
        return targetType

    # fallback route: inspect P31 if no explicit type provided
    p31List = []
    if isinstance(v, BaseModel):
        p31List = getattr(v, "instanceOf", []) or getattr(v, "P31", [])
    elif isinstance(v, dict):
        p31List = v.get("P31", []) or v.get("instanceOf", [])

    if isinstance(p31List, str):
        p31List = [p31List]

    p31Set = {str(item).lower().strip() for item in p31List}

    personMarkers = {"q5", "mensch", "human"}
    corporateMarkers = {
        "q43229", "organisation", "organization", "unternehmen", 
        "business", "bibliothek", "library", "hochschule", "university"
    }
    eventMarkers = {"q1656682", "ereignis", "event", "konferenz", "conference"}

    if p31Set.intersection(personMarkers):
        return "person"
    if p31Set.intersection(corporateMarkers):
        return "corporate"
    if p31Set.intersection(eventMarkers):
        return "conferenceOrEvent"

    return "default"


class DataWikidata(BaseModel):
    wikidataId: str = Field(description="Wikidata Q-ID used for enrichment")

    wikidataInformation: Annotated[
        Union[
            Annotated[WikidataPerson, Tag("person")],
            Annotated[WikidataCorporate, Tag("corporate")],
            Annotated[WikidataConferenceEvent, Tag("conferenceOrEvent")],
            Annotated[DefaultWikidata, Tag("default")],
        ],
        Discriminator(resolveWikidataType),
    ] = Field(description="Structured Wikidata information parsed dynamically")