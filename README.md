# Enterprise AI Investigation & Decision System

> **Portfolio & Educational Disclaimer:**
> This repository is an educational portfolio project simulating an enterprise-grade AI investigation and decision-support system. It is designed to demonstrate production-grade AI system architecture, safety guardrails, controlled tool execution, and evidence-first decision making. It does **not** claim real company usage, real customer data, or fabricated performance metrics.

---

## 📌 Problem Statement

In enterprise environments, operational anomalies (such as sudden customer churn spikes, billing discrepancies, or supply chain bottlenecks) require cross-functional investigation across structured relational databases and unstructured internal documents. 

Standard LLM chat interfaces often hallucinate answers, lack access to live data, or pose severe security risks if granted unconstrained database or shell access. Enterprises need an **auditable, deterministic, and evidence-grounded AI investigation system** where every conclusion is traceable back to verified raw evidence, tools operate within strict sandboxes, and actions require human authorization.

---

## 🎯 Purpose & Goals

The **Enterprise AI Investigation & Decision System** simulates an internal AI analyst that:
1. Translates high-level business questions into structured investigation plans.
2. Selects and executes specific, sandboxed, read-only tools to gather facts.
3. Queries structured SQL databases safely (read-only AST-validated queries).
4. Retrieves relevant internal documentation and policy guidelines.
5. Assembles a structured, immutable evidence chain with citations.
6. Synthesizes an evidence-backed root-cause analysis and actionable recommendations.
7. Enforces a human-in-the-loop approval workflow prior to decision execution.

---

## 🔄 Investigation Flow

```
Business Question / Incident Alert
               │
               ▼
   [ Investigation Planner ]
               │
               ▼
   [ Controlled Tool Registry ]
       ├── Read-Only SQL Investigation Tool
       ├── Document & Policy Retrieval Tool
       └── Domain-Specific API Tools (Mocked)
               │
               ▼
     [ Evidence Collector ]
  (Raw queries, records, citations)
               │
               ▼
     [ Root-Cause Analysis ]
               │
               ▼
  [ Evidence-Backed Recommendation ]
               │
               ▼
   [ Human Approval / Sign-Off ]
```

---

## 🛡️ Core Architectural Principles

- **Controlled Tools Only:** No arbitrary shell or dynamic code execution. Every tool has a strictly typed input/output schema.
- **Read-Only SQL Access:** All SQL queries are parsed via Abstract Syntax Tree (AST) validation and executed against read-only database connections.
- **Evidence-First Responses:** Every claim in a final recommendation must cite specific records, metrics, or document excerpts captured in the evidence collector.
- **Auditable Tool Execution:** Complete immutable audit logs capturing prompts, tool invocations, parameters, raw tool outputs, and timestamps.
- **Data & Repository Isolation:** Clear separation between domain logic, data access repositories, and AI orchestration.
- **Provider-Agnostic LLM Layer:** Abstracted model interface allowing seamless switching between OpenAI, Anthropic, or local offline models (e.g., via Ollama).
- **Deterministic Evaluation:** System performance is evaluated against reproducible, offline test scenarios with verified ground truth—avoiding subjective or fabricated benchmark numbers.

---

## 🛠️ Planned Tech Stack

| Layer | Planned Technology |
| :--- | :--- |
| **Language & Runtime** | Python 3.11+ |
| **API Framework** | FastAPI (ASGI) |
| **Data Validation & Schemas** | Pydantic v2 |
| **Data Layer & ORM** | SQLAlchemy 2.0 (Repository Pattern) |
| **Databases** | SQLite (development/local) → PostgreSQL (production abstraction) |
| **SQL Safety** | SQLGlot / AST analysis for read-only query verification |
| **Document Retrieval** | Local embeddings + Vector/FTS search abstraction |
| **Testing & Evaluation** | Pytest, JSON Schema validation, deterministic test suites |
| **Frontend (Future)** | Modern lightweight web interface |

---

## 🚦 Project Status

- **Current Phase:** `Phase 0 — Foundation`
- **Next Phase:** `Phase 1 — Enterprise Data Foundation`

See [ROADMAP.md](docs/ROADMAP.md) for full phase-by-phase execution plan.
See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architectural specifications.
See [DECISIONS.md](docs/DECISIONS.md) for Architecture Decision Records (ADRs).
