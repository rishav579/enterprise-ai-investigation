"""EvidenceCollector — converts successful tool outputs into typed EvidenceItems.

The collector is NOT an LLM summarizer.  It faithfully transcribes the
structured outputs of controlled tools into immutable, traceable evidence items.
It never invents, infers, or transforms factual content.

Evidence collection is deterministic and works completely offline.
"""

from typing import Any, Dict, List

from src.investigation.evidence import (
    DocumentListingContent,
    DocumentMatchContent,
    DocumentSearchSummaryContent,
    DocumentTextContent,
    EvidenceItem,
    EvidenceStore,
    EvidenceType,
    SQLEvidenceContent,
    compute_content_hash,
)
from src.investigation.models import InvestigationStepResult, StepStatus
from src.tools.schemas import DocumentRetrievalResult, SQLQueryResult


def _make_evidence_id(sequence_number: int) -> str:
    """Return a zero-padded, stable evidence ID in EVID-NNN format."""
    return f"EVID-{sequence_number:03d}"


class EvidenceCollector:
    """Converts successful InvestigationStepResult tool outputs into EvidenceItems.

    Usage:
        store = EvidenceStore(investigation_run_id=run_id)
        collector = EvidenceCollector(investigation_run_id=run_id, store=store)
        evidence_ids = collector.collect(step_result)
    """

    def __init__(self, investigation_run_id: str, store: EvidenceStore):
        self._run_id = investigation_run_id
        self._store = store

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def collect(self, step_result: InvestigationStepResult) -> List[str]:
        """Convert a completed step result into one or more EvidenceItems.

        Returns the list of evidence IDs collected from this step.
        Only COMPLETED steps produce evidence.  FAILED and BLOCKED steps
        produce nothing (no false evidence fabricated).
        """
        if step_result.status != StepStatus.COMPLETED:
            return []
        if step_result.tool_output is None:
            return []

        tool_name = step_result.tool_name
        tool_output = step_result.tool_output

        if tool_name == "sql_investigation":
            return self._collect_sql_evidence(step_result, tool_output)
        elif tool_name == "document_retrieval":
            return self._collect_document_evidence(step_result, tool_output)
        else:
            # Unknown tool — collect raw evidence with generic typing
            return self._collect_generic_evidence(step_result, tool_output)

    # ------------------------------------------------------------------
    # SQL evidence
    # ------------------------------------------------------------------

    def _collect_sql_evidence(
        self,
        step_result: InvestigationStepResult,
        tool_output: Dict[str, Any],
    ) -> List[str]:
        """Extract one SQL_RESULT evidence item from a successful SQL tool output."""
        query = step_result.tool_input.get("query", "(query not recorded)")
        columns: List[str] = tool_output.get("columns", [])
        rows: List[Dict[str, Any]] = tool_output.get("rows", [])
        row_count: int = tool_output.get("row_count", len(rows))
        truncated: bool = tool_output.get("truncated", False)

        content = SQLEvidenceContent(
            query_reference=query,
            columns=columns,
            rows=rows,
            row_count=row_count,
            truncated=truncated,
        ).model_dump()

        return [
            self._append_item(
                step_result=step_result,
                evidence_type=EvidenceType.SQL_RESULT,
                source_reference=f"sql_investigation:{step_result.step_id}",
                content=content,
                metadata={
                    "max_rows_applied": step_result.tool_input.get("max_rows"),
                    "params": step_result.tool_input.get("params"),
                },
            )
        ]

    # ------------------------------------------------------------------
    # Document evidence
    # ------------------------------------------------------------------

    def _collect_document_evidence(
        self,
        step_result: InvestigationStepResult,
        tool_output: Dict[str, Any],
    ) -> List[str]:
        """Extract evidence from document retrieval tool outputs.

        - 'list' action → DOCUMENT_LISTING (one item)
        - 'get' action  → DOCUMENT_TEXT (one item)
        - 'search' action → DOCUMENT_MATCH (one item per match)
        """
        action: str = tool_output.get("action", "")

        if action == "get":
            return self._collect_document_text(step_result, tool_output)
        elif action == "search":
            return self._collect_document_matches(step_result, tool_output)
        elif action == "list":
            return self._collect_document_listing(step_result, tool_output)
        return []

    def _collect_document_text(
        self,
        step_result: InvestigationStepResult,
        tool_output: Dict[str, Any],
    ) -> List[str]:
        document_id: str = step_result.tool_input.get("document_id", "(unknown)")
        full_text: str = tool_output.get("content", "")

        content = DocumentTextContent(
            document_id=document_id,
            full_text=full_text,
            char_count=len(full_text),
        ).model_dump()

        return [
            self._append_item(
                step_result=step_result,
                evidence_type=EvidenceType.DOCUMENT_TEXT,
                source_reference=f"document_retrieval:{document_id}",
                content=content,
                metadata={"document_id": document_id},
            )
        ]

    def _collect_document_matches(
        self,
        step_result: InvestigationStepResult,
        tool_output: Dict[str, Any],
    ) -> List[str]:
        """Collect evidence from a document search action.

        Always emits one DOCUMENT_SEARCH_SUMMARY item (even on zero matches).
        Additionally emits one DOCUMENT_MATCH item per individual match found.
        This guarantees every completed search step produces at least one evidence item,
        making the search auditable regardless of outcome.
        """
        matches: List[Dict[str, Any]] = tool_output.get("matches", [])
        total_matches: int = tool_output.get("total_matches", len(matches))
        query_used: str = step_result.tool_input.get("query", "")
        collected_ids: List[str] = []

        # 1. Always emit a search summary evidence item
        matched_doc_ids = list({m.get("document_id", "") for m in matches if m.get("document_id")})
        summary_content = DocumentSearchSummaryContent(
            search_query=query_used,
            total_matches=total_matches,
            matched_documents=matched_doc_ids,
        ).model_dump()

        summary_id = self._append_item(
            step_result=step_result,
            evidence_type=EvidenceType.DOCUMENT_SEARCH_SUMMARY,
            source_reference=f"document_retrieval:search:{step_result.step_id}",
            content=summary_content,
            metadata={"search_query": query_used, "total_matches": total_matches},
        )
        collected_ids.append(summary_id)

        # 2. Emit one DOCUMENT_MATCH item per individual match
        for match in matches:
            document_id: str = match.get("document_id", "(unknown)")
            content = DocumentMatchContent(
                document_id=document_id,
                line_number=match.get("line_number", 0),
                excerpt=match.get("excerpt", ""),
                context_before=match.get("context_before"),
                context_after=match.get("context_after"),
            ).model_dump()

            evidence_id = self._append_item(
                step_result=step_result,
                evidence_type=EvidenceType.DOCUMENT_MATCH,
                source_reference=f"document_retrieval:{document_id}:L{match.get('line_number', 0)}",
                content=content,
                metadata={"search_query": query_used, "document_id": document_id},
            )
            collected_ids.append(evidence_id)

        return collected_ids

    def _collect_document_listing(
        self,
        step_result: InvestigationStepResult,
        tool_output: Dict[str, Any],
    ) -> List[str]:
        documents: List[Dict[str, Any]] = [
            {
                "document_id": doc.get("document_id", ""),
                "title": doc.get("title", ""),
                "size_bytes": doc.get("size_bytes", 0),
            }
            for doc in tool_output.get("documents", [])
        ]
        content = DocumentListingContent(
            documents=documents,
            document_count=len(documents),
        ).model_dump()

        return [
            self._append_item(
                step_result=step_result,
                evidence_type=EvidenceType.DOCUMENT_LISTING,
                source_reference="document_retrieval:listing",
                content=content,
                metadata={},
            )
        ]

    # ------------------------------------------------------------------
    # Generic fallback
    # ------------------------------------------------------------------

    def _collect_generic_evidence(
        self,
        step_result: InvestigationStepResult,
        tool_output: Dict[str, Any],
    ) -> List[str]:
        """Collect a single METRIC evidence item for unknown tool outputs."""
        content = {k: v for k, v in tool_output.items() if k != "success"}

        return [
            self._append_item(
                step_result=step_result,
                evidence_type=EvidenceType.METRIC,
                source_reference=f"{step_result.tool_name}:{step_result.step_id}",
                content=content,
                metadata={},
            )
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _append_item(
        self,
        *,
        step_result: InvestigationStepResult,
        evidence_type: EvidenceType,
        source_reference: str,
        content: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> str:
        """Create an EvidenceItem, compute its hash, append it to the store, and return its ID."""
        sequence_number = self._store.total_count + 1
        evidence_id = _make_evidence_id(sequence_number)

        item = EvidenceItem(
            evidence_id=evidence_id,
            investigation_run_id=self._run_id,
            step_id=step_result.step_id,
            tool_name=step_result.tool_name,
            evidence_type=evidence_type,
            source_reference=source_reference,
            content=content,
            content_hash=compute_content_hash(content),
            sequence_number=sequence_number,
            metadata=metadata,
        )
        self._store.append(item)
        return evidence_id
