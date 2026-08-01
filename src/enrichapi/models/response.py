from typing import Literal, Union, Annotated, Any
from pydantic import BaseModel, Field, Discriminator, Tag

from .basicMarc21MD import BasicMarc21MD
from .additionalRecsSRU import AdditionalRecsSRU
from .lobidGND import DataLobidGND
from .wikidata import DataWikidata
from .otherAPIs import BookCoverOpenLibrary, DescriptionGoogleBooks


# =====================================================================
# LEVEL 1: Institutional Schemas
# =====================================================================

class BaseInstitutionResponse(BaseModel):
    """Common fields shared by any bibliographic source."""

    identifier: str | None = Field(
        default=None, description="System identifier (e.g., Barcode or Bib Identifier)"
    )
    basicMarc21MD: BasicMarc21MD | None = Field(default=None, description="Basic Marc21 metadata")
    additionalRecsSRU: AdditionalRecsSRU | None = Field(default=None, description="Similar Records via SRU")
    gndInfoLobid: DataLobidGND | None = Field(default=None, description="Data fetched via Lobid GND API")
    wikidataData: DataWikidata | None = Field(default=None, description="Data fetched via Wikidata SPARQL")
    bookCover: BookCoverOpenLibrary | None = Field(default=None, description="Book cover fetched via Open Library")
    bookDescription: DescriptionGoogleBooks | None = Field(default=None, description="Description fetched via GoogleBooks")


class OenbResponse(BaseInstitutionResponse):
    """The explicit footprint for the Austrian National Library."""

    iName: Literal["oenb"] = "oenb"
    identifierType: Literal["barcode", "ac"] | None = Field(
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