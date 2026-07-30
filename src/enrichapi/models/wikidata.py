from typing import Literal, Union, Annotated, Any
from pydantic import BaseModel, Field, Discriminator, Tag, ConfigDict


class WikidataBaseInfo(BaseModel):

    # all inheriting models get the config
    model_config = ConfigDict(populate_by_name=True)

    instanceOf: list[str] = Field(default_factory=list, alias="P31", description="Instance of (P31)")
    image: list[str] = Field(default_factory=list, alias="P18", description="Image (P18)")


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


# catch-all fallback model for unexpected Wikidata entity categories
class DefaultWikidata(WikidataBaseInfo):
    
    wikidataType: str = Field(description="Fallback for unmapped Wikidata types")


def resolveWikidataType(v: Any) -> str:

    # handle Pydantic model instance as well as dict
    if isinstance(v, BaseModel):
        entityType = getattr(v, "entityType", None) # or whichever field stores the type string
    elif isinstance(v, dict):
        entityType = v.get("entityType")
    else:
        entityType = None

    if entityType in ("Person", "Work", "Place", "Organization"): # adjust list to match your tags
        return entityType

    return "default"


class DataWikidata(BaseModel):

    wikidataId: str = Field(description="Wikidata ID to use for enrichment")
    otherIds: list[str] = Field(default_factory=list, description="Other IDs to try with SPARQL")
    
    wikidataInformation: Annotated[
        Union[
            Annotated[WikidataPerson, Tag("person")],
            Annotated[WikidataCorporate, Tag("corporate")],
            Annotated[WikidataConferenceEvent, Tag("conferenceOrEvent")],
            Annotated[DefaultWikidata, Tag("default")]
        ],
        Discriminator(resolveWikidataType)
    ] = Field(description="Use SPARQL with Wikidata endpoint with safety fallback routing")
