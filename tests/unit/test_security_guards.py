"""Comprehensive security guardrail tests for SQL and Document tools."""

from pathlib import Path
import pytest
from src.tools.sql_tool import SQLInvestigationTool
from src.tools.document_tool import DocumentRetrievalTool
from src.tools.schemas import SQLQueryInput, DocumentRetrievalInput


@pytest.fixture
def mock_db_url(tmp_path):
    db_url = f"sqlite:///{tmp_path}/sec_test.db"
    from src.data.database import init_db
    init_db(db_url)
    return db_url


# --- SQL Security Tests ---

@pytest.mark.parametrize("dangerous_keyword", [
    "DELETE",
    "UPDATE",
    "INSERT",
    "DROP",
    "ALTER",
    "CREATE",
    "ATTACH",
    "DETACH",
    "TRUNCATE",
    "GRANT",
    "REVOKE",
    "PRAGMA",
    "EXEC",
    "EXECUTE",
    "VACUUM",
    "REPLACE",
    "BEGIN",
    "COMMIT",
    "ROLLBACK",
])
def test_sql_tool_rejects_mutation_keywords(mock_db_url, dangerous_keyword):
    """Verify tool rejects statements containing any dangerous mutation keyword."""
    tool = SQLInvestigationTool(db_url=mock_db_url)
    query = f"{dangerous_keyword} FROM customers"
    result = tool.execute({"query": query})

    assert result.success is False
    assert result.error is not None
    assert "Prohibited" in result.error or "Only read-only SELECT" in result.error


@pytest.mark.parametrize("multi_statement", [
    "SELECT * FROM customers; DROP TABLE customers;",
    "SELECT 1; DELETE FROM billing_events WHERE 1=1;",
    "SELECT * FROM subscriptions; SELECT * FROM customers;",
    "SELECT customer_id FROM customers; -- followed by comment\nDELETE FROM customers;",
])
def test_sql_tool_rejects_multi_statements(mock_db_url, multi_statement):
    """Verify tool strictly rejects multiple SQL statements separated by semicolons."""
    tool = SQLInvestigationTool(db_url=mock_db_url)
    result = tool.execute({"query": multi_statement})

    assert result.success is False
    assert "Multiple SQL statements" in result.error or "Prohibited" in result.error


def test_sql_tool_rejects_excessive_query_length(mock_db_url):
    """Verify tool rejects queries exceeding maximum character length."""
    tool = SQLInvestigationTool(db_url=mock_db_url)
    huge_query = "SELECT " + ("a, " * 3000) + "b FROM customers"
    result = tool.execute({"query": huge_query})

    assert result.success is False
    assert "5000 characters" in result.error or "exceeds maximum allowed length" in result.error


def test_sql_tool_rejects_excessive_parameters(mock_db_url):
    """Verify tool rejects requests exceeding parameter count limit."""
    tool = SQLInvestigationTool(db_url=mock_db_url)
    huge_params = {f"p_{i}": i for i in range(55)}
    result = tool.execute({
        "query": "SELECT * FROM customers WHERE customer_id = :p_0",
        "params": huge_params,
    })

    assert result.success is False
    assert "exceed maximum allowed limit" in result.error


def test_sql_tool_parameter_isolation_prevents_injection(mock_db_url):
    """Verify parameterized values are safely treated as data and cannot inject SQL clauses."""
    tool = SQLInvestigationTool(db_url=mock_db_url)
    
    # An injection attempt passed as a parameter value
    injection_param = "' OR '1'='1"
    result = tool.execute({
        "query": "SELECT * FROM customers WHERE customer_id = :cid",
        "params": {"cid": injection_param},
    })
    
    # Tool safely executes with no rows matching the literal string "' OR '1'='1"
    assert result.success is True
    assert len(result.rows) == 0


# --- Document Tool Security Tests ---

@pytest.mark.parametrize("traversal_id", [
    "../secret.txt",
    "../../etc/passwd",
    "..\\..\\windows\\win.ini",
    "subdir/../../app.py",
    "/etc/shadow",
    "C:\\Windows\\System32\\cmd.exe",
    "doc.md\0.txt",
])
def test_document_tool_rejects_path_traversal(tmp_path, traversal_id):
    """Verify DocumentRetrievalTool strictly rejects path traversal and absolute path identifiers."""
    docs_dir = tmp_path / "safe_docs"
    docs_dir.mkdir()
    (docs_dir / "safe.md").write_text("# Safe Doc", encoding="utf-8")

    tool = DocumentRetrievalTool(doc_dir=docs_dir)
    result = tool.execute({
        "action": "get",
        "document_id": traversal_id,
    })

    assert result.success is False
    assert result.error is not None
    assert ("Path traversal" in result.error or 
            "outside allowed" in result.error or 
            "Input validation error" in result.error or
            "not found" in result.error)
