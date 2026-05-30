from typing import Union, Literal, Annotated
from pydantic import BaseModel, Field

#############################
# Library Models            #
#############################

class OeNB(BaseModel):

    iName: Literal["oenb"] = "oenb"
    barcode: str = Field(description="OeNB specific barcode")


LibraryInstitution = Annotated[
    Union[OeNB],                        # expand library here if needed
    Field(discriminator="iName")
]


#################################
# Institution Models            #
#################################

class Library(BaseModel):

    iType: Literal["bib"] = "bib"
    institution: LibraryInstitution


#################################
# Enrichment Model              #
#################################

EnrichmentRequest = Annotated[
    Union[Library],                 # expand type here if needed
    Field(discriminator="iType")
]