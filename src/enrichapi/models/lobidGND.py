# with lobid/json -> pydantic can do the heavy lifting

from typing import Literal, Union, Annotated, Any
from pydantic import BaseModel, Field, Discriminator, Tag, ConfigDict, field_validator, model_validator


class LobidGndSameAs(BaseModel):

    idURL: str | None = Field(default=None, alias="id")
    collectionName: str | None = Field(default=None)

    @model_validator(mode="before")
    @classmethod
    def flattenCollectionName(cls, raw: Any) -> Any:
        if isinstance(raw, dict):
            collectionDict = raw.get("collection")
            if isinstance(collectionDict, dict):
                # safe copy or direct update
                return {**raw, "collectionName": collectionDict.get("name")}
        return raw


class LobidGndGeographicAreaCode(BaseModel):
    
    code: str | None = Field(default=None, description="Extracted code, e.g. XA-AT")
    idURL: str | None = Field(default=None, alias="id", description="Full URL string")

    @model_validator(mode="before")
    @classmethod
    def extractCodeAndUrl(cls, raw: Any) -> Any:
        if isinstance(raw, dict):
            # grab full URL from 'id'
            fullUrl = raw.get("id")
            if isinstance(fullUrl, str):
                # ensure idURL gets populated
                raw["idURL"] = fullUrl
                
                # extract fragment after '#' (e.g. "XA-AT") if present
                if "#" in fullUrl:
                    raw["code"] = fullUrl.split("#")[-1]
                else:
                    raw["code"] = fullUrl.rstrip("/").split("/")[-1]
        return raw


class LobidGndHomepage(BaseModel):

    homepageId: str | None = Field(default=None, alias="id")
    homepageLabel: str | None = Field(default=None, alias="label")


class LobidGndSubjectCategory(BaseModel):

    subjectCategoryId: str | None = Field(default=None, alias="id")
    subjectCategoryLabel: str | None = Field(default=None, alias="label")


class LobidGndAffiliation(BaseModel):

    affiliationId: str | None = Field(default=None, alias="id")
    affiliationLabel: str | None = Field(default=None, alias="label")


class LobidGndPlaceOfBusiness(BaseModel):

    pobId: str | None = Field(default=None, alias="id")
    pobLabel: str | None = Field(default=None, alias="label")


class LobidGndSpatialAreaOfActivity(BaseModel):

    saaId: str | None = Field(default=None, alias="id")
    saaLabel: str | None = Field(default=None, alias="label")


class LobidGndPlaceOfConferenceOrEvent(BaseModel):

    poceId: str | None = Field(default=None, alias="id")
    poceLabel: str | None = Field(default=None, alias="label")


class LobidGndRelatedConferenceOrEvent(BaseModel):

    rceId: str | None = Field(default=None, alias="id")
    rceLabel: str | None = Field(default=None, alias="label")


class LobidGndSponsorOrPatron(BaseModel):

    rpId: str | None = Field(default=None, alias="id")
    rpLabel: str | None = Field(default=None, alias="label")


class BaseLobidGND(BaseModel):

    # enables creating the model using either alias OR Python attribute name
    model_config = ConfigDict(populate_by_name=True)

    entityTypes: list[str] = Field(
        default_factory=list,
        alias="type",  # Lobid JSON key: "types"
        description="Information on type of GND record"
    )
    preferredName: str | None = Field(
        default=None,
        alias="preferredName"  # matches directly, but explicit alias doesn't hurt
    )
    biographicalOrHistoricalInformation: list[str] = Field(
        default_factory=list,
        alias="biographicalOrHistoricalInformation"  # matches directly
    )

    depictionURLs: list[str] = Field(default_factory=list, alias="depiction")
    # validate depiction before parsing
    @field_validator("depictionURLs", mode="before")
    @classmethod
    def extractDepictionURLs(cls, rawVal: Any) -> list[str]:
        if not rawVal:
            return []
        if isinstance(rawVal, list):
            # pull "id" string from each depiction dictionary
            return [item.get("id") for item in rawVal if isinstance(item, dict) and "id" in item]
        return []

    geographicAreaCodes: list[LobidGndGeographicAreaCode] = Field(
        default_factory=list, alias="geographicAreaCode"
    )
    sameAs: list[LobidGndSameAs] = Field(default_factory=list, alias="sameAs")
    homepage: list[LobidGndHomepage] = Field(default_factory=list, alias="homepage")
    gndSubjectCategories: list[LobidGndSubjectCategory] = Field(
        default_factory=list, alias="gndSubjectCategory"
    )


class PersonLobidGND(BaseLobidGND):

    gndType: Literal["person"] = "person"

    # define fields with aliases to Lobid JSON keys (simple for str | list[str])
    professionsOrOccupations: list[str] = Field(default_factory=list, alias="professionOrOccupation")
    placesOfBirth: list[str] = Field(default_factory=list, alias="placeOfBirth")
    placesOfDeath: list[str] = Field(default_factory=list, alias="placeOfDeath")

    # attach one validator to multiple fields
    # intercepts raw JSON for field before Pydantic checks types
    # for: extracting strings/labels from dicts, flattening lists
    @field_validator("professionsOrOccupations", "placesOfBirth", "placesOfDeath", mode="before")
    @classmethod
    def extractLabels(cls, rawVal: Any) -> list[str]:
        if not rawVal:
            return []
        if isinstance(rawVal, list):
            # if item is {"id": "...", "label": "Physicist"}, pull "label"
            return [item.get("label") if isinstance(item, dict) else str(item) for item in rawVal]
        return []

    datesOfBirth: list[str] = Field(
        default_factory=list,
        alias="dateOfBirth"
    )
    datesOfDeath: list[str] = Field(
        default_factory=list,
        alias="dateOfDeath"
    )
    publications: list[str] = Field(
        default_factory=list,
        alias="publication"
    )

    affiliations: list[LobidGndAffiliation] = Field(default_factory=list, alias="affiliation")

    # examples: https://lobid.org/gnd/118610465.json, https://lobid.org/gnd/1046376195.json, https://lobid.org/gnd/11881544X.json


class CorporateLobidGND(BaseLobidGND):

    gndType: Literal["corporate"] = "corporate"

    variantNames: list[str] = Field(
        default_factory=list,
        alias="variantName"
    )

    placesOfBusiness: list[LobidGndPlaceOfBusiness] = Field(
        default_factory=list, alias="placeOfBusiness"
    )
    spatialAreasOfActivity: list[LobidGndSpatialAreaOfActivity] = Field(
        default_factory=list, alias="spatialAreaOfActivity"   
    )

    datesOfEstablishment: list[str] = Field(
        default_factory=list,
        alias="dateOfEstablishment"
    )

    # examples: https://lobid.org/gnd/2024703-5.json, https://lobid.org/gnd/38633-9.json, https://lobid.org/gnd/5003949-0.json


class ConferenceOrEventLobidGND(BaseLobidGND):

    gndType: Literal["conferenceOrEvent"] = "conferenceOrEvent"

    variantNames: list[str] = Field(
        default_factory=list,
        alias="variantName"
    )
    datesOfConferenceOrEvent: list[str] = Field(
        default_factory=list,
        alias="dateOfConferenceOrEvent"
    )

    placesOfConferenceOrEvent: list[LobidGndPlaceOfConferenceOrEvent] = Field(
        default_factory=list, alias="placeOfConferenceOrEvent"
    )
    relatedConferencesOrEvents: list[LobidGndRelatedConferenceOrEvent] = Field(
        default_factory=list, alias="relatedConferenceOrEvent"
    )
    sponsorsOrPatrons: list[LobidGndSponsorOrPatron] = Field(
        default_factory=list, alias="sponsorOrPatron"
    )

    # examples: https://lobid.org/gnd/6514095-3.json, https://lobid.org/gnd/1216257191.json, https://lobid.org/gnd/2096142-X.json, https://lobid.org/gnd/1058916807.json, https://lobid.org/gnd/5281710-6.json


# catch-all fallback model
class DefaultLobidGND(BaseLobidGND):
    """
    This model catches any entity types that are not explicitly structured yet 
    (e.g., Geografikum, Sachbegriff, Werk). It won't crash the API.
    """
    gndType: str = Field(default="default", description="Fallback for unmapped or generic GND types")


# discriminator function to determine the model dynamically
def resolveGndType(v: Any) -> str:
    # extract types list from dict or model instance
    types = []
    if isinstance(v, BaseModel):
        types = getattr(v, "entityTypes", []) or getattr(v, "type", [])
    elif isinstance(v, dict):
        types = v.get("type", []) or v.get("entityTypes", [])
    
    if isinstance(types, str):
        types = [types]

    # inspect type array for matching entity tag
    if "Person" in types:
        return "person"
    if "CorporateBody" in types:
        return "corporate"
    if any(t in types for t in ("Event", "ConferenceOrEvent")):
        return "conferenceOrEvent"

    # fallback tag for Geografikum, Sachbegriff, Werk, etc.
    return "default"


class DataLobidGND(BaseModel):

    gndId: str = Field(description="GND ID to use for enrichment")
    
    # apply custom discriminator function
    gndInformation: Annotated[
        Union[
            Annotated[PersonLobidGND, Tag("person")],
            Annotated[CorporateLobidGND, Tag("corporate")],
            Annotated[ConferenceOrEventLobidGND, Tag("conferenceOrEvent")],
            Annotated[DefaultLobidGND, Tag("default")]
        ],
        Discriminator(resolveGndType)
    ] = Field(description="Use lobid API: https://lobid.org/gnd/<gndid>.json with fallback routing")
