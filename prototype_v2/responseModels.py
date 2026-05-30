from typing import Annotated, List, Literal, Union
from pydantic import BaseModel, Field


#############################
# Metadata                  #
# baseFetchONB              #
#############################

class BasicBibMetadata(BaseModel):

    title245: str | None = Field(default=None, description="Title (245 a/b)")
    author100: str | None = Field(default=None, description="Author (100 a)")
    gndID: str | None = Field(default=None, description="GND-ID (100 0)")
    titlesGND: List[str] = Field(default=[], description="Works from lobid")

# could add other metadata to get here


#############################      
# InstitutionResponse       #
#############################

class OeNBResponse(BaseModel):

    iName: Literal["oenb"] = "oenb"
    barcode: str
    metadata: BasicBibMetadata

# could add other libraries here


#############################
# LibraryResponse           #
#############################

LibraryResponseUnion = Annotated[
    Union[OeNBResponse], 
    Field(discriminator="iName")
]

class LibraryResponse(BaseModel):
    iType: Literal["bib"] = "bib"
    result: LibraryResponseUnion

# could add other institution types here


#############################
# EnrichmentResponse        #
#############################

# this is what API actually returns
EnrichmentResponse = Annotated[
    Union[LibraryResponse],
    Field(discriminator="iType")
]