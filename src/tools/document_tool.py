"""Controlled Document Retrieval Tool for accessing internal knowledge base documents."""

from pathlib import Path
from typing import List, Optional
from src.config.settings import PROJECT_ROOT
from src.tools.base import BaseTool
from src.tools.schemas import (
    DocumentRetrievalInput,
    DocumentRetrievalResult,
    DocumentMetadata,
    DocumentMatch,
)


def extract_document_title(file_path: Path) -> str:
    """Extract first top-level header (# Title) or fallback to filename."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("# "):
                    return stripped[2:].strip()
    except Exception:
        pass
    return file_path.name


class DocumentRetrievalTool(BaseTool):
    """Controlled tool for listing, retrieving, and searching internal documents."""

    name: str = "document_retrieval"
    description: str = (
        "Retrieves and searches internal enterprise documentation, incident postmortems, "
        "and policy runbooks from the configured knowledge base repository."
    )
    input_model = DocumentRetrievalInput
    output_model = DocumentRetrievalResult

    def __init__(self, doc_dir: Optional[Path] = None):
        self.doc_dir = (doc_dir or (PROJECT_ROOT / "data" / "raw")).resolve()

    def _validate_safe_path(self, document_id: str) -> Path:
        """Ensure document_id does not escape the configured document directory."""
        if not document_id or not document_id.strip():
            raise ValueError("document_id cannot be empty.")

        # Reject path separators and traversal patterns directly
        if "/" in document_id or "\\" in document_id or ".." in document_id or "\0" in document_id:
            raise PermissionError(f"Path traversal detected in document identifier: '{document_id}'")

        candidate_path = self.doc_dir / document_id
        if candidate_path.is_symlink():
            raise PermissionError(f"Symlink document identifiers are not allowed: '{document_id}'")

        resolved_target = candidate_path.resolve()

        # Verify that resolved path is inside doc_dir
        try:
            resolved_target.relative_to(self.doc_dir)
        except ValueError:
            raise PermissionError(f"Target document '{document_id}' is outside allowed document directory.")

        if not resolved_target.exists() or not resolved_target.is_file():
            raise FileNotFoundError(f"Document '{document_id}' not found in knowledge base.")

        return resolved_target

    def _run(self, validated_input: DocumentRetrievalInput) -> DocumentRetrievalResult:
        """Execute the requested document retrieval action."""
        if not self.doc_dir.exists():
            return DocumentRetrievalResult(
                success=False,
                action=validated_input.action,
                error=f"Document repository directory does not exist: {self.doc_dir}",
            )

        # Action: List documents
        if validated_input.action == "list":
            return self._handle_list()

        # Action: Get specific document
        elif validated_input.action == "get":
            return self._handle_get(validated_input.document_id)

        # Action: Search documents
        elif validated_input.action == "search":
            return self._handle_search(validated_input.query, validated_input.max_results)

        return DocumentRetrievalResult(
            success=False,
            action=validated_input.action,
            error=f"Unknown action: '{validated_input.action}'",
        )

    def _safe_document_files(self) -> List[Path]:
        """Return direct, regular document files whose resolved paths stay in doc_dir."""
        safe_files: List[Path] = []
        for doc_file in sorted(self.doc_dir.iterdir()):
            if doc_file.is_symlink() or not doc_file.is_file():
                continue
            try:
                resolved_file = doc_file.resolve(strict=True)
                resolved_file.relative_to(self.doc_dir)
            except (FileNotFoundError, ValueError):
                continue
            if resolved_file.suffix.lower() in (".md", ".txt", ".json"):
                safe_files.append(resolved_file)
        return safe_files

    def _handle_list(self) -> DocumentRetrievalResult:
        """List all available documents in the knowledge base directory."""
        try:
            doc_files = self._safe_document_files()
            doc_metas: List[DocumentMetadata] = []
            for doc_file in doc_files:
                doc_metas.append(
                    DocumentMetadata(
                        document_id=doc_file.name,
                        title=extract_document_title(doc_file),
                        size_bytes=doc_file.stat().st_size,
                        relative_path=str(doc_file.relative_to(self.doc_dir.parent.parent)),
                    )
                )

            return DocumentRetrievalResult(
                success=True,
                action="list",
                documents=doc_metas,
                error=None,
            )
        except Exception as ex:
            return DocumentRetrievalResult(
                success=False,
                action="list",
                error=f"Error listing documents: {str(ex)}",
            )

    def _handle_get(self, document_id: Optional[str]) -> DocumentRetrievalResult:
        """Retrieve full text of a specific document."""
        if not document_id:
            return DocumentRetrievalResult(
                success=False,
                action="get",
                error="Action 'get' requires 'document_id' parameter.",
            )

        try:
            target_path = self._validate_safe_path(document_id)
            with open(target_path, "r", encoding="utf-8") as f:
                content = f.read()

            return DocumentRetrievalResult(
                success=True,
                action="get",
                content=content,
                error=None,
            )
        except (ValueError, PermissionError, FileNotFoundError) as safe_err:
            return DocumentRetrievalResult(
                success=False,
                action="get",
                error=str(safe_err),
            )
        except Exception as ex:
            return DocumentRetrievalResult(
                success=False,
                action="get",
                error=f"Error reading document: {str(ex)}",
            )

    def _handle_search(self, query: Optional[str], max_results: int) -> DocumentRetrievalResult:
        """Search documents for query keywords and return matching excerpts."""
        if not query or not query.strip():
            return DocumentRetrievalResult(
                success=False,
                action="search",
                error="Action 'search' requires non-empty 'query' parameter.",
            )

        normalized_query = query.strip().lower()
        matches: List[DocumentMatch] = []

        try:
            doc_files = self._safe_document_files()

            for doc_file in doc_files:
                with open(doc_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                for idx, line in enumerate(lines):
                    if normalized_query in line.lower():
                        prev_line = lines[idx - 1].strip() if idx > 0 else None
                        next_line = lines[idx + 1].strip() if idx + 1 < len(lines) else None

                        matches.append(
                            DocumentMatch(
                                document_id=doc_file.name,
                                line_number=idx + 1,
                                excerpt=line.strip(),
                                context_before=prev_line,
                                context_after=next_line,
                            )
                        )

                        if len(matches) >= max_results:
                            break

                if len(matches) >= max_results:
                    break

            return DocumentRetrievalResult(
                success=True,
                action="search",
                matches=matches,
                total_matches=len(matches),
                error=None,
            )
        except Exception as ex:
            return DocumentRetrievalResult(
                success=False,
                action="search",
                error=f"Error performing document search: {str(ex)}",
            )
