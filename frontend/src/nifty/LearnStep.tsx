import React from 'react';
import { BookOpenCheck, RotateCcw } from 'lucide-react';
import type { NiftyExplainResponse, NiftyRunResponse } from './types';

interface LearnStepProps {
  run: NiftyRunResponse;
  explanation: NiftyExplainResponse;
  onRestart: () => void;
  onBack: () => void;
}

export const LearnStep: React.FC<LearnStepProps> = ({ run, explanation, onRestart, onBack }) => {
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
        <h2 style={{ fontSize: '15px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <BookOpenCheck size={16} color="var(--color-success)" />
          LEARN — Grounded summary (deterministic, advice-free)
        </h2>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          Derived only from the TEST metrics above ({run.signals_detected} signal(s), {run.primary.trade_count}{' '}
          primary trade(s), {run.experiment.sharp_fall_threshold_pct}% threshold, {run.experiment.cost_bps} bps
          cost). Synthetic mock data — historical observation, not guidance about future markets.
        </p>

        <section
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '14px 16px',
          }}
        >
          <h3 style={{ fontSize: '13px', fontWeight: 700, marginBottom: '6px' }}>What the data shows</h3>
          <p style={{ fontSize: '13px', color: 'var(--text-primary)', whiteSpace: 'pre-wrap' }}>
            {explanation.what_data_shows}
          </p>
        </section>

        <section
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '14px 16px',
          }}
        >
          <h3 style={{ fontSize: '13px', fontWeight: 700, marginBottom: '6px' }}>What we conclude</h3>
          <p style={{ fontSize: '13px', color: 'var(--text-primary)', whiteSpace: 'pre-wrap' }}>
            {explanation.what_we_conclude}
          </p>
        </section>

        <section
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '14px 16px',
          }}
        >
          <h3 style={{ fontSize: '13px', fontWeight: 700, marginBottom: '6px' }}>What to investigate next</h3>
          <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '13px', color: 'var(--text-secondary)' }}>
            {explanation.what_to_investigate_next.map((item) => (
              <li key={item} style={{ marginBottom: '4px' }}>{item}</li>
            ))}
          </ul>
        </section>
      </div>

      <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
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
          Back to TEST
        </button>
        <button
          type="button"
          onClick={onRestart}
          style={{
            backgroundColor: 'var(--bg-surface)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-md)',
            padding: '8px 16px',
            fontSize: '13px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <RotateCcw size={14} />
          Start a new question
        </button>
      </div>
    </div>
  );
};
