/**
 * TypeScript definitions mapping directly to backend Pydantic models.
 */

export type StepStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped' | 'blocked';
export type InvestigationStatus = 'pending' | 'running' | 'completed' | 'partial' | 'failed';

export interface InvestigationRequestPayload {
  question: string;
  investigation_id?: string;
  scenario_hint?: string;
}

export interface InvestigationStep {
  step_id: string;
  objective: string;
  rationale: string;
  tool_name: string;
  tool_input: Record<string, unknown>;
  expected_evidence_type: string;
  depends_on: string[];
}

export interface InvestigationPlan {
  plan_id: string;
  investigation_id: string;
  question: string;
  scenario: string;
  steps: InvestigationStep[];
  total_steps: number;
}

export interface InvestigationStepResult {
  step_id: string;
  status: StepStatus;
  tool_name: string;
  tool_input: Record<string, unknown>;
  tool_output?: Record<string, unknown> | null;
  error_message?: string | null;
  row_count?: number | null;
  evidence_summary?: string | null;
  evidence_ids: string[];
}

export interface InvestigationRunResult {
  investigation_id: string;
  question: string;
  status: InvestigationStatus;
  plan: InvestigationPlan;
  step_results: InvestigationStepResult[];
  total_steps: number;
  completed_steps: number;
  failed_steps: number;
  skipped_steps: number;
  error_message?: string | null;
  total_evidence_items: number;
  audit_event_count: number;
}

export type EvidenceType =
  | 'sql_result'
  | 'database_record'
  | 'document_text'
  | 'document_match'
  | 'document_listing'
  | 'document_search_summary'
  | 'metric';

export interface SQLEvidenceContent {
  query_reference: string;
  columns: string[];
  rows: Array<Record<string, unknown>>;
  row_count: number;
  truncated?: boolean;
}

export interface DocumentTextContent {
  document_id: string;
  full_text: string;
  char_count: number;
}

export interface DocumentMatchContent {
  document_id: string;
  line_number: number;
  excerpt: string;
  context_before?: string | null;
  context_after?: string | null;
}

export interface DocumentListingContent {
  documents: Array<{ id: string; title: string; size_bytes?: number }>;
  document_count: number;
}

export interface EvidenceItem {
  evidence_id: string;
  investigation_run_id: string;
  step_id: string;
  tool_name: string;
  evidence_type: EvidenceType;
  source_reference: string;
  content: Record<string, unknown>;
  content_hash: string;
  sequence_number: number;
  metadata?: Record<string, unknown>;
}

export type ConfidenceLevel = 'high' | 'medium' | 'low';
export type PriorityLevel = 'critical' | 'high' | 'medium' | 'low';
export type SynthesisStatus = 'success' | 'insufficient_evidence' | 'validation_failed' | 'error';

export interface Finding {
  finding_id: string;
  statement: string;
  evidence_ids: string[];
  confidence: ConfidenceLevel;
}

export interface Recommendation {
  recommendation_id: string;
  action: string;
  rationale: string;
  evidence_ids: string[];
  priority: PriorityLevel;
}

export interface InvestigationReport {
  investigation_run_id: string;
  question: string;
  executive_summary: string;
  findings: Finding[];
  root_cause?: string | null;
  contributing_factors: string[];
  recommendations: Recommendation[];
  limitations: string[];
  evidence_ids: string[];
  citation_valid: boolean;
  synthesis_status: SynthesisStatus;
  validation_errors: string[];
  metadata?: Record<string, unknown>;
}

export type AuditEventType =
  | 'investigation_started'
  | 'plan_created'
  | 'step_started'
  | 'step_completed'
  | 'step_failed'
  | 'step_blocked'
  | 'evidence_collected'
  | 'investigation_completed'
  | 'investigation_failed'
  | 'investigation_partial'
  | 'synthesis_started'
  | 'synthesis_generated'
  | 'synthesis_validated'
  | 'synthesis_failed';

export interface AuditEvent {
  event_id: string;
  investigation_run_id: string;
  event_type: AuditEventType;
  sequence_number: number;
  step_id?: string | null;
  tool_name?: string | null;
  evidence_ids: string[];
  metadata?: Record<string, unknown>;
}

export interface FullInvestigationResponse {
  run_result: InvestigationRunResult;
  report: InvestigationReport;
  evidence_items: EvidenceItem[];
  audit_events: AuditEvent[];
}

export interface ScenarioItem {
  id: string;
  name: string;
  question: string;
  category: string;
  expected_behavior: string;
}

export interface BackendHealthResponse {
  status: string;
  version?: string;
  app?: string;
}

export type ReviewDecision = 'approved' | 'rejected' | 'more_evidence_needed' | 'pending';

export interface SimulatedReviewState {
  recommendation_id: string;
  decision: ReviewDecision;
  reviewer: string;
  timestamp: string;
  comments?: string;
}
