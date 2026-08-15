import React, { useState } from 'react';
import {
  History,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';
import type { AuditEvent, AuditEventType } from '../api/types';

interface AuditTrailStreamProps {
  auditEvents: AuditEvent[];
}

export const AuditTrailStream: React.FC<AuditTrailStreamProps> = ({ auditEvents }) => {
  const [expandedEventIds, setExpandedEventIds] = useState<Set<string>>(new Set());
  const [filterType, setFilterType] = useState<string>('all');

  const toggleEvent = (eventId: string) => {
    setExpandedEventIds((prev) => {
      const next = new Set(prev);
      if (next.has(eventId)) {
        next.delete(eventId);
      } else {
        next.add(eventId);
      }
      return next;
    });
  };

  const renderEventBadge = (eventType: AuditEventType) => {
    switch (eventType) {
      case 'investigation_started':
      case 'investigation_completed':
        return <span className="badge badge-info">{eventType}</span>;
      case 'plan_created':
        return <span className="badge badge-primary">{eventType}</span>;
      case 'step_started':
        return <span className="badge badge-neutral">{eventType}</span>;
      case 'step_completed':
      case 'synthesis_validated':
        return <span className="badge badge-success">{eventType}</span>;
      case 'evidence_collected':
        return <span className="badge badge-primary" style={{ color: '#38bdf8' }}>{eventType}</span>;
      case 'step_failed':
      case 'investigation_failed':
      case 'synthesis_failed':
        return <span className="badge badge-danger">{eventType}</span>;
      case 'step_blocked':
      case 'investigation_partial':
        return <span className="badge badge-warning">{eventType}</span>;
      case 'synthesis_started':
      case 'synthesis_generated':
        return <span className="badge badge-info">{eventType}</span>;
      default:
        return <span className="badge badge-neutral">{eventType}</span>;
    }
  };

  const filteredEvents = auditEvents.filter((ev) => {
    if (filterType === 'all') return true;
    if (filterType === 'evidence') return ev.event_type === 'evidence_collected';
    if (filterType === 'synthesis') return ev.event_type.startsWith('synthesis');
    if (filterType === 'errors') return ev.event_type.includes('fail') || ev.event_type.includes('block');
    return true;
  });

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
            <History size={16} color="var(--color-primary)" />
            Immutable Audit Trail ({auditEvents.length} Events)
          </h2>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Sequential, tamper-evident record of all lifecycle transitions, tool executions, and validation checks.
          </p>
        </div>

        {/* Filter Controls */}
        <div style={{ display: 'flex', gap: '6px' }}>
          {['all', 'evidence', 'synthesis', 'errors'].map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setFilterType(f)}
              style={{
                fontSize: '11px',
                padding: '3px 8px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: filterType === f ? 'var(--color-primary-bg)' : 'var(--bg-surface)',
                color: filterType === f ? 'var(--color-primary)' : 'var(--text-secondary)',
                border: `1px solid ${filterType === f ? 'var(--color-primary-border)' : 'var(--border-subtle)'}`,
                textTransform: 'capitalize',
                fontWeight: 600,
              }}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Events Table / Stream */}
      {filteredEvents.length === 0 ? (
        <div style={{
          padding: '20px',
          textAlign: 'center',
          backgroundColor: 'var(--bg-surface)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--text-muted)',
          fontSize: '12px',
        }}>
          No audit events match the selected filter.
        </div>
      ) : (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
          maxHeight: '400px',
          overflowY: 'auto',
          paddingRight: '4px',
        }}>
          {filteredEvents.map((event) => {
            const isExpanded = expandedEventIds.has(event.event_id);
            const hasMetadata = event.metadata && Object.keys(event.metadata).length > 0;

            return (
              <div
                key={event.event_id}
                style={{
                  backgroundColor: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  overflow: 'hidden',
                  fontSize: '12px',
                }}
              >
                <div
                  onClick={() => hasMetadata && toggleEvent(event.event_id)}
                  style={{
                    padding: '8px 12px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: '10px',
                    cursor: hasMetadata ? 'pointer' : 'default',
                    userSelect: 'none',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0, flex: 1 }}>
                    {hasMetadata && (
                      <span style={{ color: 'var(--text-muted)' }}>
                        {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                      </span>
                    )}

                    <span style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '11px',
                      fontWeight: 700,
                      color: 'var(--text-muted)',
                      minWidth: '70px',
                    }}>
                      {event.event_id}
                    </span>

                    <div>{renderEventBadge(event.event_type)}</div>

                    {event.step_id && (
                      <span style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '11px',
                        color: 'var(--color-primary)',
                        backgroundColor: 'var(--bg-app)',
                        padding: '1px 5px',
                        borderRadius: 'var(--radius-sm)',
                      }}>
                        {event.step_id}
                      </span>
                    )}

                    {event.tool_name && (
                      <span style={{ color: 'var(--text-secondary)', fontSize: '11px' }}>
                        via {event.tool_name}
                      </span>
                    )}
                  </div>

                  {event.evidence_ids && event.evidence_ids.length > 0 && (
                    <div style={{ display: 'flex', gap: '4px', flexShrink: 0 }}>
                      {event.evidence_ids.map((eid) => (
                        <span
                          key={eid}
                          style={{
                            fontFamily: 'var(--font-mono)',
                            fontSize: '10px',
                            color: '#38bdf8',
                            backgroundColor: 'rgba(56, 189, 248, 0.1)',
                            padding: '1px 4px',
                            borderRadius: '2px',
                          }}
                        >
                          {eid}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Expanded Metadata */}
                {isExpanded && hasMetadata && (
                  <div style={{
                    padding: '8px 12px 10px 32px',
                    borderTop: '1px solid var(--border-subtle)',
                    backgroundColor: 'var(--bg-app)',
                  }}>
                    <pre style={{
                      fontSize: '11px',
                      color: 'var(--text-muted)',
                      fontFamily: 'var(--font-mono)',
                      whiteSpace: 'pre-wrap',
                    }}>
                      {JSON.stringify(event.metadata, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
