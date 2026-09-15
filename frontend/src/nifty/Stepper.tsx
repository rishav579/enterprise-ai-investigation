import React from 'react';
import { Check } from 'lucide-react';
import type { NiftyStage } from './types';
import { NIFTY_STAGES } from './types';

const STAGE_META: Record<NiftyStage, { title: string; hint: string }> = {
  ask: { title: 'ASK', hint: 'Research question' },
  clarify: { title: 'CLARIFY', hint: 'Ambiguities + assumptions' },
  define: { title: 'DEFINE', hint: 'Lock experiment' },
  test: { title: 'TEST', hint: 'Deterministic run' },
  learn: { title: 'LEARN', hint: 'Grounded summary' },
};

interface StepperProps {
  current: NiftyStage;
  reached: NiftyStage;
  onNavigate: (stage: NiftyStage) => void;
}

export const Stepper: React.FC<StepperProps> = ({ current, reached, onNavigate }) => {
  const reachedIdx = NIFTY_STAGES.indexOf(reached);
  return (
    <ol
      aria-label="NIFTY research progress"
      style={{ display: 'flex', gap: '8px', listStyle: 'none', padding: 0, margin: 0, flexWrap: 'wrap' }}
    >
      {NIFTY_STAGES.map((stage, idx) => {
        const isDone = idx < NIFTY_STAGES.indexOf(current) || idx <= reachedIdx && stage !== current && idx < NIFTY_STAGES.indexOf(current);
        const completed = idx < NIFTY_STAGES.indexOf(current);
        const isCurrent = stage === current;
        const navigable = idx <= reachedIdx;
        return (
          <li key={stage} style={{ flex: '1 1 120px', minWidth: '120px' }}>
            <button
              type="button"
              disabled={!navigable}
              onClick={() => onNavigate(stage)}
              aria-current={isCurrent ? 'step' : undefined}
              style={{
                width: '100%',
                textAlign: 'left',
                backgroundColor: isCurrent ? 'var(--color-primary-bg)' : 'var(--bg-surface)',
                border: isCurrent ? '1px solid var(--color-primary-border)' : '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '8px 12px',
                color: isCurrent ? 'var(--color-primary)' : 'var(--text-secondary)',
                opacity: navigable ? 1 : 0.55,
              }}
            >
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: 700 }}>
                <span
                  style={{
                    width: '20px',
                    height: '20px',
                    borderRadius: '9999px',
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '11px',
                    backgroundColor: completed ? 'var(--color-success-bg)' : isCurrent ? 'var(--color-primary)' : 'var(--bg-app)',
                    color: completed ? 'var(--color-success)' : isCurrent ? '#030712' : 'var(--text-muted)',
                    border: '1px solid var(--border-default)',
                  }}
                >
                  {completed || isDone ? <Check size={12} /> : idx + 1}
                </span>
                {STAGE_META[stage].title}
              </span>
              <span style={{ display: 'block', fontSize: '11px', marginTop: '2px', color: 'var(--text-muted)' }}>
                {STAGE_META[stage].hint}
              </span>
            </button>
          </li>
        );
      })}
    </ol>
  );
};
