"""Controlled, read-only SQL Investigation Tool with multi-layered safety guardrails."""

import re
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy import text
from src.data.database import get_engine
from src.tools.base import BaseTool
from src.tools.schemas import SQLQueryInput, SQLQueryResult


# Comprehensive list of forbidden SQL keywords (checked as discrete tokens)
FORBIDDEN_SQL_TOKENS: Set[str] = {
    "INSERT",
    "UPDATE",
    "DELETE",
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
    "LOAD_EXTENSION",
    "INTO",
    "UPSERT",
    "REINDEX",
}

# Regex to strip single-line comments (-- ...) and multi-line comments (/* ... */)
COMMENT_REGEX = re.compile(r"(--[^\r\n]*)|(/\*[\s\S]*?\*/)")

# Regex to split SQL by tokens (words, symbols, string literals)
TOKEN_REGEX = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*|'[^']*'|\"[^\"]*\"|;|--|/\*|\*/")


def sanitize_and_tokenize_sql(raw_sql: str) -> Tuple[str, List[str]]:
    """Strip comments and return clean SQL text along with uppercase keyword tokens."""
    # 1. Strip comments
    clean_sql = COMMENT_REGEX.sub(" ", raw_sql).strip()

    # 2. Extract tokens outside string literals
    raw_tokens = TOKEN_REGEX.findall(clean_sql)
    tokens: List[str] = []
    for token in raw_tokens:
        if token.startswith("'") or token.startswith('"'):
            continue
        tokens.append(token.upper())

    return clean_sql, tokens


def validate_sql_safety(raw_sql: str, params: Optional[Dict[str, Any]] = None) -> str:
    """Validate that the given SQL query is strictly a safe read-only SELECT or WITH statement.
    
    Raises ValueError or PermissionError with a descriptive message if unsafe.
    Returns the cleaned SQL string on success.
    """
    if not raw_sql or not raw_sql.strip():
        raise ValueError("SQL query string cannot be empty.")

    if len(raw_sql) > 5000:
        raise ValueError("SQL query exceeds maximum allowed length of 5000 characters.")

    if params and len(params) > 50:
        raise ValueError("Query parameters exceed maximum allowed limit of 50 parameters.")

    clean_sql, tokens = sanitize_and_tokenize_sql(raw_sql)

    if not tokens:
        raise ValueError("No executable SQL tokens found in query.")

    # 1. Must start with SELECT or WITH
    first_token = tokens[0]
    if first_token not in ("SELECT", "WITH"):
        raise PermissionError(
            f"Prohibited statement type '{first_token}'. Only read-only SELECT or WITH queries are permitted."
        )

    # 2. Multi-statement prevention: check for semicolons that have subsequent tokens
    semicolon_indices = [i for i, t in enumerate(tokens) if t == ";"]
    for idx in semicolon_indices:
        # If there are tokens after the semicolon, it's a multi-statement attempt
        if idx < len(tokens) - 1:
            raise PermissionError("Multiple SQL statements separated by semicolons are strictly prohibited.")

    # 3. Check for forbidden keywords in tokens
    for token in tokens:
        if token in FORBIDDEN_SQL_TOKENS:
            raise PermissionError(f"Prohibited SQL keyword detected: '{token}'. Mutating operations are forbidden.")

    # 4. Trailing semicolon cleanup
    if clean_sql.endswith(";"):
        clean_sql = clean_sql[:-1].strip()

    return clean_sql


class SQLInvestigationTool(BaseTool):
    """Controlled tool for executing read-only analytical SQL queries."""

    name: str = "sql_investigation"
    description: str = (
        "Safely executes read-only SQL queries against the enterprise relational database. "
        "Permits SELECT and WITH statements only, with parameterized inputs and row limits."
    )
    input_model = SQLQueryInput
    output_model = SQLQueryResult

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url

    def _run(self, validated_input: SQLQueryInput) -> SQLQueryResult:
        """Validate safety constraints and execute the read-only query."""
        try:
            clean_sql = validate_sql_safety(
                raw_sql=validated_input.query,
                params=validated_input.params,
            )
        except (ValueError, PermissionError) as safety_err:
            return SQLQueryResult(
                success=False,
                error=str(safety_err),
            )

        engine = get_engine(self.db_url)
        params = validated_input.params or {}
        max_rows = validated_input.max_rows

        try:
            with engine.connect() as connection:
                # Fetch max_rows + 1 to detect if truncation occurred
                stmt = text(clean_sql)
                result = connection.execute(stmt, params)
                columns = list(result.keys())
                fetched_rows = result.fetchmany(max_rows + 1)

                truncated = len(fetched_rows) > max_rows
                output_rows = fetched_rows[:max_rows]

                row_dicts = [dict(zip(columns, row)) for row in output_rows]

                return SQLQueryResult(
                    success=True,
                    columns=columns,
                    rows=row_dicts,
                    row_count=len(row_dicts),
                    truncated=truncated,
                    error=None,
                )
        except Exception as db_err:
            return SQLQueryResult(
                success=False,
                error=f"Database execution error: {str(db_err)}",
            )
