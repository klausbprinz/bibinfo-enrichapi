from typing import Literal
from pydantic import BaseModel, Field


class LobidGND_SameAs(BaseModel):

    idURL: str | None = Field(default=None, description="sameAs elem, list, id node")
    collectionName: str | None = Field(default=None, description="sameAs elem, list, collection elem, name elem")


class LobidGND_GeographicAreaCode(BaseModel):
    
    code: str | None = Field(default=None, description="geographicAreaCode elem, list, id elem")
    idURL: str | None = Field(default=None, description="geographicAreaCode elem, list, label elem")


class LobidGND_EntityTypes(BaseModel):

    types: list[str] = Field(default=[], description="type elem, list")


class LobidGND_DepictionURLs(BaseModel):

    urls: list[str] = Field(default=[], description="depiction elem, list, id node")


class LobidGND_Homepage(BaseModel):

    homepageId: str | None = Field(default=None, description="homepage elem, list, id elem")
    homepageLabel: str | None = Field(default=None, description="homepage elem, list, label elem")


class LobidGND_SubjectCategory(BaseModel):

    subjectCategoryId: str | None = Field(default=None, description="gndSubjectCategory elem, list, id elem")
    subjectCategoryLabel: str | None = Field(default=None, description="gndSubjectCategory elem, list, label elem")


class LobidGND_Affiliation(BaseModel):

    affiliationId: str | None = Field(default=None, description="affiliation elem, list, id elem")
    affiliationLabel: str | None = Field(default=None, description="affiliation elem, list, label elem")


class LobidGND_PreferredName(BaseModel):

    preferredName: str | None = Field(default=None, description="preferredName elem, text node")


class LobidGND_VariantNames(BaseModel):

    variantNames: list[str] = Field(default=[], description="variantName elem, list, text nodes")


class LobidGND_PlaceOfBusiness(BaseModel):

    pobId: str | None = Field(default=None, description="placeOfBusiness elem, list, id elem")
    pobLabel: str | None = Field(default=None, description="placeOfBusiness elem, list, label elem")


class LobidGND_SpatialAreaOfActivity(BaseModel):

    saaId: str | None = Field(default=None, description="spatialAreaOfActivity elem, list, id elem")
    saaLabel: str | None = Field(default=None, description="spatialAreaOfActivity elem, list, label elem")


class LobidGND_BiographicalOrHistoricalInfos(BaseModel):

    bohInfos: list[str] = Field(default=[], description="biographicalOrHistoricalInformation elem, list, text nodes")


class LobidGND_PlaceOfConferenceOrEvent(BaseModel):

    poceId: str | None = Field(default=None, description="placeOfConferenceOrEvent elem, list, id elem")
    poceLabel: str | None = Field(default=None, description="placeOfConferenceOrEvent elem, list, label elem")


class LobidGND_RelatedConferenceOrEvent(BaseModel):

    rceId: str | None = Field(default=None, description="relatedConferenceOrEvent elem, list, id elem")
    rceLabel: str | None = Field(default=None, description="relatedConferenceOrEvent elem, list, label elem")


class LobidGND_SponsorOrPatron(BaseModel):

    rpId: str | None = Field(default=None, description="sponsorOrPatron elem, list, id elem")
    rpLabel: str | None = Field(default=None, description="sponsorOrPatron elem, list, label elem")


class PersonLobidGND(BaseModel):

    entityTypes: LobidGND_EntityTypes = Field(description="Information on type of GND record (I guess)")
    depictionURLs: list[LobidGND_DepictionURLs] = Field(default=[], description="Depiction")
    professionsOrOccupations: list[str] = Field(default=[], description="professionOrOccupation elem, list, label elem")
    geographicAreaCodes: list[LobidGND_GeographicAreaCode] = Field(default=[], description="geographicAreaCode elem list")
    datesOfBirth: list[str] = Field(default=[], description="dateOfBirth elem, list, text nodes")
    datesOfDeath: list[str] = Field(default=[], description="dateOfDeath elem, list, text nodes")
    placesOfBirth: list[str] = Field(default=[], description="placeOfBirth elem, list, label elems")
    placesOfDeath: list[str] = Field(default=[], description="placeOfDeath elem, list, label elems")
    sameAs: list[LobidGND_SameAs] = Field(default=[], description="idURL and collectionName")
    publications: list[str] = Field(default=[], description="publication elem, list, text nodes")
    homepage: list[LobidGND_Homepage] = Field(default=[], description="Homepage, Id and Label")
    gndSubjectCategories: list[LobidGND_SubjectCategory] = Field(default=[], description="GND Subject Category")
    preferredName: LobidGND_PreferredName = Field(description="Preferred Name")
    biographicalOrHistoricalInformation: LobidGND_BiographicalOrHistoricalInfos = Field(description="Biographical or Historical Information")
    affiliations: list[LobidGND_Affiliation] = Field(default=[], description="Affiliations")

    # examples: https://lobid.org/gnd/118610465.json, https://lobid.org/gnd/1046376195.json, https://lobid.org/gnd/11881544X.json


class CorporateLobidGND(BaseModel):

    entityTypes: LobidGND_EntityTypes = Field(description="Information on Type of GND Record (I guess)")
    depictionURLs: list[LobidGND_DepictionURLs] = Field(default=[], description="Depiction")
    geographicAreaCodes: list[LobidGND_GeographicAreaCode] = Field(default=[], description="geographicAreaCode elem list")
    sameAs: list[LobidGND_SameAs] = Field(default=[], description="idURL and collectionName")
    homepage: list[LobidGND_Homepage] = Field(default=[], description="Homepage, Id, and Label")
    gndSubjectCategories: list[LobidGND_SubjectCategory] = Field(default=[], description="GND Subject Category")
    preferredName: LobidGND_PreferredName = Field(description="Preferred Name")
    variantNames: LobidGND_VariantNames = Field(description="Variant Names")
    placesOfBusiness: list[LobidGND_PlaceOfBusiness] = Field(default=[], description="Places of Business")
    spatialAreasOfActivity: list[LobidGND_SpatialAreaOfActivity] = Field(default=[], description="Spatial Areas of Activity")
    datesOfEstablishment: list[str] = Field(default=[], description="dateOfEstablishment, list, text nodes")
    biographicalOrHistoricalInformation: LobidGND_BiographicalOrHistoricalInfos = Field(description="Biographical or Historical Information")

    # examples: https://lobid.org/gnd/2024703-5.json, https://lobid.org/gnd/38633-9.json, https://lobid.org/gnd/5003949-0.json


class ConferenceOrEventLobidGND(BaseModel):

    entityTypes: LobidGND_EntityTypes = Field(description="Information on type of GND record (I guess)")
    depictionURLs: list[LobidGND_DepictionURLs] = Field(default=[], description="Depiction")
    geographicAreaCodes: list[LobidGND_GeographicAreaCode] = Field(default=[], description="geographicAreaCode elem list")
    sameAs: list[LobidGND_SameAs] = Field(default=[], description="idURL and collectionName")
    homepage: list[LobidGND_Homepage] = Field(default=[], description="Homepage, Id and Label")
    gndSubjectCategories: list[LobidGND_SubjectCategory] = Field(default=[], description="GND Subject Category")
    preferredName: LobidGND_PreferredName = Field(description="Preferred Name")
    variantNames: LobidGND_VariantNames = Field(description="Variant Names")
    biographicalOrHistoricalInformation: LobidGND_BiographicalOrHistoricalInfos = Field(description="Biographical or Historical Information")
    datesOfConferenceOrEvent: list[str] = Field(default=[], description="datesOfConferenceOrEvent elem, list, text nodes")
    placesOfConferenceOrEvent: list[LobidGND_PlaceOfConferenceOrEvent] = Field(default=[], description="Places of Conference or Event")
    relatedConferencesOrEvents: list[LobidGND_RelatedConferenceOrEvent] = Field(default=[], description="Related Conferences or Events")
    sponsorsOrPatrons: list[LobidGND_SponsorOrPatron] = Field(default=[], description="Sponsors or Patrons")

    # examples: https://lobid.org/gnd/6514095-3.json, https://lobid.org/gnd/1216257191.json, https://lobid.org/gnd/2096142-X.json, https://lobid.org/gnd/1058916807.json, https://lobid.org/gnd/5281710-6.json



class DataLobidGND(BaseModel):

    gndId: str = Field(description="GND ID to use for enrichment")
    gndIdType: Literal["person", "corporate", "conferenceOrEvent"] = Field(description="Type derived from Marc21 fields")
    gndInformation: PersonLobidGND | CorporateLobidGND | ConferenceOrEventLobidGND = Field(description="Use lobid API: https://lobid.org/gnd/<gndid>.json")

