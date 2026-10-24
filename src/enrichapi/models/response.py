from typing import Literal, Union, Annotated, Any
from pydantic import BaseModel, Field, Discriminator, Tag

from .envelope import EnrichmentEnvelope
from .basicMarc21MD import BasicMarc21MD
from .additionalRecsSRU import AdditionalRecsSRU
from .lobidGND import DataLobidGND
from .wikidata import DataWikidata
from .cover import BookCoverData
from .otherAPIs import BookCoverOpenLibrary, DescriptionGoogleBooks

# =====================================================================
# SPECIAL SCHEMAS: Ambiguity Contract for ISBN (HTTP 300)
# =====================================================================

class IsbnCandidate(BaseModel):
    """Represents a single edition option when an ISBN match is ambiguous."""
    bibId: str | None = Field(default=None, description="System record identifier (bibId)")
    title: str | None = Field(default=None, description="Title of this specific edition")
    author: str | None = Field(default=None, description="Main author or creator")
    publishers: list[str] = Field(default_factory=list, description="Publishers details")
    dates: list[str] = Field(default_factory=list, description="Publication dates")


class IsbnAmbiguityResponse(BaseModel):
    """Returned on HTTP 300 when an ISBN matches multiple editions."""
    status: Literal["ambiguous_isbn"] = "ambiguous_isbn"
    isbn: str = Field(description="The ISBN that triggered the ambiguity")
    totalMatches: int = Field(description="Total number of matching records found")
    candidates: list[IsbnCandidate] = Field(description="List of matching catalog candidates")

# =====================================================================
# LEVEL 1: Institutional Schemas
# =====================================================================

class BaseInstitutionResponse(BaseModel):
    """Common fields shared by any bibliographic source."""

    identifier: str | None = Field(
        default=None, description="System identifier (e.g., Barcode or Bib Identifier)"
    )

    # new: diagnostics field for tracking data anomalies, warnings, or collisions
    diagnostics: list[str] | None = Field(
        default=None, description="Execution warnings, data anomalies, or collision notes"
    )

    basicMarc21MD: BasicMarc21MD | None = Field(default=None, description="Basic Marc21 metadata")
    additionalRecsSRU: AdditionalRecsSRU | None = Field(default=None, description="Similar Records via SRU")

    # wrap auxiliary enrichment services in the generic status envelope
    gndInfoLobid: EnrichmentEnvelope[DataLobidGND] | None = Field(
        default=None, description="Data fetched via Lobid GND API with execution diagnostics"
    )
    wikidataData: EnrichmentEnvelope[DataWikidata] | None = Field(
        default=None, description="Data fetched via Wikidata SPARQL with execution diagnostics"
    )
    bookCover: EnrichmentEnvelope[BookCoverData] | None = Field(
        default=None, description="Book cover fetched via waterfall providers with execution diagnostics"
    )
    bookDescription: EnrichmentEnvelope[DescriptionGoogleBooks] | None = Field(
        default=None, description="Description fetched via GoogleBooks with execution diagnostics"
    )

class OenbResponse(BaseInstitutionResponse):
    """The explicit footprint for the Austrian National Library."""

    iName: Literal["oenb"] = "oenb"

    # updated: added "isbn" here
    identifierType: Literal["barcode", "bibId", "ac", "isbn"] | None = Field(
        default=None, description="Type of input identifier used"
    )


# future proofing: adding another library network should be trivial
class DnbResponse(BaseInstitutionResponse):
    """The explicit footprint for the German National Library."""

    iName: Literal["dnb"] = "dnb"


def resolveInstitutionType(v: Any) -> str:
    
    if isinstance(v, dict):
        return v.get("iName", "oenb")
    
    return "oenb"


# =====================================================================
# LEVEL 2: Category Wrappers
# =====================================================================

class BibliographicLibraryResponse(BaseModel):
    """Wraps traditional book-based library networks."""
    
    iType: Literal["bib"] = "bib"
    
    # dynamically decides if it's oenb, dnb, etc.
    result: Annotated[
        Union[
            Annotated[OenbResponse, Tag("oenb")],
            Annotated[DnbResponse, Tag("dnb")]
        ],
        Discriminator(resolveInstitutionType)
    ]


class ArchivalResponse(BaseModel):
    """Future proofing: wraps archive-based networks."""
    
    iType: Literal["archive"] = "archive"
    result: dict[str, Any] = Field(description="Placeholder for archival metadata structure")


# =====================================================================
# LEVEL 3: Core API Root
# =====================================================================

def resolveCategoryType(v: Any) -> str:
    
    if isinstance(v, dict):
        return v.get("iType", "bib")
    
    return "bib"


class RootApiResponse(BaseModel):
    """
    The master response returned by API.
    """
    response: Annotated[
        Union[
            Annotated[BibliographicLibraryResponse, Tag("bib")],
            Annotated[ArchivalResponse, Tag("archive")]
        ],
        Discriminator(resolveCategoryType)
    ]