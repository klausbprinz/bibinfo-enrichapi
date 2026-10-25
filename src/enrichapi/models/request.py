from typing import Union, Literal, Annotated
from pydantic import BaseModel, Field

class OeNBRequestData(BaseModel):
    iName: Literal["oenb"] = "oenb"
    
    # main identifier
    identifier: str | None = Field(
        default=None, description="The primary search term (Barcode or Bib-ID/AC-Number)",
        examples=["AC14474940", "+Z168276302"]
    )
    
    # updated: added "bibId" as the new generic standard, kept "ac" for backward compatibility
    # updated: added "isbn" to the allowed identifier types
    identifierType: Literal["barcode", "bibId", "ac", "isbn"] | None = Field(
        default=None, 
        description="Explicitly state what type the identifier is",
        examples=["bibId", "barcode", "isbn"]
    )
    
    # optional direct bypass identifiers (if user already has them)
    gndId: str | None = Field(
        default=None, 
        description="Direct GND ID bypass if known",
        examples=[None, "2024703-5"]
    )
    wikidataId: str | None = Field(
        default=None, 
        description="Direct Wikidata ID bypass if known",
        examples=[None, "Q76518"]
    )
    isbn: str | None = Field(
        default=None, 
        description="Direct ISBN ID bypass if known",
        examples=[None, "9781473224469"]
    )
    
    # core features
    fetchMarc21MD: bool = Field(default=True, description="Fetch core MARC21 record via SRU")
    fetchLobidGND: bool = Field(default=True, description="Enrich via Lobid GND API")
    fetchWikidata: bool = Field(default=True, description="Enrich via Wikidata SPARQL")
    fetchCover: bool = Field(default=False, description="Fetch Book Cover via multi-tier waterfall")
    fetchDescription: bool = Field(default=False, description="Fetch Book Description / Abstract")

    # granular sru similar recs features
    fetchSimilarByAuthor: bool = Field(default=False, description="Fetch subsidiary records by the author's name")
    fetchSimilarBySubject: bool = Field(default=False, description="Fetch subsidiary records by subject headings")
    fetchSimilarByClassification: bool = Field(default=False, description="Fetch subsidiary records by classification numbers")

    # limit control
    maxRecs: int = Field(default=5, ge=1, le=50, description="Maximum number of additional records to return per strategy")


class GBVRequestData(BaseModel):
    iName: Literal["gbv"] = "gbv"
    
    # main identifier
    identifier: str | None = Field(
        default=None, description="The primary search term (Barcode, PPN / Bib-ID, or ISBN)",
        examples=["123456789X", "9783161484100"]
    )
    identifierType: Literal["barcode", "bibId", "isbn"] | None = Field(
        default=None, 
        description="Explicitly state what type the identifier is (bibId maps to PPN for K10plus)",
        examples=["bibId", "barcode", "isbn"]
    )
    
    # optional direct bypass identifiers
    gndId: str | None = Field(default=None, description="Direct GND ID bypass if known")
    wikidataId: str | None = Field(default=None, description="Direct Wikidata ID bypass if known")
    isbn: str | None = Field(default=None, description="Direct ISBN ID bypass if known")
    
    # core features
    fetchMarc21MD: bool = Field(default=True, description="Fetch core MARC21 record via SRU")
    fetchLobidGND: bool = Field(default=True, description="Enrich via Lobid GND API")
    fetchWikidata: bool = Field(default=True, description="Enrich via Wikidata SPARQL")
    fetchCover: bool = Field(default=False, description="Fetch Book Cover via multi-tier waterfall")
    fetchDescription: bool = Field(default=False, description="Fetch Book Description / Abstract")

    # granular sru similar recs features
    fetchSimilarByAuthor: bool = Field(default=False, description="Fetch subsidiary records by the author's name")
    fetchSimilarBySubject: bool = Field(default=False, description="Fetch subsidiary records by subject headings")
    fetchSimilarByClassification: bool = Field(default=False, description="Fetch subsidiary records by classification numbers")

    # limit control
    maxRecs: int = Field(default=5, ge=1, le=50, description="Maximum number of additional records to return per strategy")


LibraryInstitution = Annotated[
    Union[OeNBRequestData, GBVRequestData], 
    Field(discriminator="iName")
]

class LibraryCategory(BaseModel):
    iType: Literal["bib"] = "bib"
    institution: LibraryInstitution

EnrichmentRequest = Annotated[
    Union[LibraryCategory], 
    Field(discriminator="iType")
]