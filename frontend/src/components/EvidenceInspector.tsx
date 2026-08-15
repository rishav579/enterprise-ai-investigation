import React, { useState } from 'react';
import {
  X,
  Copy,
  Check,
  Hash,
  Code,
  Table as TableIcon,
} from 'lucide-react';
import type { EvidenceItem } from '../api/types';

interface EvidenceInspectorProps {
  evidenceItem: EvidenceItem | null;
  onClose: () => void;
}

export const EvidenceInspector: React.FC<EvidenceInspectorProps> = ({
  evidenceItem,
  onClose,
}) => {
  const [copiedHash, setCopiedHash] = useState(false);
  const [activeTab, setActiveTab] = useState<'formatted' | 'raw'>('formatted');

  if (!evidenceItem) {
    return null;
  }

  const handleCopyHash = () => {
    navigator.clipboard.writeText(evidenceItem.content_hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const renderContent = () => {
    const { evidence_type, content } = evidenceItem;

    if (activeTab === 'raw') {
      return (
        <pre style={{
          backgroundColor: 'var(--bg-app)',
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-md)',
          padding: '14px',
          fontSize: '11px',
          fontFamily: 'var(--font-mono)',
          color: '#bae6fd',
          overflowX: 'auto',
          maxHeight: '400px',
        }}>
          {JSON.stringify(content, null, 2)}
        </pre>
      );
    }

    // 1. SQL Result Viewer
    if (evidence_type === 'sql_result') {
      const rows = Array.isArray(content.rows) ? (content.rows as Array<Record<string, unknown>>) : [];
      const columns = Array.isArray(content.columns)
        ? (content.columns as string[])
        : rows.length > 0
        ? Object.keys(rows[0])
        : [];
      const queryRef = typeof content.query_reference === 'string' ? content.query_reference : '';
      const rowCount = typeof content.row_count === 'number' ? content.row_count : rows.length;

      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* Query Reference */}
          {queryRef && (
            <div>
              <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>
                Executed Analytical SQL Query:
              </div>
              <pre style={{
                backgroundColor: 'var(--bg-app)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '10px 12px',
                color: '#7dd3fc',
                fontSize: '11px',
                fontFamily: 'var(--font-mono)',
                overflowX: 'auto',
                whiteSpace: 'pre-wrap',
              }}>
                {queryRef}
              </pre>
            </div>
          )}

          {/* Table Data */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Result Set ({rowCount} rows {content.truncated ? '• Truncated' : ''})
              </span>
            </div>

            {rows.length === 0 ? (
              <div style={{
                padding: '20px',
                textAlign: 'center',
                backgroundColor: 'var(--bg-app)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-muted)',
                fontSize: '12px',
              }}>
                Query returned 0 rows.
              </div>
            ) : (
              <div style={{
                overflowX: 'auto',
                maxHeight: '300px',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
              }}>
                <table>
                  <thead>
                    <tr>
                      {columns.map((col) => (
                        <th key={col}>{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row, rIdx) => (
                      <tr key={rIdx}>
                        {columns.map((col) => (
                          <td key={col} style={{ fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
                            {row[col] !== null && row[col] !== undefined
                              ? String(row[col])
                              : <span style={{ color: 'var(--text-muted)' }}>NULL</span>}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      );
    }

    // 2. Document Text Viewer
    if (evidence_type === 'document_text') {
      const docId = typeof content.document_id === 'string' ? content.document_id : '';
      const fullText = typeof content.full_text === 'string' ? content.full_text : '';

      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Document ID: <strong>{docId}</strong> ({typeof content.char_count === 'number' ? content.char_count : fullText.length} characters)
          </div>
          <pre style={{
            backgroundColor: 'var(--bg-app)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-md)',
            padding: '14px',
            color: 'var(--text-primary)',
            fontSize: '12px',
            fontFamily: 'var(--font-mono)',
            whiteSpace: 'pre-wrap',
            maxHeight: '350px',
            overflowY: 'auto',
          }}>
            {fullText}
          </pre>
        </div>
      );
    }

    // 3. Document Match Excerpt
    if (evidence_type === 'document_match') {
      const docId = typeof content.document_id === 'string' ? content.document_id : '';
      const lineNum = typeof content.line_number === 'number' ? content.line_number : 1;
      const excerpt = typeof content.excerpt === 'string' ? content.excerpt : '';

      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Document: <strong>{docId}</strong> (Line {lineNum})
          </div>

          <div style={{
            backgroundColor: 'var(--bg-app)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-md)',
            padding: '12px',
            fontFamily: 'var(--font-mono)',
            fontSize: '12px',
          }}>
            {Boolean(content.context_before) && (
              <div style={{ color: 'var(--text-muted)' }}>{String(content.context_before)}</div>
            )}
            <div style={{ color: '#38bdf8', fontWeight: 600, backgroundColor: 'rgba(56, 189, 248, 0.1)', padding: '2px 4px', borderRadius: '2px' }}>
              &gt; {excerpt}
            </div>
            {Boolean(content.context_after) && (
              <div style={{ color: 'var(--text-muted)' }}>{String(content.context_after)}</div>
            )}
          </div>
        </div>
      );
    }

    // 4. Document Listing
    if (evidence_type === 'document_listing') {
      const docs = Array.isArray(content.documents) ? (content.documents as Array<{ id: string; title: string; size_bytes?: number }>) : [];
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Total Available Documents: {docs.length}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {docs.map((doc, idx) => (
              <div
                key={idx}
                style={{
                  backgroundColor: 'var(--bg-app)',
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: '12px',
                }}
              >
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{doc.title || doc.id}</span>
                <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{doc.size_bytes ? `${doc.size_bytes} B` : ''}</span>
              </div>
            ))}
          </div>
        </div>
      );
    }

    // Fallback: JSON Dump
    return (
      <pre style={{
        backgroundColor: 'var(--bg-app)',
        padding: '12px',
        borderRadius: 'var(--radius-md)',
        fontSize: '11px',
        fontFamily: 'var(--font-mono)',
        color: '#bae6fd',
        overflowX: 'auto',
      }}>
        {JSON.stringify(content, null, 2)}
      </pre>
    );
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.75)',
      display: 'flex',
      justifyContent: 'flex-end',
      zIndex: 1000,
      backdropFilter: 'blur(3px)',
    }}>
      <div style={{
        width: '100%',
        maxWidth: '680px',
        height: '100%',
        backgroundColor: 'var(--bg-panel)',
        borderLeft: '1px solid var(--border-default)',
        boxShadow: 'var(--shadow-drawer)',
        display: 'flex',
        flexDirection: 'column',
        overflowY: 'auto',
        padding: '24px',
        gap: '20px',
      }}>
        {/* Header Row */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '16px',
                fontWeight: 700,
                color: 'var(--color-primary)',
              }}>
                {evidenceItem.evidence_id}
              </span>
              <span className="badge badge-info">
                {evidenceItem.evidence_type}
              </span>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              Produced by <strong>{evidenceItem.tool_name}</strong> in step <strong>{evidenceItem.step_id}</strong>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-default)',
              color: 'var(--text-secondary)',
              borderRadius: 'var(--radius-md)',
              padding: '6px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
            aria-label="Close evidence inspector"
          >
            <X size={18} />
          </button>
        </div>

        {/* Provenance Metadata Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '8px',
          backgroundColor: 'var(--bg-surface)',
          padding: '12px',
          borderRadius: 'var(--radius-md)',
          fontSize: '11px',
          border: '1px solid var(--border-subtle)',
        }}>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Investigation Run:</span>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
              {evidenceItem.investigation_run_id}
            </div>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Collection Order:</span>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
              #{evidenceItem.sequence_number}
            </div>
          </div>
          <div style={{ gridColumn: 'span 2' }}>
            <span style={{ color: 'var(--text-muted)' }}>Source Reference:</span>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
              {evidenceItem.source_reference}
            </div>
          </div>
        </div>

        {/* Cryptographic Hash Badge (SHA-256) */}
        <div style={{
          backgroundColor: 'var(--bg-app)',
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-md)',
          padding: '10px 12px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '8px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
            <Hash size={14} color="var(--color-success)" />
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--color-success)', letterSpacing: '0.04em' }}>
                SHA-256 CONTENT INTEGRITY FINGERPRINT
              </div>
              <div style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                color: 'var(--text-primary)',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}>
                {evidenceItem.content_hash}
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={handleCopyHash}
            style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '6px 10px',
              fontSize: '11px',
              color: 'var(--text-secondary)',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              flexShrink: 0,
            }}
          >
            {copiedHash ? <Check size={12} color="var(--color-success)" /> : <Copy size={12} />}
            {copiedHash ? 'Copied' : 'Copy'}
          </button>
        </div>

        {/* Tab Toggle: Formatted vs Raw */}
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border-default)', gap: '16px' }}>
          <button
            type="button"
            onClick={() => setActiveTab('formatted')}
            style={{
              background: 'none',
              border: 'none',
              borderBottom: activeTab === 'formatted' ? '2px solid var(--color-primary)' : '2px solid transparent',
              color: activeTab === 'formatted' ? 'var(--color-primary)' : 'var(--text-secondary)',
              padding: '8px 4px',
              fontSize: '12px',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <TableIcon size={14} />
            Structured View
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('raw')}
            style={{
              background: 'none',
              border: 'none',
              borderBottom: activeTab === 'raw' ? '2px solid var(--color-primary)' : '2px solid transparent',
              color: activeTab === 'raw' ? 'var(--color-primary)' : 'var(--text-secondary)',
              padding: '8px 4px',
              fontSize: '12px',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <Code size={14} />
            Raw JSON Content
          </button>
        </div>

        {/* Evidence Render Area */}
        <div style={{ flex: 1 }}>
          {renderContent()}
        </div>
      </div>
    </div>
  );
};
