import React from 'react';
import { Search, Database, ShieldAlert, Sparkles } from 'lucide-react';
import type { ScenarioItem } from '../api/types';

interface EmptyStateProps {
  onSelectScenario: (scenario: ScenarioItem) => void;
  scenarios: ScenarioItem[];
}

export const EmptyState: React.FC<EmptyStateProps> = ({ onSelectScenario, scenarios }) => {
  const primaryScenario = scenarios.find((s) => s.id === 'scenario_A_churn') || scenarios[0];

  return (
    <div style={{
      backgroundColor: 'var(--bg-panel)',
      border: '1px dashed var(--border-default)',
      borderRadius: 'var(--radius-lg)',
      padding: '48px 24px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      textAlign: 'center',
      gap: '16px',
      maxWidth: '720px',
      margin: '20px auto',
    }}>
      <div style={{
        width: '56px',
        height: '56px',
        borderRadius: '50%',
        backgroundColor: 'var(--color-primary-bg)',
        border: '1px solid var(--color-primary-border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--color-primary)',
      }}>
        <Search size={28} />
      </div>

      <div>
        <h3 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px' }}>
          No Active Investigation Dispatched
        </h3>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', maxWidth: '480px', lineHeight: '1.6' }}>
          Launch a data-driven investigation to correlate relational telemetry, internal postmortems, and software release timelines.
        </p>
      </div>

      {primaryScenario && (
        <button
          type="button"
          onClick={() => onSelectScenario(primaryScenario)}
          style={{
            backgroundColor: 'var(--color-primary)',
            color: '#030712',
            border: 'none',
            borderRadius: 'var(--radius-md)',
            padding: '10px 20px',
            fontSize: '13px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            boxShadow: 'var(--shadow-sm)',
            marginTop: '8px',
          }}
        >
          <Sparkles size={16} />
          Load Primary Churn Scenario Demo
        </button>
      )}

      {/* Quick Feature highlights */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '12px',
        width: '100%',
        marginTop: '16px',
        textAlign: 'left',
      }}>
        <div style={{
          backgroundColor: 'var(--bg-surface)',
          padding: '12px',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
        }}>
          <Database size={16} color="var(--color-primary)" style={{ marginBottom: '4px' }} />
          <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
            Multi-Table SQL Analysis
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            6 tables: churn, subscriptions, billing failures, support SLA & release events.
          </div>
        </div>

        <div style={{
          backgroundColor: 'var(--bg-surface)',
          padding: '12px',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
        }}>
          <ShieldAlert size={16} color="var(--color-warning)" style={{ marginBottom: '4px' }} />
          <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
            100% Verified Citations
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Strict validation rejects fabricated claims or missing evidence references.
          </div>
        </div>
      </div>
    </div>
  );
};
