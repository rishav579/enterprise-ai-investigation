import React, { useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  Database,
  FileText,
  ChevronDown,
  ChevronRight,
  ShieldAlert,
  Search,
} from 'lucide-react';
import type { InvestigationPlan, InvestigationStepResult } from '../api/types';

interface InvestigationTimelineProps {
  plan: InvestigationPlan;
  stepResults: InvestigationStepResult[];
  onSelectEvidenceId: (evidenceId: string) => void;
}

export const InvestigationTimeline: React.FC<InvestigationTimelineProps> = ({
  plan,
  stepResults,
  onSelectEvidenceId,
}) => {
  const [expandedStepIds, setExpandedStepIds] = useState<Set<string>>(
    new Set(plan.steps.map((s) => s.step_id))
  );

  const toggleStep = (stepId: string) => {
    setExpandedStepIds((prev) => {
      const next = new Set(prev);
      if (next.has(stepId)) {
        next.delete(stepId);
      } else {
        next.add(stepId);
      }
      return next;
    });
  };

  const getStepResult = (stepId: string): InvestigationStepResult | undefined => {
    return stepResults.find((r) => r.step_id === stepId);
  };

  const renderStatusBadge = (status?: string) => {
    switch (status) {
      case 'completed':
        return (
          <span className="badge badge-success">
            <CheckCircle2 size={11} /> Completed
          </span>
        );
      case 'failed':
        return (
          <span className="badge badge-danger">
            <XCircle size={11} /> Failed
          </span>
        );
      case 'blocked':
        return (
          <span className="badge badge-warning">
            <ShieldAlert size={11} /> Blocked
          </span>
        );
      case 'skipped':
        return (
          <span className="badge badge-neutral">
            <Clock size={11} /> Skipped
          </span>
        );
      default:
        return (
          <span className="badge badge-info">
            <Clock size={11} /> Pending
          </span>
        );
    }
  };

  const renderToolIcon = (toolName: string) => {
    if (toolName === 'sql_investigation') {
      return <Database size={13} color="var(--color-primary)" />;
    }
    return <FileText size={13} color="var(--color-info)" />;
  };

  return (
    <div style={{
      backgroundColor: 'var(--bg-panel)',
      border: '1px solid var(--border-default)',
      borderRadius: 'var(--radius-lg)',
      padding: '20px',
      display: 'flex',
      flexDirection: 'column',
      gap: '16px',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
        <div>
          <h2 style={{ fontSize: '15px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Search size={16} color="var(--color-primary)" />
            Investigation Plan & Tool Execution Timeline
          </h2>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Ordered, dependency-aware tool dispatches executing read-only AST SQL & document retrievals.
          </p>
        </div>
        <div style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
          Scenario: <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{plan.scenario}</span> ({plan.steps.length} steps)
        </div>
      </div>

      {/* Steps List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {plan.steps.map((step) => {
          const result = getStepResult(step.step_id);
          const isExpanded = expandedStepIds.has(step.step_id);
          const status = result ? result.status : 'pending';

          return (
            <div
              key={step.step_id}
              style={{
                backgroundColor: 'var(--bg-surface)',
                border: `1px solid ${
                  status === 'failed'
                    ? 'var(--color-danger-border)'
                    : status === 'blocked'
                    ? 'var(--color-warning-border)'
                    : 'var(--border-subtle)'
                }`,
                borderRadius: 'var(--radius-md)',
                overflow: 'hidden',
                transition: 'border-color 0.15s ease',
              }}
            >
              {/* Step Header Row */}
              <div
                onClick={() => toggleStep(step.step_id)}
                style={{
                  padding: '12px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '12px',
                  cursor: 'pointer',
                  userSelect: 'none',
                  backgroundColor: 'rgba(255, 255, 255, 0.02)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1, minWidth: 0 }}>
                  <button
                    type="button"
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--text-secondary)',
                      display: 'flex',
                      alignItems: 'center',
                      padding: 0,
                    }}
                    aria-label={isExpanded ? 'Collapse step' : 'Expand step'}
                  >
                    {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                  </button>

                  <span style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '12px',
                    fontWeight: 700,
                    color: 'var(--color-primary)',
                    minWidth: '60px',
                  }}>
                    {step.step_id}
                  </span>

                  <span style={{
                    fontSize: '13px',
                    fontWeight: 500,
                    color: 'var(--text-primary)',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}>
                    {step.objective}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
                  <span className="badge badge-neutral" style={{ textTransform: 'none' }}>
                    {renderToolIcon(step.tool_name)}
                    {step.tool_name}
                  </span>

                  {result?.row_count !== undefined && result.row_count !== null && (
                    <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      {result.row_count} rows
                    </span>
                  )}

                  {renderStatusBadge(status)}
                </div>
              </div>

              {/* Step Expanded Content */}
              {isExpanded && (
                <div style={{
                  padding: '14px 16px',
                  borderTop: '1px solid var(--border-subtle)',
                  backgroundColor: 'var(--bg-app)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px',
                  fontSize: '12px',
                }}>
                  {/* Rationale */}
                  <div>
                    <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Rationale: </span>
                    <span style={{ color: 'var(--text-muted)' }}>{step.rationale}</span>
                  </div>

                  {/* Dependencies */}
                  {step.depends_on.length > 0 && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Depends on: </span>
                      {step.depends_on.map((dep) => (
                        <span key={dep} className="badge badge-neutral" style={{ fontSize: '10px' }}>
                          {dep}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Error Message if Failed/Blocked */}
                  {result?.error_message && (
                    <div style={{
                      backgroundColor: 'var(--color-danger-bg)',
                      border: '1px solid var(--color-danger-border)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '8px 12px',
                      color: 'var(--color-danger)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                    }}>
                      <AlertCircle size={14} />
                      <span>{result.error_message}</span>
                    </div>
                  )}

                  {/* Tool Input Query or Action */}
                  {step.tool_input && (
                    <div>
                      <div style={{ fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                        Tool Payload:
                      </div>
                      <pre style={{
                        backgroundColor: 'var(--bg-panel)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-sm)',
                        padding: '8px 10px',
                        color: '#93c5fd',
                        fontSize: '11px',
                        overflowX: 'auto',
                        whiteSpace: 'pre-wrap',
                      }}>
                        {typeof step.tool_input.query === 'string'
                          ? step.tool_input.query
                          : JSON.stringify(step.tool_input, null, 2)}
                      </pre>
                    </div>
                  )}

                  {/* Evidence Summary & Badges */}
                  {result?.evidence_summary && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <div>
                        <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Evidence Output: </span>
                        <span style={{ color: 'var(--color-success)' }}>{result.evidence_summary}</span>
                      </div>

                      {result.evidence_ids.length > 0 && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                          <span style={{ color: 'var(--text-muted)' }}>Collected Artifacts:</span>
                          {result.evidence_ids.map((eid) => (
                            <button
                              key={eid}
                              type="button"
                              className="citation-token"
                              onClick={() => onSelectEvidenceId(eid)}
                              title="Click to view raw evidence and cryptographic content hash"
                            >
                              🔍 {eid}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
