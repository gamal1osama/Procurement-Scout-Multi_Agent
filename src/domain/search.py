"""Domain models and schemas for search queries and search engine results."""

from typing import List
from pydantic import BaseModel, Field, ConfigDict


class SuggestedSearchQueries(BaseModel):
    """Schema representing generated search engine queries."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    queries: List[str] = Field(
        ...,
        description="Suggested search queries to be passed to the search engine.",
        min_length=1,
    )


class SingleSearchResult(BaseModel):
    """Schema representing a single product search result from the search engine."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    title: str = Field(..., description="The title of the search result page.")
    url: str = Field(..., description="The URL of the individual product page.")
    content: str = Field(..., description="Snippet or content extracted by the search engine.")
    score: float = Field(..., description="Relevance / confidence score from the search provider.")
    search_query: str = Field(..., description="The search query that produced this result.")


class AllSearchResults(BaseModel):
    """Schema aggregating all filtered single-product search results."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    results: List[SingleSearchResult] = Field(
        default_factory=list,
        description="List of single-product search results.",
    )
