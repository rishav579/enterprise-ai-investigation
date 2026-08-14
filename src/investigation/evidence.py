"""Evidence domain model for the Enterprise AI Investigation System.

Every piece of evidence produced during an investigation is represented as a
typed, immutable EvidenceItem.  Each item carries:

  - A stable, deterministic evidence ID (EVID-NNN, assigned in collection order).
  - Full provenance: investigation run, step, tool, and source reference.
  - Typed content: structured SQL rows, document text, or search matches.
  - A canonical content hash (SHA-256 via stdlib hashlib) for integrity checks.

Evidence collection is deterministic and does NOT use an LLM.
"""

import hashlib
import json
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Evidence type taxonomy
# ---------------------------------------------------------------------------

class EvidenceType(str, Enum):
    """Controlled vocabulary of evidence source types."""
    SQL_RESULT              = "sql_result"           # rows returned by a read-only SQL query
    DATABASE_RECORD         = "database_record"      # a single record extracted from SQL rows
    DOCUMENT_TEXT           = "document_text"        # full text content of a retrieved document
    DOCUMENT_MATCH          = "document_match"       # keyword-search match excerpt from a document
    DOCUMENT_LISTING        = "document_listing"     # directory listing of available documents
    DOCUMENT_SEARCH_SUMMARY = "document_search_summary"  # search result summary (including zero-match)
    METRIC                  = "metric"               # a computed statistical or aggregate value


# ---------------------------------------------------------------------------
# Typed evidence content schemas
# ---------------------------------------------------------------------------

class SQLEvidenceContent(BaseModel):
    """Structured content for SQL-backed evidence items."""
    model_config = ConfigDict(extra="forbid")

    query_reference: str = Field(
        ...,
        description="The SQL query that produced this evidence (stored for traceability)",
    )
    columns: List[str] = Field(
        default_factory=list,
        description="Ordered column names from the query result",
    )
    rows: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Returned rows (bounded by tool max_rows limit)",
    )
    row_count: int = Field(..., description="Number of rows in this evidence item")
    truncated: bool = Field(
        False,
        description="True if the result set was capped by the max_rows limit",
    )


class DocumentTextContent(BaseModel):
    """Structured content for a full retrieved document."""
    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(..., description="Identifier of the retrieved document")
    full_text: str = Field(..., description="Full text content of the document")
    char_count: int = Field(..., description="Character count of the full text")


class DocumentMatchContent(BaseModel):
    """Structured content for a single keyword search match."""
    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(..., description="Document where the match was found")
    line_number: int = Field(..., description="1-indexed line number of the match")
    excerpt: str = Field(..., description="Matched text line or snippet")
    context_before: Optional[str] = Field(None, description="Preceding line for context")
    context_after: Optional[str] = Field(None, description="Succeeding line for context")


class DocumentListingContent(BaseModel):
    """Structured content for a document directory listing."""
    model_config = ConfigDict(extra="forbid")

    documents: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of document metadata dicts (id, title, size_bytes)",
    )
    document_count: int = Field(..., description="Number of documents listed")


class DocumentSearchSummaryContent(BaseModel):
    """Structured content for a document search result (including zero-match outcomes).

    Recorded whenever a 'search' action is executed, regardless of whether
    matches were found.  This ensures the search is auditable even when the
    query returns no results.
    """
    model_config = ConfigDict(extra="forbid")

    search_query: str = Field(..., description="The keyword query that was searched")
    total_matches: int = Field(..., description="Number of matches returned (may be 0)")
    matched_documents: List[str] = Field(
        default_factory=list,
        description="Unique document IDs where matches were found",
    )


# ---------------------------------------------------------------------------
# EvidenceItem — the core unit
# ---------------------------------------------------------------------------

class EvidenceItem(BaseModel):
    """A single traceable, integrity-checked piece of investigation evidence.

    EvidenceItems are immutable after creation.  The content_hash field is
    computed at instantiation from the canonical JSON serialization of the
    content and must match on verification.
    """
    model_config = ConfigDict(frozen=True)  # immutable after construction

    evidence_id: str = Field(
        ...,
        description="Stable unique identifier assigned in collection order (e.g. EVID-001)",
    )
    investigation_run_id: str = Field(
        ...,
        description="ID of the investigation run that produced this evidence",
    )
    step_id: str = Field(
        ...,
        description="ID of the investigation step that produced this evidence",
    )
    tool_name: str = Field(
        ...,
        description="Name of the registered tool that produced this evidence",
    )
    evidence_type: EvidenceType = Field(
        ...,
        description="Controlled vocabulary evidence type",
    )
    source_reference: str = Field(
        ...,
        description=(
            "Human-readable reference to the evidence source "
            "(e.g. 'sql_investigation:STEP-03', 'document_retrieval:postmortem_inc_2025_002.md')"
        ),
    )
    content: Dict[str, Any] = Field(
        ...,
        description="Typed evidence content serialized to a plain dict (use typed schemas above)",
    )
    content_hash: str = Field(
        ...,
        description=(
            "Deterministic SHA-256 hex digest of the canonical content "
            "(sorted-key JSON serialization with no trailing whitespace)"
        ),
    )
    sequence_number: int = Field(
        ...,
        description="1-based collection order within the investigation run",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional additional metadata (e.g. max_rows applied, search query used)",
    )


# ---------------------------------------------------------------------------
# Content hash helper
# ---------------------------------------------------------------------------

def compute_content_hash(content: Dict[str, Any]) -> str:
    """Return the deterministic SHA-256 hex digest of a canonicalized content dict.

    Canonicalization rules:
      - JSON serialization with sorted keys, no extra whitespace.
      - Strings encoded as UTF-8.

    Properties:
      - same content dict → same hash
      - any mutation to content → different hash
    """
    canonical = json.dumps(content, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# EvidenceStore — ordered, append-only collection
# ---------------------------------------------------------------------------

class EvidenceStore(BaseModel):
    """Ordered, append-only collection of EvidenceItems for one investigation run.

    Items are indexed by evidence_id for O(1) lookup, and stored in insertion
    order via the ordered_ids list.  Existing items cannot be replaced once
    appended.
    """

    investigation_run_id: str = Field(..., description="Parent investigation run identifier")
    _items: Dict[str, EvidenceItem] = {}
    _ordered_ids: List[str] = []

    def model_post_init(self, __context: Any) -> None:
        object.__setattr__(self, "_items", {})
        object.__setattr__(self, "_ordered_ids", [])

    def append(self, item: EvidenceItem) -> None:
        """Append an EvidenceItem.  Raises ValueError if ID already exists."""
        if item.evidence_id in self._items:
            raise ValueError(
                f"EvidenceItem '{item.evidence_id}' already exists in this store. "
                "Evidence items are immutable once recorded."
            )
        self._items[item.evidence_id] = item
        self._ordered_ids.append(item.evidence_id)

    def get(self, evidence_id: str) -> Optional[EvidenceItem]:
        """Retrieve an EvidenceItem by ID, or None if not found."""
        return self._items.get(evidence_id)

    def all(self) -> List[EvidenceItem]:
        """Return all items in insertion order."""
        return [self._items[eid] for eid in self._ordered_ids]

    def for_step(self, step_id: str) -> List[EvidenceItem]:
        """Return all items collected for a specific step, in insertion order."""
        return [item for item in self.all() if item.step_id == step_id]

    def ids_for_step(self, step_id: str) -> List[str]:
        """Return all evidence IDs for a specific step, in insertion order."""
        return [item.evidence_id for item in self.for_step(step_id)]

    @property
    def total_count(self) -> int:
        return len(self._ordered_ids)
