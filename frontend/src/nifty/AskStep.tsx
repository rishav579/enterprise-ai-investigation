import React from 'react';
import { Play, MessageCircleQuestion } from 'lucide-react';

interface AskStepProps {
  question: string;
  onChange: (q: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
}

export const AskStep: React.FC<AskStepProps> = ({ question, onChange, onSubmit, isLoading }) => {
  const valid = question.trim().length >= 5;
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (valid && !isLoading) onSubmit();
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
        gap: '12px',
      }}
    >
      <h2 style={{ fontSize: '15px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
        <MessageCircleQuestion size={16} color="var(--color-primary)" />
        ASK — State the research question
      </h2>
      <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
        Ask about buying NIFTY after a sharp fall. The next step proposes locked assumptions — nothing is
        computed from market data yet.
      </p>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{ position: 'relative' }}>
          <textarea
            aria-label="Research question"
            value={question}
            onChange={(e) => onChange(e.target.value)}
            disabled={isLoading}
            rows={3}
            placeholder="e.g. Does buying NIFTY after a sharp fall work?"
            style={{
              width: '100%',
              backgroundColor: 'var(--bg-app)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)',
              padding: '12px 14px',
              color: 'var(--text-primary)',
              fontFamily: 'var(--font-sans)',
              fontSize: '14px',
              lineHeight: '1.5',
              resize: 'vertical',
              outline: 'none',
            }}
          />
          <div
            style={{
              position: 'absolute',
              bottom: '8px',
              right: '12px',
              fontSize: '11px',
              color: question.trim().length < 5 ? 'var(--color-danger)' : 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {question.trim().length}/500 chars
          </div>
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            type="submit"
            disabled={!valid || isLoading}
            style={{
              backgroundColor: valid && !isLoading ? 'var(--color-primary)' : 'var(--bg-surface-hover)',
              color: valid && !isLoading ? '#030712' : 'var(--text-muted)',
              borderRadius: 'var(--radius-md)',
              padding: '8px 20px',
              fontSize: '13px',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <Play size={15} fill="currentColor" />
            {isLoading ? 'Interpreting…' : 'Clarify assumptions'}
          </button>
        </div>
      </form>
    </div>
  );
};
