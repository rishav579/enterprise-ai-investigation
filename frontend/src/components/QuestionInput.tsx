import React from 'react';
import { Play, Sparkles, AlertTriangle, RefreshCw, HelpCircle } from 'lucide-react';
import type { ScenarioItem } from '../api/types';

interface QuestionInputProps {
  question: string;
  onChangeQuestion: (q: string) => void;
  onRunInvestigation: () => void;
  onReset: () => void;
  isLoading: boolean;
  scenarios: ScenarioItem[];
  selectedScenarioId: string;
  onSelectScenario: (scenario: ScenarioItem) => void;
  isBackendOnline: boolean;
}

export const QuestionInput: React.FC<QuestionInputProps> = ({
  question,
  onChangeQuestion,
  onRunInvestigation,
  onReset,
  isLoading,
  scenarios,
  selectedScenarioId,
  onSelectScenario,
  isBackendOnline,
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim().length >= 5 && !isLoading && isBackendOnline) {
      onRunInvestigation();
    }
  };

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
      {/* Title & Description */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
        <div>
          <h2 style={{ fontSize: '15px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={16} color="var(--color-primary)" />
            Investigation Query & Scenario Dispatch
          </h2>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Enter a business investigation question or load a deterministic golden benchmark scenario.
          </p>
        </div>

        {/* Quick Scenario Pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)' }}>
            PRESETS:
          </span>
          {scenarios.map((sc) => {
            const isSelected = selectedScenarioId === sc.id;
            const isAdversarial = sc.category === 'security_adversarial';
            const isInsufficient = sc.category === 'insufficient_evidence';

            return (
              <button
                key={sc.id}
                type="button"
                onClick={() => onSelectScenario(sc)}
                disabled={isLoading}
                style={{
                  fontSize: '11px',
                  fontWeight: 500,
                  padding: '4px 10px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: isSelected
                    ? 'var(--color-primary-bg)'
                    : 'var(--bg-surface)',
                  color: isSelected
                    ? 'var(--color-primary)'
                    : isAdversarial
                    ? 'var(--color-danger)'
                    : isInsufficient
                    ? 'var(--color-warning)'
                    : 'var(--text-secondary)',
                  border: `1px solid ${
                    isSelected ? 'var(--color-primary-border)' : 'var(--border-subtle)'
                  }`,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
                title={`${sc.name}: ${sc.expected_behavior}`}
              >
                {isAdversarial && <AlertTriangle size={10} />}
                {isInsufficient && <HelpCircle size={10} />}
                {sc.name.split(' ')[0]} {sc.name.split(' ')[1] || ''}
              </button>
            );
          })}
        </div>
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{ position: 'relative' }}>
          <textarea
            value={question}
            onChange={(e) => onChangeQuestion(e.target.value)}
            disabled={isLoading}
            placeholder="e.g. Why did customer cancellations increase sharply in September 2025? (Look for billing, support, or release incidents)"
            rows={3}
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
              transition: 'border-color 0.15s ease',
            }}
            onFocus={(e) => (e.target.style.borderColor = 'var(--border-focus)')}
            onBlur={(e) => (e.target.style.borderColor = 'var(--border-default)')}
          />
          <div style={{
            position: 'absolute',
            bottom: '8px',
            right: '12px',
            fontSize: '11px',
            color: question.length < 5 ? 'var(--color-danger)' : 'var(--text-muted)',
            fontFamily: 'var(--font-mono)',
          }}>
            {question.length}/1000 chars
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            {!isBackendOnline && (
              <span style={{ color: 'var(--color-danger)', fontWeight: 600 }}>
                ⚠️ Backend is offline. Ensure FastAPI is running on port 8000.
              </span>
            )}
            {isBackendOnline && (
              <span>
                💡 Deterministic pipeline: Step planning &rarr; AST SQL / Doc tools &rarr; Evidence hashing &rarr; Grounded report
              </span>
            )}
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              type="button"
              onClick={onReset}
              disabled={isLoading || !question}
              style={{
                backgroundColor: 'var(--bg-surface)',
                color: 'var(--text-secondary)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                padding: '8px 16px',
                fontSize: '13px',
                fontWeight: 500,
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <RefreshCw size={14} />
              Reset
            </button>

            <button
              type="submit"
              disabled={isLoading || question.trim().length < 5 || !isBackendOnline}
              style={{
                backgroundColor: isBackendOnline && question.trim().length >= 5
                  ? 'var(--color-primary)'
                  : 'var(--bg-surface-hover)',
                color: isBackendOnline && question.trim().length >= 5 ? '#030712' : 'var(--text-muted)',
                borderRadius: 'var(--radius-md)',
                padding: '8px 20px',
                fontSize: '13px',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                boxShadow: isBackendOnline ? 'var(--shadow-sm)' : 'none',
              }}
            >
              {isLoading ? (
                <>
                  <RefreshCw size={15} style={{ animation: 'spin 1s linear infinite' }} />
                  Investigating...
                </>
              ) : (
                <>
                  <Play size={15} fill="currentColor" />
                  Run Investigation
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};
