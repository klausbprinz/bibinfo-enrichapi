from typing import Literal, Union, Annotated, Any
from pydantic import BaseModel, Field, Discriminator, Tag

from .basicMarc21MD import Marc21MdClassificationNumber

class AdditionalRec(BaseModel):

    ac: str = Field(description="AC identifier of additional record")
    callNumbers: list[str] = Field(default_factory=list, description="Call number identifiers of additional record")
    barcodes: list[str] = Field(default_factory=list, description="Barcode identifiers of additional record")
    isbns: list[str] = Field(default_factory=list, description="ISBN identifiers of additional record")
    issns: list[str] = Field(default_factory=list, description="ISSN identifiers of additional record")


class AdditionalRecsByAuthor(BaseModel):

    searchType: Literal["author"] = "author"
    name: str = Field(description="Author name to search via SRU")
    maxRecs: int | None = Field(default=None, description="Maximum number of additional records")
    additionalRecs: list[AdditionalRec] = Field(default_factory=list, description="Additional records")


class AdditionalRecsBySubjectHeadings(BaseModel):

    searchType: Literal["subjectHeadings"] = "subjectHeadings"
    subjectHeadings: list[str] = Field(description="Subject headings to search via SRU")
    maxRecs: int | None = Field(default=None, description="Maximum number of additional records")
    additionalRecs: list[AdditionalRec] = Field(default_factory=list, description="Additional records")


class AdditionalRecsByClassification(BaseModel):

    searchType: Literal["classification"] = "classification"
    classifications: list[Marc21MdClassificationNumber] = Field(description="Classifications to search via SRU")
    maxRecs: int | None = Field(default=None, description="Maximum number of additional records")
    additionalRecs: list[AdditionalRec] = Field(default_factory=list, description="Additional records")


# catch-all fallback model for unexpected or newly introduced search strategies
class DefaultAdditionalRecs(BaseModel):
    """
    Safety net. If new search avenue is added upstream, 
    this captures the metadata safely instead of crashing the API parser.
    """
    searchType: str = Field(description="Fallback for unmapped search strategies")
    maxRecs: int | None = Field(default=None)
    additionalRecs: list[AdditionalRec] = Field(default_factory=list)


def resolveSearchType(v: Any) -> str:
    
    if isinstance(v, dict):
        sType = v.get("searchType")
        
        if sType in ("author", "subjectHeadings", "classification"):
            return sType
        
    return "default"


class AdditionalRecsSRU(BaseModel):
    records: list[
        Annotated[
            Union[
                Annotated[AdditionalRecsByAuthor, Tag("author")],
                Annotated[AdditionalRecsBySubjectHeadings, Tag("subjectHeadings")],
                Annotated[AdditionalRecsByClassification, Tag("classification")],
                Annotated[DefaultAdditionalRecs, Tag("default")]
            ],
            Discriminator(resolveSearchType)
        ]
    ] = Field(default_factory=list, description="Data from defined avenues to fetch additional records")
