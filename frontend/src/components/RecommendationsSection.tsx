import React, { useState } from 'react';
import {
  ListChecks,
  CheckCircle2,
  XCircle,
  HelpCircle,
  UserCheck,
  Clock,
  ShieldCheck,
} from 'lucide-react';
import type {
  Recommendation,
  ReviewDecision,
  SimulatedReviewState,
} from '../api/types';

interface RecommendationsSectionProps {
  recommendations: Recommendation[];
  onSelectEvidenceId: (evidenceId: string) => void;
}

export const RecommendationsSection: React.FC<RecommendationsSectionProps> = ({
  recommendations,
  onSelectEvidenceId,
}) => {
  // Local state for human review simulation
  const [reviews, setReviews] = useState<Record<string, SimulatedReviewState>>({});
  const [activeCommentId, setActiveCommentId] = useState<string | null>(null);
  const [commentText, setCommentText] = useState<string>('');

  const handleDecision = (recId: string, decision: ReviewDecision) => {
    setReviews((prev) => ({
      ...prev,
      [recId]: {
        recommendation_id: recId,
        decision,
        reviewer: 'Enterprise Incident Reviewer (You)',
        timestamp: new Date().toLocaleTimeString(),
        comments: prev[recId]?.comments || '',
      },
    }));
  };

  const handleSaveComment = (recId: string) => {
    if (reviews[recId]) {
      setReviews((prev) => ({
        ...prev,
        [recId]: {
          ...prev[recId],
          comments: commentText,
        },
      }));
    }
    setActiveCommentId(null);
    setCommentText('');
  };

  const renderPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'critical':
        return <span className="badge badge-danger">Critical Priority</span>;
      case 'high':
        return <span className="badge badge-warning">High Priority</span>;
      case 'medium':
        return <span className="badge badge-info">Medium Priority</span>;
      case 'low':
        return <span className="badge badge-neutral">Low Priority</span>;
      default:
        return null;
    }
  };

  const renderReviewStatusBadge = (decision?: ReviewDecision) => {
    switch (decision) {
      case 'approved':
        return (
          <span className="badge badge-success" style={{ fontSize: '11px' }}>
            <CheckCircle2 size={11} /> Approved by Human Reviewer
          </span>
        );
      case 'rejected':
        return (
          <span className="badge badge-danger" style={{ fontSize: '11px' }}>
            <XCircle size={11} /> Rejected by Reviewer
          </span>
        );
      case 'more_evidence_needed':
        return (
          <span className="badge badge-warning" style={{ fontSize: '11px' }}>
            <HelpCircle size={11} /> Additional Evidence Requested
          </span>
        );
      default:
        return (
          <span className="badge badge-neutral" style={{ fontSize: '11px' }}>
            <Clock size={11} /> Pending Human Sign-Off
          </span>
        );
    }
  };

  if (recommendations.length === 0) {
    return null;
  }

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
            <ListChecks size={16} color="var(--color-primary)" />
            Actionable Recommendations & Human Authorization
          </h2>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Operational remediations linked to verified evidence with explicit human review simulation.
          </p>
        </div>

        {/* Simulation Notice */}
        <div style={{
          backgroundColor: 'rgba(251, 191, 36, 0.08)',
          border: '1px solid var(--color-warning-border)',
          borderRadius: 'var(--radius-sm)',
          padding: '4px 10px',
          fontSize: '11px',
          fontWeight: 600,
          color: 'var(--color-warning)',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
        }}>
          <UserCheck size={13} />
          HUMAN REVIEW — SIMULATION
        </div>
      </div>

      {/* Recommendations Cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {recommendations.map((rec) => {
          const review = reviews[rec.recommendation_id];
          const isCommenting = activeCommentId === rec.recommendation_id;

          return (
            <div
              key={rec.recommendation_id}
              style={{
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
              }}
            >
              {/* Header: ID + Priority + Review Status */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '12px',
                    fontWeight: 700,
                    color: 'var(--color-primary)',
                  }}>
                    {rec.recommendation_id}
                  </span>
                  {renderPriorityBadge(rec.priority)}
                </div>

                <div>
                  {renderReviewStatusBadge(review?.decision)}
                </div>
              </div>

              {/* Action Description */}
              <div>
                <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '2px' }}>
                  Recommended Action:
                </div>
                <p style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', lineHeight: '1.4' }}>
                  {rec.action}
                </p>
              </div>

              {/* Rationale */}
              <div>
                <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '2px' }}>
                  Operational Rationale:
                </div>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                  {rec.rationale}
                </p>
              </div>

              {/* Evidence Citations */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>
                  SUPPORTING EVIDENCE:
                </span>
                {rec.evidence_ids.map((eid) => (
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

              {/* Human Review Simulation Controls */}
              <div style={{
                marginTop: '4px',
                paddingTop: '12px',
                borderTop: '1px solid var(--border-subtle)',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <ShieldCheck size={12} color="var(--color-primary)" />
                    Human Authorization Simulation:
                  </div>

                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                    <button
                      type="button"
                      onClick={() => handleDecision(rec.recommendation_id, 'approved')}
                      style={{
                        padding: '4px 10px',
                        fontSize: '11px',
                        fontWeight: 600,
                        borderRadius: 'var(--radius-sm)',
                        backgroundColor: review?.decision === 'approved' ? 'var(--color-success)' : 'var(--bg-app)',
                        color: review?.decision === 'approved' ? '#030712' : 'var(--color-success)',
                        border: '1px solid var(--color-success-border)',
                      }}
                    >
                      ✓ Approve Action
                    </button>

                    <button
                      type="button"
                      onClick={() => handleDecision(rec.recommendation_id, 'rejected')}
                      style={{
                        padding: '4px 10px',
                        fontSize: '11px',
                        fontWeight: 600,
                        borderRadius: 'var(--radius-sm)',
                        backgroundColor: review?.decision === 'rejected' ? 'var(--color-danger)' : 'var(--bg-app)',
                        color: review?.decision === 'rejected' ? '#030712' : 'var(--color-danger)',
                        border: '1px solid var(--color-danger-border)',
                      }}
                    >
                      ✕ Reject Action
                    </button>

                    <button
                      type="button"
                      onClick={() => handleDecision(rec.recommendation_id, 'more_evidence_needed')}
                      style={{
                        padding: '4px 10px',
                        fontSize: '11px',
                        fontWeight: 600,
                        borderRadius: 'var(--radius-sm)',
                        backgroundColor: review?.decision === 'more_evidence_needed' ? 'var(--color-warning)' : 'var(--bg-app)',
                        color: review?.decision === 'more_evidence_needed' ? '#030712' : 'var(--color-warning)',
                        border: '1px solid var(--color-warning-border)',
                      }}
                    >
                      ? Request More Evidence
                    </button>
                  </div>
                </div>

                {/* Review Log if Decision Made */}
                {review && (
                  <div style={{
                    fontSize: '11px',
                    color: 'var(--text-secondary)',
                    backgroundColor: 'var(--bg-app)',
                    padding: '6px 10px',
                    borderRadius: 'var(--radius-sm)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: '6px',
                  }}>
                    <span>
                      Logged by <strong>{review.reviewer}</strong> at {review.timestamp}
                    </span>
                    {!isCommenting && !review.comments && (
                      <button
                        type="button"
                        onClick={() => {
                          setActiveCommentId(rec.recommendation_id);
                          setCommentText(review.comments || '');
                        }}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: 'var(--color-primary)',
                          fontSize: '11px',
                          textDecoration: 'underline',
                          padding: 0,
                        }}
                      >
                        + Add Review Note
                      </button>
                    )}
                  </div>
                )}

                {/* Comment / Note Box */}
                {isCommenting && (
                  <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                    <input
                      type="text"
                      placeholder="Add compliance or authorization comments..."
                      value={commentText}
                      onChange={(e) => setCommentText(e.target.value)}
                      style={{
                        flex: 1,
                        backgroundColor: 'var(--bg-app)',
                        border: '1px solid var(--border-default)',
                        borderRadius: 'var(--radius-sm)',
                        padding: '4px 8px',
                        fontSize: '12px',
                        color: 'var(--text-primary)',
                        outline: 'none',
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => handleSaveComment(rec.recommendation_id)}
                      style={{
                        backgroundColor: 'var(--color-primary)',
                        color: '#030712',
                        borderRadius: 'var(--radius-sm)',
                        padding: '4px 10px',
                        fontSize: '11px',
                        fontWeight: 600,
                      }}
                    >
                      Save
                    </button>
                  </div>
                )}

                {review?.comments && !isCommenting && (
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontStyle: 'italic', paddingLeft: '6px' }}>
                    &ldquo;{review.comments}&rdquo;
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
