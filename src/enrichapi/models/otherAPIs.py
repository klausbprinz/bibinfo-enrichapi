from typing import Literal
from pydantic import BaseModel, Field, model_validator

# Use https://covers.openlibrary.org/b/isbn/<ISBN>-M.jpg?default=false -> if no image: 404
class BookCoverOpenLibrary(BaseModel):

    imageSize: Literal["S", "M", "L"] = Field(default="M", description="Size of cover image to retrieve via URL")
    isbn: str | None = Field(default=None, description="ISBN identifier to fetch cover image for")
    coverURL: str | None = Field(default=None, description="Computed Open Library covers endpoint URL")

    @model_validator(mode="after")

    def computeCoverUrl(self) -> "BookCoverOpenLibrary":        # string literal type hint/forward reference     
        # if isbn is provided but coverURL hasn't been set yet, calculate it dynamically
        if self.isbn and not self.coverURL:
            
            # clean up hyphens or spaces if any exist in raw isbn strings
            cleanIsbn = self.isbn.replace("-", "").replace(" ", "")
            self.coverURL = f"https://covers.openlibrary.org/b/isbn/{cleanIsbn}-{self.imageSize}.jpg?default=false"
        
        return self


class DescriptionGoogleBooks(BaseModel):

    description: str | None = Field(
        default=None, 
        description="""https://www.googleapis.com/books/v1/volumes?q=isbn:<ISBN> , may need an API key at some point,
                    ca. 100 calls per day for free, get info at items elem, list[0], volumeInfoElem, description text node
                    could also try to use OpenLibrary: access via ISBN, the get work Id then access via work ID,
                    look for description elem, value text node
                    """              
    )

