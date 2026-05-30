from typing import Literal
from pydantic import BaseModel, Field


class Wikidata_BaseInfo(BaseModel):

    instanceOf: list[str] = Field(default=[], description="...")
    image: list[str] = Field(default=[], description="...")


class WikidataPerson(BaseModel):

    baseInfo: Wikidata_BaseInfo = Field(description="Shared fields: instanceOf, image")
    countryOfCitizenship: list[str] = Field(default=[], description="...")
    occupation: list[str] = Field(default=[], description="...")
    fieldOfWork: list[str] = Field(default=[], description="...")
    employer: list[str] = Field(default=[], description="...")
    educatedAt: list[str] = Field(default=[], description="...")
    participantIn: list[str] = Field(default=[], description="...")
    residence: list[str] = Field(default=[], description="...")
    noteableWork: list[str] = Field(default=[], description="...")
    memberOf: list[str] = Field(default=[], description="...")
    describedAtURL: list[str] = Field(default=[], description="...")
    movement: list[str] = Field(default=[], description="...")
    influencedBy: list[str] = Field(default=[], description="...")
    timePeriod: list[str] = Field(default=[], description="...")
    describedBySource: list[str] = Field(default=[], description="...")


class WikidataCorporate(BaseModel):

    # may use e.g. alias="P31"
    baseInfo: Wikidata_BaseInfo = Field(description="Shared fields: instanceOf, image")
    industry: list[str] = Field(default=[], description="...")
    inception: list[str] = Field(default=[], description="...")
    nativeLabel: list[str] = Field(default=[], description="...")
    affiliation: list[str] = Field(default=[], description="...")
    officialName: list[str] = Field(default=[], description="...")
    fieldOfWork: list[str] = Field(default=[], description="...")
    founder: list[str] = Field(default=[], description="...")
    country: list[str] = Field(default=[], description="...")
    location: list[str] = Field(default=[], description="...")
    legalForm: list[str] = Field(default=[], description="...")
    officialWebsite: list[str] = Field(default=[], description="...")


class WikidataConferenceEvent(BaseModel):

    baseInfo: Wikidata_BaseInfo = Field(description="Shared fields: instanceOf, image")
    title: list[str] = Field(default=[], description="...")
    shortName: list[str] = Field(default=[], description="...")
    country: list[str] = Field(default=[], description="...")
    location: list[str] = Field(default=[], description="...")
    partOfTheSeries: list[str] = Field(default=[], description="...")
    hasParts: list[str] = Field(default=[], description="...")
    mainSubject: list[str] = Field(default=[], description="...")
    languageUsed: list[str] = Field(default=[], description="...")
    startTime: list[str] = Field(default=[], description="...")
    endTime: list[str] = Field(default=[], description="...")
    organizer: list[str] = Field(default=[], description="...")
    officialWebsite: list[str] = Field(default=[], description="...")


class DataWikidata(BaseModel):

    wikidataId: str = Field(description="Wikidata ID to use for enrichment")
    otherIds: list[str] = Field(default=[], description="Other IDs to try with SPARQL: orcid, viaf, ...")
    wikidataIdType: Literal["person", "corporate", "conferenceOrEvent"] = Field(description="Type derived from Marc21 fields")
    wikidataInformation: WikidataPerson | WikidataCorporate | WikidataConferenceEvent = Field(description="Use SPARQL with wikidata endpoint: ... ")

