import React, { useState } from 'react';
import { FlaskConical, Lock } from 'lucide-react';
import type { NiftyExperimentIntent } from './types';
import { NIFTY_SENSITIVITY_HOLDING_DAYS, NIFTY_PRIMARY_HOLDING_DAYS } from './types';

interface DefineStepProps {
  draft: NiftyExperimentIntent;
  onChange: (next: NiftyExperimentIntent) => void;
  onValidateAndRun: () => void;
  onBack: () => void;
  isLoading: boolean;
  serverError: string | null;
}

function validateLocal(draft: NiftyExperimentIntent): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!(draft.sharp_fall_threshold_pct < 0)) {
    errors.sharp_fall_threshold_pct = 'Threshold must be negative (e.g. -3.0).';
  } else if (draft.sharp_fall_threshold_pct < -50) {
    errors.sharp_fall_threshold_pct = 'Threshold is unreasonably large (min -50%).';
  }
  if (draft.cost_bps < 0) {
    errors.cost_bps = 'Cost cannot be negative.';
  } else if (draft.cost_bps > 200) {
    errors.cost_bps = 'Cost is unreasonably large (max 200 bps).';
  }
  if (!draft.test_period_start || !draft.test_period_end) {
    errors.test_period = 'Both start and end dates are required.';
  } else if (draft.test_period_end <= draft.test_period_start) {
    errors.test_period = 'End date must be after start date.';
  }
  return errors;
}

const inputStyle: React.CSSProperties = {
  width: '100%',
  backgroundColor: 'var(--bg-app)',
  border: '1px solid var(--border-default)',
  borderRadius: 'var(--radius-md)',
  padding: '8px 12px',
  color: 'var(--text-primary)',
  fontFamily: 'var(--font-mono)',
  fontSize: '13px',
  outline: 'none',
};

const labelStyle: React.CSSProperties = {
  fontSize: '12px',
  fontWeight: 600,
  color: 'var(--text-secondary)',
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
};

export const DefineStep: React.FC<DefineStepProps> = ({
  draft,
  onChange,
  onValidateAndRun,
  onBack,
  isLoading,
  serverError,
}) => {
  const [touched, setTouched] = useState(false);
  const errors = validateLocal(draft);
  const hasErrors = Object.keys(errors).length > 0;

  const set = (patch: Partial<NiftyExperimentIntent>) => {
    setTouched(true);
    onChange({ ...draft, ...patch });
  };

  return (
    <div
      style={{
        backgroundColor: 'var(--bg-panel)',
        border: '1px solid var(--border-default)',
        borderRadius: 'var(--radius-lg)',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
      }}
    >
      <h2 style={{ fontSize: '15px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
        <FlaskConical size={16} color="var(--color-primary)" />
        DEFINE — Lock the experiment before seeing results
      </h2>
      <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
        Pre-commit the definitions. Validating locks the assumptions via{' '}
        <span className="font-mono">POST /api/experiment</span> — it never runs the backtest.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
        <label style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <span style={labelStyle}>Sharp-fall threshold (% daily fall)</span>
          <input
            aria-label="Sharp-fall threshold percent"
            type="number"
            step="0.1"
            value={draft.sharp_fall_threshold_pct}
            onChange={(e) => set({ sharp_fall_threshold_pct: Number(e.target.value) })}
            disabled={isLoading}
            style={inputStyle}
          />
          {touched && errors.sharp_fall_threshold_pct && (
            <span style={{ fontSize: '11px', color: 'var(--color-danger)' }}>{errors.sharp_fall_threshold_pct}</span>
          )}
        </label>

        <label style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <span style={labelStyle}>Round-trip cost (basis points)</span>
          <input
            aria-label="Round-trip cost in basis points"
            type="number"
            step="0.5"
            min={0}
            value={draft.cost_bps}
            onChange={(e) => set({ cost_bps: Number(e.target.value) })}
            disabled={isLoading}
            style={inputStyle}
          />
          {touched && errors.cost_bps && (
            <span style={{ fontSize: '11px', color: 'var(--color-danger)' }}>{errors.cost_bps}</span>
          )}
        </label>

        <label style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <span style={labelStyle}>Test period start</span>
          <input
            aria-label="Test period start"
            type="date"
            value={draft.test_period_start}
            onChange={(e) => set({ test_period_start: e.target.value })}
            disabled={isLoading}
            style={inputStyle}
          />
        </label>

        <label style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <span style={labelStyle}>Test period end</span>
          <input
            aria-label="Test period end"
            type="date"
            value={draft.test_period_end}
            onChange={(e) => set({ test_period_end: e.target.value })}
            disabled={isLoading}
            style={inputStyle}
          />
        </label>
      </div>
      {touched && errors.test_period && (
        <span style={{ fontSize: '11px', color: 'var(--color-danger)' }}>{errors.test_period}</span>
      )}

      <div
        style={{
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '12px 14px',
          fontSize: '12px',
          color: 'var(--text-secondary)',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
        }}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600, color: 'var(--text-primary)' }}>
          <Lock size={13} /> Locked by the MVP prototype (not editable)
        </span>
        <span className="font-mono">
          market NIFTY50 · “work” = avg_return · primary hold {NIFTY_PRIMARY_HOLDING_DAYS}d · sensitivity{' '}
          {NIFTY_SENSITIVITY_HOLDING_DAYS.join(', ')}d · entry next_open · no overlapping positions
        </span>
      </div>

      <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
        <button
          type="button"
          onClick={onBack}
          disabled={isLoading}
          style={{
            backgroundColor: 'var(--bg-surface)',
            color: 'var(--text-secondary)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-md)',
            padding: '8px 16px',
            fontSize: '13px',
            fontWeight: 500,
          }}
        >
          Back to CLARIFY
        </button>
        <button
          type="button"
          onClick={() => {
            setTouched(true);
            if (!hasErrors) onValidateAndRun();
          }}
          disabled={isLoading || (touched && hasErrors)}
          title={hasErrors ? 'Fix validation issues first' : 'Validate then run the deterministic backtest'}
          style={{
            backgroundColor: 'var(--color-primary)',
            color: '#030712',
            borderRadius: 'var(--radius-md)',
            padding: '8px 20px',
            fontSize: '13px',
            fontWeight: 600,
          }}
        >
          {isLoading ? 'Validating…' : 'Lock & run TEST'}
        </button>
      </div>
      {serverError && (
        <div
          role="alert"
          style={{
            backgroundColor: 'var(--color-danger-bg)',
            border: '1px solid var(--color-danger-border)',
            borderRadius: 'var(--radius-md)',
            padding: '10px 14px',
            fontSize: '12px',
            color: 'var(--color-danger)',
          }}
        >
          {serverError}
        </div>
      )}
    </div>
  );
};
