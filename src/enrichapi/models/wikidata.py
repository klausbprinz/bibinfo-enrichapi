from typing import Literal, Union, Annotated
from pydantic import BaseModel, Field, Discriminator


class WikidataBaseInfo(BaseModel):

    instanceOf: list[str] = Field(default=[], description="...")
    image: list[str] = Field(default=[], description="...")


class WikidataPerson(WikidataBaseInfo):

    wikidataType: Literal["person"] = "person"
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


class WikidataCorporate(WikidataBaseInfo):

    # may use e.g. alias="P31"
    wikidataType: Literal["corporate"] = "corporate"
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


class WikidataConferenceEvent(WikidataBaseInfo):

    wikidataType: Literal["conferenceOrEvent"] = "conferenceOrEvent"
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
    
    wikidataInformation: Annotated[
        Union[WikidataPerson, WikidataCorporate, WikidataConferenceEvent],
        Discriminator("wikidataType")
    ] = Field(description="Use SPARQL with wikidata endpoint")

