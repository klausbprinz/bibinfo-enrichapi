# with lobid/json -> pydantic can do the heavy lifting

from typing import Literal, Union, Annotated, Any
from pydantic import BaseModel, Field, Discriminator, Tag, ConfigDict


class LobidGndSameAs(BaseModel):

    idURL: str | None = Field(default=None, description="sameAs elem, list, id node")
    collectionName: str | None = Field(default=None, description="sameAs elem, list, collection elem, name elem")


class LobidGndGeographicAreaCode(BaseModel):
    
    code: str | None = Field(default=None, description="geographicAreaCode elem, list, id elem")
    idURL: str | None = Field(default=None, description="geographicAreaCode elem, list, label elem")


class LobidGndHomepage(BaseModel):

    homepageId: str | None = Field(default=None, description="homepage elem, list, id elem")
    homepageLabel: str | None = Field(default=None, description="homepage elem, list, label elem")


class LobidGndSubjectCategory(BaseModel):

    subjectCategoryId: str | None = Field(default=None, description="gndSubjectCategory elem, list, id elem")
    subjectCategoryLabel: str | None = Field(default=None, description="gndSubjectCategory elem, list, label elem")


class LobidGndAffiliation(BaseModel):

    affiliationId: str | None = Field(default=None, description="affiliation elem, list, id elem")
    affiliationLabel: str | None = Field(default=None, description="affiliation elem, list, label elem")


class LobidGndPlaceOfBusiness(BaseModel):

    pobId: str | None = Field(default=None, description="placeOfBusiness elem, list, id elem")
    pobLabel: str | None = Field(default=None, description="placeOfBusiness elem, list, label elem")


class LobidGndSpatialAreaOfActivity(BaseModel):

    saaId: str | None = Field(default=None, description="spatialAreaOfActivity elem, list, id elem")
    saaLabel: str | None = Field(default=None, description="spatialAreaOfActivity elem, list, label elem")


class LobidGndPlaceOfConferenceOrEvent(BaseModel):

    poceId: str | None = Field(default=None, description="placeOfConferenceOrEvent elem, list, id elem")
    poceLabel: str | None = Field(default=None, description="placeOfConferenceOrEvent elem, list, label elem")


class LobidGndRelatedConferenceOrEvent(BaseModel):

    rceId: str | None = Field(default=None, description="relatedConferenceOrEvent elem, list, id elem")
    rceLabel: str | None = Field(default=None, description="relatedConferenceOrEvent elem, list, label elem")


class LobidGndSponsorOrPatron(BaseModel):

    rpId: str | None = Field(default=None, description="sponsorOrPatron elem, list, id elem")
    rpLabel: str | None = Field(default=None, description="sponsorOrPatron elem, list, label elem")


class BaseLobidGND(BaseModel):

    # enables creating the model using either alias OR Python attribute name
    model_config = ConfigDict(populate_by_name=True)

    entityTypes: list[str] = Field(
        default_factory=list,
        alias="type",  # Lobid JSON key: "types"
        description="Information on type of GND record"
    )


    depictionURLs: list[str] = Field(default_factory=list, description="Depiction URLs")
    geographicAreaCodes: list[LobidGndGeographicAreaCode] = Field(default_factory=list, description="geographicAreaCode elem list")
    sameAs: list[LobidGndSameAs] = Field(default_factory=list, description="idURL and collectionName")
    homepage: list[LobidGndHomepage] = Field(default_factory=list, description="Homepage, Id and Label")
    gndSubjectCategories: list[LobidGndSubjectCategory] = Field(default_factory=list, description="GND Subject Category")

    preferredName: str | None = Field(
        default=None,
        alias="preferredName"  # matches directly, but explicit alias doesn't hurt
    )
    biographicalOrHistoricalInformation: list[str] = Field(
        default_factory=list,
        alias="biographicalOrHistoricalInformation"  # matches directly
    )



class PersonLobidGND(BaseLobidGND):

    gndType: Literal["person"] = "person"

    professionsOrOccupations: list[str] = Field(default_factory=list, description="professionOrOccupation elem, list, label elem")

    datesOfBirth: list[str] = Field(
        default_factory=list,
        alias="dateOfBirth"
    )
    datesOfDeath: list[str] = Field(
        default_factory=list,
        alias="dateOfDeath"
    )

    placesOfBirth: list[str] = Field(default_factory=list, description="placeOfBirth elem, list, label elems")
    placesOfDeath: list[str] = Field(default_factory=list, description="placeOfDeath elem, list, label elems")

    publications: list[str] = Field(
        default_factory=list,
        alias="publication"
    )

    affiliations: list[LobidGndAffiliation] = Field(default_factory=list, description="Affiliations")

    # examples: https://lobid.org/gnd/118610465.json, https://lobid.org/gnd/1046376195.json, https://lobid.org/gnd/11881544X.json


class CorporateLobidGND(BaseLobidGND):

    gndType: Literal["corporate"] = "corporate"

    variantNames: list[str] = Field(
        default_factory=list,
        alias="variantName"
    )

    placesOfBusiness: list[LobidGndPlaceOfBusiness] = Field(default_factory=list, description="Places of Business")
    spatialAreasOfActivity: list[LobidGndSpatialAreaOfActivity] = Field(default_factory=list, description="Spatial Areas of Activity")

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

    placesOfConferenceOrEvent: list[LobidGndPlaceOfConferenceOrEvent] = Field(default_factory=list, description="Places of Conference or Event")
    relatedConferencesOrEvents: list[LobidGndRelatedConferenceOrEvent] = Field(default_factory=list, description="Related Conferences or Events")
    sponsorsOrPatrons: list[LobidGndSponsorOrPatron] = Field(default_factory=list, description="Sponsors or Patrons")

    # examples: https://lobid.org/gnd/6514095-3.json, https://lobid.org/gnd/1216257191.json, https://lobid.org/gnd/2096142-X.json, https://lobid.org/gnd/1058916807.json, https://lobid.org/gnd/5281710-6.json


# catch-all fallback model
class DefaultLobidGND(BaseLobidGND):
    """
    This model catches any entity types that are not explicitly structured yet 
    (e.g., Geografikum, Sachbegriff, Werk). It won't crash the API.
    """
    gndType: str = Field(description="Fallback for unmapped or generic GND types")


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

