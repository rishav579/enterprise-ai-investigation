import React from 'react';
import { ShieldCheck, Database, Cpu, Activity, RefreshCw, AlertCircle } from 'lucide-react';
import type { BackendHealthResponse } from '../api/types';

interface HeaderProps {
  health: BackendHealthResponse | null;
  healthLoading: boolean;
  onRefreshHealth: () => void;
  investigationId?: string | null;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  healthLoading,
  onRefreshHealth,
  investigationId,
}) => {
  const isOnline = health?.status === 'ok';

  return (
    <header style={{
      backgroundColor: 'var(--bg-panel)',
      borderBottom: '1px solid var(--border-default)',
      padding: '12px 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '16px',
      flexWrap: 'wrap',
    }}>
      {/* Brand & Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: 'var(--radius-md)',
          backgroundColor: 'var(--color-primary-bg)',
          border: '1px solid var(--color-primary-border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--color-primary)',
        }}>
          <ShieldCheck size={22} />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h1 style={{ fontSize: '16px', fontWeight: 700, letterSpacing: '-0.01em' }}>
              Enterprise AI Investigation & Decision System
            </h1>
            <span className="badge badge-info" style={{ fontSize: '10px' }}>
              v{health?.version || '0.1.0'}
            </span>
          </div>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Deterministic Data Investigation, Grounded Synthesis & Auditability Console
          </p>
        </div>
      </div>

      {/* Security & System Badges */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
        {investigationId && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: 'var(--bg-surface)',
            padding: '4px 10px',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-default)',
            fontSize: '12px',
            fontFamily: 'var(--font-mono)',
          }}>
            <span style={{ color: 'var(--text-muted)' }}>RUN:</span>
            <span style={{ color: 'var(--color-primary)', fontWeight: 600 }}>{investigationId}</span>
          </div>
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="badge badge-neutral" title="Read-Only SQL AST Sandbox Active">
            <Database size={11} /> AST SQL Guard
          </span>
          <span className="badge badge-neutral" title="Zero-Fabrication Synthesis Constraint Active">
            <Cpu size={11} /> Zero-Fabrication
          </span>
        </div>

        {/* Backend Status Indicator */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '4px 10px',
          borderRadius: 'var(--radius-sm)',
          backgroundColor: isOnline ? 'var(--color-success-bg)' : 'var(--color-danger-bg)',
          border: `1px solid ${isOnline ? 'var(--color-success-border)' : 'var(--color-danger-border)'}`,
        }}>
          {isOnline ? (
            <Activity size={14} color="var(--color-success)" />
          ) : (
            <AlertCircle size={14} color="var(--color-danger)" />
          )}
          <span style={{
            fontSize: '12px',
            fontWeight: 600,
            color: isOnline ? 'var(--color-success)' : 'var(--color-danger)',
          }}>
            {healthLoading ? 'Checking...' : isOnline ? 'Backend Online' : 'Backend Offline'}
          </span>
          <button
            onClick={onRefreshHealth}
            title="Refresh backend status"
            aria-label="Refresh backend status"
            style={{
              background: 'transparent',
              border: 'none',
              color: isOnline ? 'var(--color-success)' : 'var(--color-danger)',
              display: 'flex',
              alignItems: 'center',
              padding: '2px',
            }}
          >
            <RefreshCw size={12} className={healthLoading ? 'spin' : ''} />
          </button>
        </div>
      </div>
    </header>
  );
};
