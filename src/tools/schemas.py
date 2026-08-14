"""Pydantic schemas for controlled tool inputs, outputs, and metadata."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


# --- Tool Metadata ---
class ToolParameterSchema(BaseModel):
    """Metadata describing a single tool parameter."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None


class ToolMetadata(BaseModel):
    """Metadata describing a registered tool."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]


# --- SQL Investigation Tool Schemas ---
class SQLQueryInput(BaseModel):
    """Input payload for SQL investigation tool."""
    model_config = ConfigDict(extra="forbid")

    query: str = Field(
        ...,
        description="Read-only SELECT or WITH SQL query string (max 5000 chars)",
        max_length=5000,
    )
    params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Dictionary of bound query parameters (max 50 items)",
    )
    max_rows: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of rows to return (default 100, max 1000)",
    )


class SQLQueryResult(BaseModel):
    """Structured result returned by SQL investigation tool."""
    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(..., description="Whether query execution succeeded")
    columns: List[str] = Field(default_factory=list, description="Ordered list of column names")
    rows: List[Dict[str, Any]] = Field(default_factory=list, description="List of row dictionaries")
    row_count: int = Field(0, description="Number of rows returned in this result")
    truncated: bool = Field(False, description="True if results were capped by max_rows limit")
    error: Optional[str] = Field(None, description="Error message if execution failed")


# --- Document Retrieval Tool Schemas ---
class DocumentRetrievalInput(BaseModel):
    """Input payload for Document Retrieval tool."""
    model_config = ConfigDict(extra="forbid")

    action: Literal["list", "get", "search"] = Field(
        ...,
        description="Retrieval action: 'list' (list documents), 'get' (read document), or 'search' (keyword search)",
    )
    document_id: Optional[str] = Field(
        None,
        description="Target document filename / identifier (required for 'get' action)",
    )
    query: Optional[str] = Field(
        None,
        description="Search keyword or phrase (required for 'search' action)",
        max_length=200,
    )
    max_results: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of search matches to return (default 10, max 100)",
    )


class DocumentMetadata(BaseModel):
    """Metadata describing a stored knowledge document."""
    document_id: str = Field(..., description="Document identifier / filename")
    title: str = Field(..., description="Document title extracted from header")
    size_bytes: int = Field(..., description="File size in bytes")
    relative_path: str = Field(..., description="Relative path within document repository")


class DocumentMatch(BaseModel):
    """Search match snippet from a document."""
    document_id: str = Field(..., description="Document identifier where match was found")
    line_number: int = Field(..., description="Line number of matching content (1-indexed)")
    excerpt: str = Field(..., description="Matched text line or snippet")
    context_before: Optional[str] = Field(None, description="Preceding line for context")
    context_after: Optional[str] = Field(None, description="Succeeding line for context")


class DocumentRetrievalResult(BaseModel):
    """Structured result returned by Document Retrieval tool."""
    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(..., description="Whether document operation succeeded")
    action: str = Field(..., description="Action performed: list, get, or search")
    documents: List[DocumentMetadata] = Field(
        default_factory=list,
        description="List of documents (populated on 'list' action)",
    )
    content: Optional[str] = Field(
        None,
        description="Full text content of document (populated on 'get' action)",
    )
    matches: List[DocumentMatch] = Field(
        default_factory=list,
        description="Matching excerpts (populated on 'search' action)",
    )
    total_matches: int = Field(0, description="Total count of search matches found")
    error: Optional[str] = Field(None, description="Error message if operation failed")
