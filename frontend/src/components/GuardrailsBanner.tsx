import React from 'react';
import { ShieldCheck, Database, FileLock, Link2, CheckCircle2 } from 'lucide-react';

export const GuardrailsBanner: React.FC = () => {
  return (
    <div style={{
      backgroundColor: 'rgba(15, 23, 42, 0.6)',
      border: '1px solid var(--border-default)',
      borderRadius: 'var(--radius-lg)',
      padding: '14px 20px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '16px',
      flexWrap: 'wrap',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <ShieldCheck size={18} color="var(--color-success)" />
        <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
          Active Enterprise Safety & Integrity Guardrails:
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px', color: 'var(--text-secondary)' }}>
          <Database size={13} color="var(--color-primary)" />
          <span>AST Read-Only SQL</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px', color: 'var(--text-secondary)' }}>
          <FileLock size={13} color="var(--color-info)" />
          <span>Path Traversal Guard</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px', color: 'var(--text-secondary)' }}>
          <Link2 size={13} color="var(--color-warning)" />
          <span>Cross-Run Isolation</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px', color: 'var(--text-secondary)' }}>
          <CheckCircle2 size={13} color="var(--color-success)" />
          <span>SHA-256 Evidence Hashing</span>
        </div>
      </div>
    </div>
  );
};
