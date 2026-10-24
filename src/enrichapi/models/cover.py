from typing import Literal
from pydantic import BaseModel, Field, model_validator


class BookCoverData(BaseModel):
    isbn: str | None = Field(default=None, description="ISBN identifier used to fetch the cover image")
    imageSize: Literal["S", "M", "L"] = Field(default="M", description="Size variant of the cover image")
    coverURL: str | None = Field(default=None, description="Direct URL to the retrieved cover image")
    source: Literal["dnb", "google_books", "open_library", "other"] = Field(
        default="dnb", 
        description="The external service that successfully provided the cover image"
    )

    @model_validator(mode="after")
    def computeCoverUrl(self) -> "BookCoverData":
        if self.isbn and self.source == "open_library" and not self.coverURL:
            cleanIsbn = self.isbn.replace("-", "").replace(" ", "")
            self.coverURL = f"https://covers.openlibrary.org/b/isbn/{cleanIsbn}-{self.imageSize}.jpg?default=false"
        return self