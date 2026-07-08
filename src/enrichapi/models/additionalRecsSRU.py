from typing import Literal, Union, Annotated
from pydantic import BaseModel, Field, Discriminator

from .models_BasicMarc21MD import Marc21MdClassificationNumber

class AdditionalRec(BaseModel):

    ac: str = Field(description="AC identifier of additional record")
    callNumbers: list[str] = Field(default=[], description="Call number identifiers of additional record")
    barcodes: list[str] = Field(default=[], description="Barcode identifiers of additional record")
    isbns: list[str] = Field(default=[], description="ISBN identifiers of additional record")
    issns: list[str] = Field(default=[], description="ISSN identifiers of additional record")


class AdditionalRecsByAuthor(BaseModel):

    searchType: Literal["author"] = "author"
    name: str = Field(description="Author name to search via SRU")
    maxRecs: int | None = Field(default=None, description="Maximum number of additional records")
    additionalRecs: list[AdditionalRec] = Field(default=[], description="Additional records")


class AdditionalRecsBySubjectHeadings(BaseModel):

    searchType: Literal["subjectHeadings"] = "subjectHeadings"
    subjectHeadings: list[str] = Field(description="Subject headings to search via SRU")
    maxRecs: int | None = Field(default=None, description="Maximum number of additional records")
    additionalRecs: list[AdditionalRec] = Field(default=[], description="Additional records")


class AdditionalRecsByClassification(BaseModel):

    searchType: Literal["classification"] = "classification"
    classifications: list[Marc21MdClassificationNumber] = Field(description="Classifications to search via SRU")
    maxRecs: int | None = Field(default=None, description="Maximum number of additional records")
    additionalRecs: list[AdditionalRec] = Field(default=[], description="Additional records")



class AdditionalRecsSRU(BaseModel):

    records: list[
        Annotated[
            Union[
                AdditionalRecsByAuthor, 
                AdditionalRecsBySubjectHeadings, 
                AdditionalRecsByClassification
            ],
            Discriminator("searchType")
        ]
    ] = Field(default=[],
              description="Data from defined avenues to fetch additional records"
        )

