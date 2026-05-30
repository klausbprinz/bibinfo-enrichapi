from typing import Literal
from pydantic import BaseModel, Field


class BookCoverOpenLibrary(BaseModel):

    coverURL: str | None = Field(default=None, description="Use https://covers.openlibrary.org/b/isbn/<ISBN>-M.jpg?default=false -> if no image: 404")


class DescriptionGoogleBooks(BaseModel):

    description: str | None = Field(
        default=None, 
        description="""https://www.googleapis.com/books/v1/volumes?q=isbn:<ISBN> , may need an API key at some point,
                    ca. 100 calls per day for free, get info at items elem, list[0], volumeInfoElem, description text node
                    could also try to use OpenLibrary: access via ISBN, the get work Id then access via work ID,
                    look for description elem, value text node
                    """              
    )