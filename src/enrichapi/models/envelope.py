from typing import Generic, TypeVar, Literal
from pydantic import BaseModel, Field

# generic type variable to represent arbitrary payload model
# eg DataLobidGND or DataWikidata]
T = TypeVar("T")

class EnrichmentEnvelope(BaseModel, Generic[T]):
    """
    Generic wrapper / envelope for optional enrichment services.
    Provides standardized status reporting, diagnostics, and graceful partial 
    failure handling without crashing the primary library record lookup.
    """

    status: Literal["success", "not_found", "error", "skipped"] = Field(
        description="Execution status of the external enrichment API call"
    )
    message: str | None = Field(
        default=None, 
        description="Human-readable context, error reason, or success note"
    )
    data: T | None = Field(
        default=None, 
        description="Actual payload data if successful"
    )