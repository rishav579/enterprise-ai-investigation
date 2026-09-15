import React from 'react';
import { ArrowRight, Info } from 'lucide-react';
import type { NiftyInterpretResponse } from './types';

interface ClarifyStepProps {
  interpretation: NiftyInterpretResponse;
  onAccept: () => void;
  onBack: () => void;
}

export const ClarifyStep: React.FC<ClarifyStepProps> = ({ interpretation, onAccept, onBack }) => {
  const sa = interpretation.suggested_assumptions;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div
        style={{
          backgroundColor: 'var(--bg-panel)',
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-lg)',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <h2 style={{ fontSize: '15px', fontWeight: 600 }}>CLARIFY — What needs pinning down</h2>
          <span className={interpretation.recognized ? 'badge badge-success' : 'badge badge-warning'}>
            {interpretation.recognized ? 'Recognized prototype question' : 'Showing MVP defaults'}
          </span>
        </div>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{interpretation.note}</p>
        <p
          style={{
            fontSize: '12px',
            color: 'var(--text-muted)',
            display: 'flex',
            gap: '6px',
            alignItems: 'flex-start',
          }}
        >
          <Info size={14} style={{ flexShrink: 0, marginTop: '2px' }} />
          No market data has been touched. No results exist yet — these are proposed definitions only.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px' }}>
          {interpretation.ambiguities.map((a) => (
            <div
              key={a.field}
              style={{
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '12px 14px',
              }}
            >
              <div style={{ fontSize: '13px', fontWeight: 600 }}>{a.label}</div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                {a.why_it_matters}
              </div>
              {interpretation.explanations[a.field] && (
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>
                  {interpretation.explanations[a.field]}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div
        style={{
          backgroundColor: 'var(--bg-panel)',
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-lg)',
          padding: '20px',
        }}
      >
        <h3 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>Suggested locked assumptions</h3>
        <dl
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '8px 16px',
            fontSize: '12px',
          }}
        >
          <div><dt style={{ color: 'var(--text-muted)' }}>Sharp-fall threshold</dt><dd className="font-mono">{sa.sharp_fall_threshold_pct}% single-day fall</dd></div>
          <div><dt style={{ color: 'var(--text-muted)' }}>“Work” means</dt><dd className="font-mono">{sa.work_definition} (positive average net return)</dd></div>
          <div><dt style={{ color: 'var(--text-muted)' }}>Primary holding</dt><dd className="font-mono">{sa.holding_days_primary} trading days</dd></div>
          <div><dt style={{ color: 'var(--text-muted)' }}>Sensitivity</dt><dd className="font-mono">{sa.holding_days_sensitivity.join(', ')} trading days</dd></div>
          <div><dt style={{ color: 'var(--text-muted)' }}>Entry</dt><dd className="font-mono">{sa.entry_timing} (no look-ahead)</dd></div>
          <div><dt style={{ color: 'var(--text-muted)' }}>Cost</dt><dd className="font-mono">{sa.cost_bps} bps round-trip</dd></div>
          <div><dt style={{ color: 'var(--text-muted)' }}>Overlapping positions</dt><dd className="font-mono">{sa.allow_overlapping_positions ? 'allowed' : 'not allowed'}</dd></div>
          <div><dt style={{ color: 'var(--text-muted)' }}>Test period</dt><dd className="font-mono">{sa.test_period_start} → {sa.test_period_end}</dd></div>
        </dl>
        <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '16px', flexWrap: 'wrap' }}>
          <button
            type="button"
            onClick={onBack}
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
            Back to ASK
          </button>
          <button
            type="button"
            onClick={onAccept}
            style={{
              backgroundColor: 'var(--color-primary)',
              color: '#030712',
              borderRadius: 'var(--radius-md)',
              padding: '8px 20px',
              fontSize: '13px',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            Accept & define experiment
            <ArrowRight size={15} />
          </button>
        </div>
      </div>
    </div>
  );
};
