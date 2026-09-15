import React, { useCallback, useMemo, useState } from 'react';
import { RotateCcw, FlaskConical } from 'lucide-react';
import { AskStep } from './AskStep';
import { ClarifyStep } from './ClarifyStep';
import { DefineStep } from './DefineStep';
import { TestStep } from './TestStep';
import { LearnStep } from './LearnStep';
import { Stepper } from './Stepper';
import { niftyApi, NiftyApiError } from './api';
import type {
  NiftyExperimentIntent,
  NiftyExplainResponse,
  NiftyInterpretResponse,
  NiftyRunResponse,
  NiftyStage,
} from './types';
import {
  NIFTY_DEFAULT_QUESTION,
  NIFTY_STAGES,
  defaultIntentFromSuggestions,
  explainRequestFromRun,
} from './types';
import { ErrorBanner } from '../components/ErrorBanner';

type LoadingKind = 'interpret' | 'validate-run' | 'explain' | null;

function advance(reached: NiftyStage, next: NiftyStage): NiftyStage {
  return NIFTY_STAGES.indexOf(next) > NIFTY_STAGES.indexOf(reached) ? next : reached;
}

function errorMessage(err: unknown): string {
  if (err instanceof NiftyApiError) return err.message;
  return err instanceof Error ? err.message : 'Unexpected NIFTY request failure.';
}

export const NiftyWorkflow: React.FC = () => {
  const [stage, setStage] = useState<NiftyStage>('ask');
  const [reached, setReached] = useState<NiftyStage>('ask');
  const [question, setQuestion] = useState<string>(NIFTY_DEFAULT_QUESTION);
  const [interpretation, setInterpretation] = useState<NiftyInterpretResponse | null>(null);
  const [draft, setDraft] = useState<NiftyExperimentIntent>(() => defaultIntentFromSuggestions());
  const [run, setRun] = useState<NiftyRunResponse | null>(null);
  const [explanation, setExplanation] = useState<NiftyExplainResponse | null>(null);
  const [loading, setLoading] = useState<LoadingKind>(null);
  const [error, setError] = useState<string | null>(null);

  const goTo = useCallback(
    (next: NiftyStage) => {
      if (NIFTY_STAGES.indexOf(next) <= NIFTY_STAGES.indexOf(reached)) {
        setStage(next);
        setError(null);
      }
    },
    [reached],
  );

  const handleInterpret = useCallback(async () => {
    setLoading('interpret');
    setError(null);
    try {
      const res = await niftyApi.interpret(question.trim());
      setInterpretation(res);
      setDraft(defaultIntentFromSuggestions(res.suggested_assumptions));
      setRun(null);
      setExplanation(null);
      setStage('clarify');
      setReached((r) => advance(r, 'clarify'));
    } catch (err: unknown) {
      setError(errorMessage(err));
    } finally {
      setLoading(null);
    }
  }, [question]);

  const handleValidateAndRun = useCallback(async () => {
    setLoading('validate-run');
    setError(null);
    try {
      const validated = await niftyApi.validateExperiment(draft);
      const result = await niftyApi.run(validated);
      setRun(result);
      setExplanation(null);
      setStage('test');
      setReached((r) => advance(r, 'test'));
    } catch (err: unknown) {
      setError(errorMessage(err));
    } finally {
      setLoading(null);
    }
  }, [draft]);

  const handleExplain = useCallback(async () => {
    if (!run) return;
    setLoading('explain');
    setError(null);
    try {
      const res = await niftyApi.explain(explainRequestFromRun(run));
      setExplanation(res);
      setStage('learn');
      setReached((r) => advance(r, 'learn'));
    } catch (err: unknown) {
      setError(errorMessage(err));
    } finally {
      setLoading(null);
    }
  }, [run]);

  const handleRestart = useCallback(() => {
    setStage('ask');
    setReached('ask');
    setInterpretation(null);
    setDraft(defaultIntentFromSuggestions());
    setRun(null);
    setExplanation(null);
    setError(null);
    setLoading(null);
  }, []);

  const retry = useMemo(() => {
    if (stage === 'ask') return handleInterpret;
    if (stage === 'define') return handleValidateAndRun;
    if (stage === 'test') return handleExplain;
    return undefined;
  }, [stage, handleInterpret, handleValidateAndRun, handleExplain]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div
        style={{
          backgroundColor: 'var(--bg-panel)',
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-lg)',
          padding: '16px 20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '12px',
          flexWrap: 'wrap',
        }}
      >
        <div>
          <h2 style={{ fontSize: '15px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FlaskConical size={16} color="var(--color-primary)" />
            NIFTY Dip-Buy Research Lab
          </h2>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
            ASK → CLARIFY → DEFINE → TEST → LEARN on synthetic mock data. Assumptions lock before results.
          </p>
        </div>
        <button
          type="button"
          onClick={handleRestart}
          style={{
            backgroundColor: 'var(--bg-surface)',
            color: 'var(--text-secondary)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-md)',
            padding: '6px 12px',
            fontSize: '12px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <RotateCcw size={13} />
          Reset lab
        </button>
      </div>

      <Stepper current={stage} reached={reached} onNavigate={goTo} />

      {error && <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={retry} />}

      {stage === 'ask' && (
        <AskStep question={question} onChange={setQuestion} onSubmit={handleInterpret} isLoading={loading === 'interpret'} />
      )}

      {stage === 'clarify' && interpretation && (
        <ClarifyStep
          interpretation={interpretation}
          onAccept={() => {
            setStage('define');
            setReached((r) => advance(r, 'define'));
            setError(null);
          }}
          onBack={() => goTo('ask')}
        />
      )}

      {stage === 'define' && (
        <DefineStep
          draft={draft}
          onChange={setDraft}
          onValidateAndRun={handleValidateAndRun}
          onBack={() => goTo(interpretation ? 'clarify' : 'ask')}
          isLoading={loading === 'validate-run'}
          serverError={null}
        />
      )}

      {stage === 'test' && run && (
        <TestStep run={run} onExplain={handleExplain} onBack={() => goTo('define')} explainLoading={loading === 'explain'} />
      )}

      {stage === 'learn' && run && explanation && (
        <LearnStep run={run} explanation={explanation} onRestart={handleRestart} onBack={() => goTo('test')} />
      )}
    </div>
  );
};
