from typing import Literal, Union, Annotated
from pydantic import BaseModel, Field, Discriminator


class LobidGndSameAs(BaseModel):

    idURL: str | None = Field(default=None, description="sameAs elem, list, id node")
    collectionName: str | None = Field(default=None, description="sameAs elem, list, collection elem, name elem")


class LobidGndGeographicAreaCode(BaseModel):
    
    code: str | None = Field(default=None, description="geographicAreaCode elem, list, id elem")
    idURL: str | None = Field(default=None, description="geographicAreaCode elem, list, label elem")


class LobidGndEntityTypes(BaseModel):

    types: list[str] = Field(default=[], description="type elem, list")


class LobidGndDepictionURLs(BaseModel):

    urls: list[str] = Field(default=[], description="depiction elem, list, id node")


class LobidGndHomepage(BaseModel):

    homepageId: str | None = Field(default=None, description="homepage elem, list, id elem")
    homepageLabel: str | None = Field(default=None, description="homepage elem, list, label elem")


class LobidGndSubjectCategory(BaseModel):

    subjectCategoryId: str | None = Field(default=None, description="gndSubjectCategory elem, list, id elem")
    subjectCategoryLabel: str | None = Field(default=None, description="gndSubjectCategory elem, list, label elem")


class LobidGndAffiliation(BaseModel):

    affiliationId: str | None = Field(default=None, description="affiliation elem, list, id elem")
    affiliationLabel: str | None = Field(default=None, description="affiliation elem, list, label elem")


class LobidGndPreferredName(BaseModel):

    preferredName: str | None = Field(default=None, description="preferredName elem, text node")


class LobidGndVariantNames(BaseModel):

    variantNames: list[str] = Field(default=[], description="variantName elem, list, text nodes")


class LobidGndPlaceOfBusiness(BaseModel):

    pobId: str | None = Field(default=None, description="placeOfBusiness elem, list, id elem")
    pobLabel: str | None = Field(default=None, description="placeOfBusiness elem, list, label elem")


class LobidGndSpatialAreaOfActivity(BaseModel):

    saaId: str | None = Field(default=None, description="spatialAreaOfActivity elem, list, id elem")
    saaLabel: str | None = Field(default=None, description="spatialAreaOfActivity elem, list, label elem")


class LobidGndBiographicalOrHistoricalInfos(BaseModel):

    bohInfos: list[str] = Field(default=[], description="biographicalOrHistoricalInformation elem, list, text nodes")


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

    entityTypes: LobidGndEntityTypes = Field(description="Information on type of GND record (I guess)")
    depictionURLs: list[LobidGndDepictionURLs] = Field(default=[], description="Depiction")
    geographicAreaCodes: list[LobidGndGeographicAreaCode] = Field(default=[], description="geographicAreaCode elem list")
    sameAs: list[LobidGndSameAs] = Field(default=[], description="idURL and collectionName")
    homepage: list[LobidGndHomepage] = Field(default=[], description="Homepage, Id and Label")
    gndSubjectCategories: list[LobidGndSubjectCategory] = Field(default=[], description="GND Subject Category")
    preferredName: LobidGndPreferredName = Field(description="Preferred Name")
    biographicalOrHistoricalInformation: LobidGndBiographicalOrHistoricalInfos = Field(description="Biographical or Historical Information")



class PersonLobidGND(BaseLobidGND):

    gndType: Literal["person"] = "person"
    professionsOrOccupations: list[str] = Field(default=[], description="professionOrOccupation elem, list, label elem")
    datesOfBirth: list[str] = Field(default=[], description="dateOfBirth elem, list, text nodes")
    datesOfDeath: list[str] = Field(default=[], description="dateOfDeath elem, list, text nodes")
    placesOfBirth: list[str] = Field(default=[], description="placeOfBirth elem, list, label elems")
    placesOfDeath: list[str] = Field(default=[], description="placeOfDeath elem, list, label elems")
    publications: list[str] = Field(default=[], description="publication elem, list, text nodes")
    affiliations: list[LobidGndAffiliation] = Field(default=[], description="Affiliations")

    # examples: https://lobid.org/gnd/118610465.json, https://lobid.org/gnd/1046376195.json, https://lobid.org/gnd/11881544X.json


class CorporateLobidGND(BaseLobidGND):

    gndType: Literal["corporate"] = "corporate"
    variantNames: LobidGndVariantNames = Field(description="Variant Names")
    placesOfBusiness: list[LobidGndPlaceOfBusiness] = Field(default=[], description="Places of Business")
    spatialAreasOfActivity: list[LobidGndSpatialAreaOfActivity] = Field(default=[], description="Spatial Areas of Activity")
    datesOfEstablishment: list[str] = Field(default=[], description="dateOfEstablishment, list, text nodes")

    # examples: https://lobid.org/gnd/2024703-5.json, https://lobid.org/gnd/38633-9.json, https://lobid.org/gnd/5003949-0.json


class ConferenceOrEventLobidGND(BaseLobidGND):

    gndType: Literal["conferenceOrEvent"] = "conferenceOrEvent"
    variantNames: LobidGndVariantNames = Field(description="Variant Names")
    datesOfConferenceOrEvent: list[str] = Field(default=[], description="datesOfConferenceOrEvent elem, list, text nodes")
    placesOfConferenceOrEvent: list[LobidGndPlaceOfConferenceOrEvent] = Field(default=[], description="Places of Conference or Event")
    relatedConferencesOrEvents: list[LobidGndRelatedConferenceOrEvent] = Field(default=[], description="Related Conferences or Events")
    sponsorsOrPatrons: list[LobidGndSponsorOrPatron] = Field(default=[], description="Sponsors or Patrons")

    # examples: https://lobid.org/gnd/6514095-3.json, https://lobid.org/gnd/1216257191.json, https://lobid.org/gnd/2096142-X.json, https://lobid.org/gnd/1058916807.json, https://lobid.org/gnd/5281710-6.json



class DataLobidGND(BaseModel):

    gndId: str = Field(description="GND ID to use for enrichment")
    
    gndInformation: Annotated[
        Union[PersonLobidGND, CorporateLobidGND, ConferenceOrEventLobidGND],
        Discriminator("gndType")
    ] = Field(description="Use lobid API: https://lobid.org/gnd/<gndid>.json")

