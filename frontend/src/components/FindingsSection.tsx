import React from 'react';
import {
  FileCheck2,
  CheckCircle,
  AlertTriangle,
  HelpCircle,
  Info,
  ShieldCheck,
} from 'lucide-react';
import type { InvestigationReport } from '../api/types';

interface FindingsSectionProps {
  report: InvestigationReport;
  onSelectEvidenceId: (evidenceId: string) => void;
}

export const FindingsSection: React.FC<FindingsSectionProps> = ({
  report,
  onSelectEvidenceId,
}) => {
  const isInsufficient = report.synthesis_status === 'insufficient_evidence';
  const isValidationFailed = report.synthesis_status === 'validation_failed';

  const renderConfidenceBadge = (confidence: string) => {
    switch (confidence) {
      case 'high':
        return <span className="badge badge-success">High Confidence</span>;
      case 'medium':
        return <span className="badge badge-warning">Medium Confidence</span>;
      case 'low':
        return <span className="badge badge-danger">Low Confidence</span>;
      default:
        return null;
    }
  };

  return (
    <div style={{
      backgroundColor: 'var(--bg-panel)',
      border: '1px solid var(--border-default)',
      borderRadius: 'var(--radius-lg)',
      padding: '20px',
      display: 'flex',
      flexDirection: 'column',
      gap: '20px',
    }}>
      {/* Section Header with Validation State */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
        <div>
          <h2 style={{ fontSize: '15px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileCheck2 size={16} color="var(--color-primary)" />
            Synthesized Findings & Root Cause Analysis
          </h2>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Grounded synthesis requiring 100% verified citations linked to raw EvidenceStore items.
          </p>
        </div>

        {/* Provenance & Citation Verification Badge */}
        <div>
          {report.citation_valid ? (
            <span className="badge badge-success" style={{ padding: '4px 10px', fontSize: '12px' }}>
              <ShieldCheck size={13} /> Citations 100% Verified
            </span>
          ) : isInsufficient ? (
            <span className="badge badge-warning" style={{ padding: '4px 10px', fontSize: '12px' }}>
              <HelpCircle size={13} /> Insufficient Evidence
            </span>
          ) : (
            <span className="badge badge-danger" style={{ padding: '4px 10px', fontSize: '12px' }}>
              <AlertTriangle size={13} /> Citation Validation Failed
            </span>
          )}
        </div>
      </div>

      {/* Validation Errors Warning if Any */}
      {report.validation_errors && report.validation_errors.length > 0 && (
        <div style={{
          backgroundColor: 'var(--color-danger-bg)',
          border: '1px solid var(--color-danger-border)',
          borderRadius: 'var(--radius-md)',
          padding: '12px 16px',
          color: 'var(--color-danger)',
          fontSize: '13px',
        }}>
          <div style={{ fontWeight: 600, marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <AlertTriangle size={15} /> Citation Validation Violations Detected:
          </div>
          <ul style={{ paddingLeft: '20px', margin: 0 }}>
            {report.validation_errors.map((err, i) => (
              <li key={i}>{err}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Executive Summary */}
      <div style={{
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        padding: '14px 16px',
      }}>
        <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>
          Executive Summary
        </div>
        <p style={{ fontSize: '13px', color: 'var(--text-primary)', lineHeight: '1.6' }}>
          {report.executive_summary}
        </p>
      </div>

      {/* Root Cause Box */}
      <div style={{
        backgroundColor: isInsufficient
          ? 'var(--color-warning-bg)'
          : isValidationFailed
          ? 'var(--color-danger-bg)'
          : 'rgba(56, 189, 248, 0.08)',
        border: `1px solid ${
          isInsufficient
            ? 'var(--color-warning-border)'
            : isValidationFailed
            ? 'var(--color-danger-border)'
            : 'var(--color-primary-border)'
        }`,
        borderRadius: 'var(--radius-md)',
        padding: '16px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          {isInsufficient ? (
            <HelpCircle size={18} color="var(--color-warning)" />
          ) : isValidationFailed ? (
            <AlertTriangle size={18} color="var(--color-danger)" />
          ) : (
            <CheckCircle size={18} color="var(--color-primary)" />
          )}
          <span style={{
            fontSize: '13px',
            fontWeight: 700,
            color: isInsufficient
              ? 'var(--color-warning)'
              : isValidationFailed
              ? 'var(--color-danger)'
              : 'var(--color-primary)',
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
          }}>
            {isInsufficient ? 'Root Cause: Indeterminate (Evidence Gap)' : 'Primary Identified Root Cause'}
          </span>
        </div>
        <p style={{
          fontSize: '14px',
          fontWeight: 500,
          color: 'var(--text-primary)',
          lineHeight: '1.5',
        }}>
          {report.root_cause || (
            <span style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>
              No root cause could be established with deterministic factual certainty from available telemetry and evidence artifacts. Zero speculations were manufactured.
            </span>
          )}
        </p>
      </div>

      {/* Evidence-Backed Findings List */}
      {report.findings.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Grounded Findings ({report.findings.length})
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {report.findings.map((finding) => (
              <div
                key={finding.finding_id}
                style={{
                  backgroundColor: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '12px 16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px' }}>
                  <span style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '12px',
                    fontWeight: 700,
                    color: 'var(--color-primary)',
                  }}>
                    {finding.finding_id}
                  </span>
                  {renderConfidenceBadge(finding.confidence)}
                </div>

                <div style={{ fontSize: '13px', color: 'var(--text-primary)', lineHeight: '1.5' }}>
                  {finding.statement}
                </div>

                {/* Evidence Citations */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap', marginTop: '2px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>
                    EVIDENCE CITATIONS:
                  </span>
                  {finding.evidence_ids.map((eid) => (
                    <button
                      key={eid}
                      type="button"
                      className="citation-token"
                      onClick={() => onSelectEvidenceId(eid)}
                      title="Inspect cited EvidenceItem"
                    >
                      🔗 {eid}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Contributing Factors & Limitations Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '12px',
      }}>
        {/* Contributing Factors */}
        {report.contributing_factors.length > 0 && (
          <div style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 16px',
          }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '8px' }}>
              Contributing Factors
            </div>
            <ul style={{ paddingLeft: '18px', fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.6' }}>
              {report.contributing_factors.map((factor, idx) => (
                <li key={idx} style={{ marginBottom: '4px' }}>{factor}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Limitations & Data Gaps */}
        {report.limitations.length > 0 && (
          <div style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 16px',
          }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Info size={14} color="var(--color-info)" />
              Investigation Scope & Limitations
            </div>
            <ul style={{ paddingLeft: '18px', fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.6' }}>
              {report.limitations.map((lim, idx) => (
                <li key={idx} style={{ marginBottom: '4px' }}>{lim}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};
