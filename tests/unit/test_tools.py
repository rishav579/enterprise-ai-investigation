"""Unit tests for controlled tools and tool registry."""

from pathlib import Path
import pytest
from src.data.seed_database import seed_enterprise_database
from src.tools import (
    SQLInvestigationTool,
    DocumentRetrievalTool,
    ToolRegistry,
    create_default_tool_registry,
    SQLQueryInput,
    DocumentRetrievalInput,
)


@pytest.fixture
def seeded_db(tmp_path):
    """Fixture providing a seeded test database."""
    db_file = tmp_path / "tools_test.db"
    db_url = f"sqlite:///{db_file}"
    seed_enterprise_database(db_url=db_url, seed=42)
    return db_url


@pytest.fixture
def doc_dir(tmp_path):
    """Fixture providing a sample document directory."""
    docs = tmp_path / "docs"
    docs.mkdir()
    doc1 = docs / "incident_report.md"
    doc1.write_text("# Incident 101 Report\n\nRoot cause was a database connection timeout.\nResolved by restart.\n", encoding="utf-8")
    doc2 = docs / "policy.txt"
    doc2.write_text("Standard refund policy: refunds allowed within 30 days.\nContact support for exceptions.\n", encoding="utf-8")
    return docs


def test_tool_registry_registration_and_discovery(seeded_db, doc_dir):
    """Verify tools can be registered, listed, and queried in registry."""
    registry = create_default_tool_registry(db_url=seeded_db, doc_dir=doc_dir)

    names = registry.list_tool_names()
    assert "sql_investigation" in names
    assert "document_retrieval" in names

    metadata = registry.list_tools()
    assert len(metadata) == 2
    assert all(m.input_schema for m in metadata)
    assert all(m.output_schema for m in metadata)


def test_tool_registry_unregistered_tool_rejection():
    """Verify registry raises KeyError when invoking unknown tool."""
    registry = ToolRegistry()
    with pytest.raises(KeyError):
        registry.execute("unknown_tool", {})


def test_sql_investigation_tool_select_execution(seeded_db):
    """Verify SQL tool executes SELECT query and returns structured output."""
    tool = SQLInvestigationTool(db_url=seeded_db)
    result = tool.execute({
        "query": "SELECT customer_id, segment, plan FROM customers WHERE plan = :plan LIMIT 5",
        "params": {"plan": "enterprise"},
    })

    assert result.success is True
    assert result.error is None
    assert len(result.rows) == 5
    assert result.columns == ["customer_id", "segment", "plan"]
    assert result.truncated is False


def test_sql_investigation_tool_with_cte_query(seeded_db):
    """Verify SQL tool supports WITH (Common Table Expression) queries."""
    tool = SQLInvestigationTool(db_url=seeded_db)
    query = """
    WITH monthly_churn AS (
        SELECT strftime('%Y-%m', cancellation_date) AS month, COUNT(*) AS churn_count
        FROM subscriptions
        WHERE cancellation_date IS NOT NULL
        GROUP BY month
    )
    SELECT * FROM monthly_churn ORDER BY churn_count DESC LIMIT 3
    """
    result = tool.execute(SQLQueryInput(query=query))
    assert result.success is True
    assert len(result.rows) > 0


def test_sql_investigation_tool_row_limit_truncation(seeded_db):
    """Verify max_rows caps results and sets truncated flag accurately."""
    tool = SQLInvestigationTool(db_url=seeded_db)
    result = tool.execute({
        "query": "SELECT customer_id FROM customers",
        "max_rows": 10,
    })

    assert result.success is True
    assert len(result.rows) == 10
    assert result.row_count == 10
    assert result.truncated is True


def test_document_tool_list_action(doc_dir):
    """Verify DocumentRetrievalTool list action returns files with metadata."""
    tool = DocumentRetrievalTool(doc_dir=doc_dir)
    result = tool.execute({"action": "list"})

    assert result.success is True
    assert result.action == "list"
    assert len(result.documents) == 2
    doc_ids = [d.document_id for d in result.documents]
    assert "incident_report.md" in doc_ids
    assert "policy.txt" in doc_ids


def test_document_tool_get_action(doc_dir):
    """Verify DocumentRetrievalTool get action reads document content."""
    tool = DocumentRetrievalTool(doc_dir=doc_dir)
    result = tool.execute({
        "action": "get",
        "document_id": "incident_report.md",
    })

    assert result.success is True
    assert result.action == "get"
    assert "Root cause was a database connection timeout" in result.content


def test_document_tool_search_action(doc_dir):
    """Verify DocumentRetrievalTool search finds keyword matches with line numbers."""
    tool = DocumentRetrievalTool(doc_dir=doc_dir)
    result = tool.execute({
        "action": "search",
        "query": "refund",
    })

    assert result.success is True
    assert result.total_matches == 1
    match = result.matches[0]
    assert match.document_id == "policy.txt"
    assert "refunds allowed within 30 days" in match.excerpt
    assert match.line_number == 1


def test_document_tool_validation_errors(doc_dir):
    """Verify structured errors when required action parameters are omitted."""
    tool = DocumentRetrievalTool(doc_dir=doc_dir)
    
    # 'get' without document_id
    res_get = tool.execute({"action": "get"})
    assert res_get.success is False
    assert "requires 'document_id'" in res_get.error

    # 'search' without query
    res_search = tool.execute({"action": "search"})
    assert res_search.success is False
    assert "requires non-empty 'query'" in res_search.error
