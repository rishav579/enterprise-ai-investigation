# Enterprise AI Investigation Workspace — Frontend

This directory contains the React + TypeScript + Vite frontend workspace for the **Enterprise AI Investigation & Decision System**.

## 🏗️ Architecture

- **Framework:** React 19 + TypeScript + Vite
- **Testing:** Vitest + React Testing Library + `@testing-library/jest-dom`
- **Design:** Custom Enterprise Slate Design System (`src/index.css`)
- **API Client:** Centralized typed client (`src/api/client.ts`) with timeout and defensive error handling

## 🚀 Development & Testing

```bash
# Install dependencies
npm install

# Run unit and integration tests (32 tests)
npm test

# Build production bundle
npm run build

# Start local development server (port 5173)
npm run dev
```

## 🧩 Components

- **`Header.tsx`:** Operational branding, backend status ping (`/health`), and active investigation ID indicator.
- **`QuestionInput.tsx`:** Custom question input with character counter and 1-click golden benchmark scenario dispatcher.
- **`InvestigationTimeline.tsx`:** Real-time ordered step execution tracker with status pills, tool payloads, row counts, and evidence artifact badges.
- **`FindingsSection.tsx`:** Structured executive summary, primary root cause alert box, grounded findings with confidence badges, and citation verification badges.
- **`RecommendationsSection.tsx`:** Actionable operational remediations with priority levels and interactive **Human Review Simulation** ("Approve", "Reject", "Request More Evidence").
- **`EvidenceInspector.tsx`:** Rich inspection drawer displaying raw SQL result tables, full document text excerpts, line-by-line keyword matches, and canonical SHA-256 content hashes.
- **`AuditTrailStream.tsx`:** Filterable sequential trace of immutable lifecycle events (`AUDIT-001`, `AUDIT-002`, ...).
- **`GuardrailsBanner.tsx`:** Highlighting active safety boundaries (AST SQL parser, path traversal guard, cross-run citation isolation, zero-fabrication invariant).
