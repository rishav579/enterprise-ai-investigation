# Architecture Decision Records (ADRs)

This document records the foundational architectural decisions made for the **Enterprise AI Investigation & Decision System**, including context, options considered, decisions, and consequences.

---

## ADR 001: Python + FastAPI as Backend Framework

- **Status:** Accepted
- **Date:** Phase 0 (Foundation)
- **Context:** The system requires a modern, high-performance web backend capable of asynchronous request handling, strict data validation, clean OpenAPI documentation, and seamless integration with Python-based AI and data ecosystem libraries.
- **Decision:** Use **Python 3.11+** with **FastAPI** and **Pydantic v2**.
- **Consequences:**
  - *Positive:* Native support for type hints, automatic OpenAPI/Swagger generation, high throughput with ASGI, rich data ecosystem (SQLAlchemy, SQLGlot, AI SDKs).
  - *Trade-off:* Requires careful management of asynchronous operations and blocking calls during heavy data operations.

---

## ADR 002: SQLite Initially with PostgreSQL-Ready Abstraction

- **Status:** Accepted
- **Date:** Phase 0 (Foundation)
- **Context:** We need a reliable relational database for development, testing, and portfolio demonstrations that runs locally with zero external service dependencies, while ensuring straightforward migration to enterprise PostgreSQL in production.
- **Decision:** Use **SQLite** for development and testing via **SQLAlchemy 2.0** repository patterns, ensuring database dialect agnosticism so the system runs against SQLite or PostgreSQL with zero business logic changes.
- **Consequences:**
  - *Positive:* Zero installation overhead for reviewers cloning the repository; deterministic, isolated test databases created and torn down in milliseconds.
  - *Trade-off:* Advanced PostgreSQL-specific features (e.g., specific jsonb indexing or pgvector) will use abstract interfaces rather than tight coupling.

---

## ADR 003: Controlled Tool Registry (No Arbitrary Shell/Code Execution)

- **Status:** Accepted
- **Date:** Phase 0 (Foundation)
- **Context:** Unconstrained AI agents with access to bash/shell or raw Python `eval()` present unacceptable security risks in enterprise environments, including data destruction, exfiltration, and prompt injection attacks.
- **Decision:** Enforce a **Strict Controlled Tool Registry**. The LLM can only invoke registered, pre-defined tools with validated Pydantic parameter schemas. Arbitrary shell, OS commands, and dynamic code evaluation are strictly prohibited.
- **Consequences:**
  - *Positive:* Deterministic security boundary, zero risk of arbitrary remote code execution via prompt injection.
  - *Trade-off:* The LLM cannot invent ad-hoc scripts on the fly; all capabilities must be exposed via well-defined tools.

---

## ADR 004: Strictly Enforced Read-Only SQL Access

- **Status:** Accepted
- **Date:** Phase 0 (Foundation)
- **Context:** Investigating enterprise data requires running dynamic queries against relational databases. Allowing mutating SQL statements (`UPDATE`, `DELETE`, `DROP`, `ALTER`, etc.) would compromise data integrity.
- **Decision:** Implement multi-layered read-only SQL enforcement:
  1. **AST-Level Validation:** Parse all incoming SQL using an Abstract Syntax Tree (AST) parser (e.g., `sqlglot`) to verify statements are strictly `SELECT` queries without modifying clauses.
  2. **Connection Safety:** Execute queries through read-only database connections/sessions.
  3. **Row Limit Guards:** Automatically apply `LIMIT` clauses to prevent memory exhaustion from runaway queries.
- **Consequences:**
  - *Positive:* Complete protection against accidental or malicious data modification.
  - *Trade-off:* AI cannot execute analytical write operations (e.g., temporary table creation) directly in the database.

---

## ADR 005: Provider-Agnostic LLM Layer

- **Status:** Accepted
- **Date:** Phase 0 (Foundation)
- **Context:** Tying the architecture to a single proprietary AI vendor creates vendor lock-in and prevents testing against local, open-source, or cost-effective offline models.
- **Decision:** Create an abstract `LLMClient` interface that wraps model interactions. Concrete adapters will support OpenAI, Anthropic, and local model runtimes (such as Ollama).
- **Consequences:**
  - *Positive:* Easy benchmarking across different models; ability to run entirely offline or in air-gapped environments.
  - *Trade-off:* Prompts must be designed for universal model compatibility rather than relying on vendor-specific prompt extensions.

---

## ADR 006: Evidence-First Architecture with Citations

- **Status:** Accepted
- **Date:** Phase 0 (Foundation)
- **Context:** Generative AI outputs in enterprise settings often suffer from subtle hallucinations, ungrounded assumptions, and lack of accountability.
- **Decision:** Implement an **Evidence-First Architecture**. The system collects raw observations into an append-only `EvidenceCollector`. The final synthesis step requires every claim and finding to cite explicit `evidence_id` tokens linked to raw query rows or document excerpts.
- **Consequences:**
  - *Positive:* High auditability, verifiable trust for human decision-makers, eliminates unsubstantiated hallucinated claims.
  - *Trade-off:* Requires an additional extraction and validation step before presenting recommendations.

---

## ADR 007: Deterministic Offline Evaluation without Fabricated Metrics

- **Status:** Accepted
- **Date:** Phase 0 (Foundation)
- **Context:** AI portfolio projects frequently claim unrealistic or unsubstantiated accuracy statistics (e.g., "99.8% accuracy on enterprise data").
- **Decision:** Avoid all fabricated performance claims. Instead, implement a **Deterministic Evaluation Suite** using pytest and synthetic golden scenarios with known ground-truth answers. All accuracy and safety metrics must be reproducible locally by running the test suite.
- **Consequences:**
  - *Positive:* High credibility, authentic engineering rigor, transparent and reproducible test results.
  - *Trade-off:* Requires upfront investment in crafting realistic synthetic evaluation test cases.
