from pydantic import BaseModel, Field

class BookDescriptionData(BaseModel):
    isbn: str | None = Field(
        default=None, 
        description="The clean ISBN associated with the description lookup"
    )
    description: str | None = Field(
        default=None, 
        description="The full abstract, description, or summary text of the book"
    )
    source: str = Field(
        description="The provider that successfully supplied the description (e.g., 'google_books', 'open_library', 'wikipedia')"
    )