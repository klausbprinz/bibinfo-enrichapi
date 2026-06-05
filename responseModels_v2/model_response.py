from .models_BasicMarc21MD import BasicMarc21MD
from .models_AdditionalRecsSRU import AdditionalRecsSRU
from .models_LobidGND import DataLobidGND
from .models_Wikidata import DataWikidata

from .models_otherAPIs import BookCoverOpenLibrary
from .models_otherAPIs import DescriptionGoogleBooks

from typing import Literal
from pydantic import BaseModel, Field


class OenbResponse(BaseModel):

    iName: Literal["oenb"] = "oenb"
    identifier: str = Field(description="Mandatory identifier")
    identifierType: Literal["barcode", "ac"] = Field(description="Identifier: barcode or ac")
    basicMarc21MD: BasicMarc21MD = Field(description="Basic Marc21 metadata")
    additionalRecsSRU: AdditionalRecsSRU | None = Field(default=None, description="Similar Records")
    gndInfoLobid: DataLobidGND | None = Field(default=None, description="Data fetched via LobidAPI")
    wikidataData: DataWikidata | None = Field(default=None, description="Data fetched via Wikidata")
    bookCover: BookCoverOpenLibrary | None = Field(default=None, description="Book cover fetched via Open Library")
    bookDescription: DescriptionGoogleBooks | None = Field(default=None, description="Description fetched via GoogleBooks")


class Response(BaseModel):

    response: OenbResponse