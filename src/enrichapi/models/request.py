from typing import Union, Literal, Annotated
from pydantic import BaseModel, Field

class OeNBRequestData(BaseModel):
    iName: Literal["oenb"] = "oenb"
    
    # flexible main identifier (optional for bypass queries)
    identifier: str | None = Field(
        default=None, description="The primary search term (Barcode or AC-Number)"
    )
    identifierType: Literal["barcode", "ac"] | None = Field(
        default=None, description="Explicitly state of what type the identifier is"
    )
    
    # optional direct bypass identifiers (if user already has them)
    gndId: str | None = Field(default=None, description="Direct GND ID bypass if known")
    wikidataId: str | None = Field(default=None, description="Direct Wikidata ID bypass if known")
    isbn: str | None = Field(default=None, description="Direct ISBN ID bypass if known")
    
    # core features
    fetchMarc21MD: bool = Field(default=True, description="Fetch core MARC21 record via SRU")
    fetchSimilarSRU: bool = Field(default=False, description="Fetch similar records via subsidiary SRU queries")
    fetchLobidGND: bool = Field(default=True, description="Enrich via Lobid GND API")
    fetchWikidata: bool = Field(default=True, description="Enrich via Wikidata SPARQL")
    fetchCover: bool = Field(default=True, description="Fetch Open Library Book Cover")
    fetchDescription: bool = Field(default=True, description="Fetch Google Books Description")

    # granula sru similar recs features
    fetchSimilarByAuthor: bool = Field(default=False, description="Fetch subsidiary records by the author's name")
    fetchSimilarBySubject: bool = Field(default=False, description="Fetch subsidiary records by subject headings")
    fetchSimilarByClassification: bool = Field(default=False, description="Fetch subsidiary records by classification numbers")

    # limit control
    maxRecs: int = Field(default=5, ge=1, le=50, description="Maximum number of additional records to return per strategy")

LibraryInstitution = Annotated[
    Union[OeNBRequestData], 
    Field(discriminator="iName")
]

class LibraryCategory(BaseModel):
    iType: Literal["bib"] = "bib"
    institution: LibraryInstitution

EnrichmentRequest = Annotated[
    Union[LibraryCategory], 
    Field(discriminator="iType")
]