/**
 * NIFTY dip-buy research prototype — frontend types.
 * Mirror the backend Pydantic contracts in src/nifty/ + src/api/nifty_routes.py.
 * No arithmetic here; formatting lives in format.ts.
 */

export const NIFTY_DEFAULT_QUESTION = 'Does buying NIFTY after a sharp fall work?';

export const NIFTY_DEFAULT_TEST_START = '2015-01-01';
export const NIFTY_DEFAULT_TEST_END = '2024-12-31';

/** Locked MVP constants (backend src/nifty/models.py). Displayed read-only in DEFINE. */
export const NIFTY_PRIMARY_HOLDING_DAYS = 5;
export const NIFTY_SENSITIVITY_HOLDING_DAYS: readonly number[] = [10, 20];

export type NiftyStage = 'ask' | 'clarify' | 'define' | 'test' | 'learn';

export const NIFTY_STAGES: readonly NiftyStage[] = ['ask', 'clarify', 'define', 'test', 'learn'];

export interface NiftyAmbiguity {
  field: string;
  label: string;
  why_it_matters: string;
}

export interface NiftySuggestedAssumptions {
  sharp_fall_threshold_pct: number;
  work_definition: string;
  holding_days_primary: number;
  holding_days_sensitivity: number[];
  entry_timing: string;
  cost_bps: number;
  allow_overlapping_positions: boolean;
  test_period_start: string;
  test_period_end: string;
}

export interface NiftyInterpretResponse {
  question: string;
  market: string;
  recognized: boolean;
  note: string;
  ambiguities: NiftyAmbiguity[];
  suggested_assumptions: NiftySuggestedAssumptions;
  explanations: Record<string, string>;
}

export interface NiftyExperimentIntent {
  market: 'NIFTY50';
  sharp_fall_threshold_pct: number;
  work_definition: 'avg_return';
  holding_days_primary: 5;
  holding_days_sensitivity: number[];
  entry_timing: 'next_open';
  cost_bps: number;
  allow_overlapping_positions: false;
  test_period_start: string;
  test_period_end: string;
}

export interface NiftyDatasetInfo {
  type: string;
  source_note: string;
  rows_in_period: number;
  coverage_start: string;
  coverage_end: string;
}

export interface NiftyHoldingResult {
  holding_days: number;
  is_primary: boolean;
  trade_count: number;
  average_net_return: number | null;
  median_net_return: number | null;
  win_rate: number | null;
}

export interface NiftyTradeResult {
  signal_date: string;
  entry_date: string;
  exit_date: string;
  holding_days: number;
  entry_price: number;
  exit_price: number;
  gross_return: number;
  net_return: number;
}

export interface NiftyRunResponse {
  experiment: NiftyExperimentIntent;
  dataset: NiftyDatasetInfo;
  signals_detected: number;
  primary: NiftyHoldingResult;
  sensitivity: NiftyHoldingResult[];
  warnings: string[];
  trades: NiftyTradeResult[];
  returns_by_holding: Record<string, number[]>;
}

export interface NiftyExplainRequest {
  threshold_pct: number;
  cost_bps: number;
  test_period_start: string;
  test_period_end: string;
  signals_detected: number;
  primary: NiftyHoldingResult;
  sensitivity: NiftyHoldingResult[];
  warnings: string[];
}

export interface NiftyExplainResponse {
  what_data_shows: string;
  what_we_conclude: string;
  what_to_investigate_next: string[];
}

/** Build the /api/explain payload strictly from a /api/run response (mirrors backend helper). */
export function explainRequestFromRun(run: NiftyRunResponse): NiftyExplainRequest {
  return {
    threshold_pct: run.experiment.sharp_fall_threshold_pct,
    cost_bps: run.experiment.cost_bps,
    test_period_start: run.experiment.test_period_start,
    test_period_end: run.experiment.test_period_end,
    signals_detected: run.signals_detected,
    primary: run.primary,
    sensitivity: run.sensitivity,
    warnings: run.warnings,
  };
}

/** Default experiment pre-filled from CLARIFY suggestions (or locked MVP defaults). */
export function defaultIntentFromSuggestions(s?: NiftySuggestedAssumptions): NiftyExperimentIntent {
  return {
    market: 'NIFTY50',
    sharp_fall_threshold_pct: s?.sharp_fall_threshold_pct ?? -3.0,
    work_definition: 'avg_return',
    holding_days_primary: 5,
    holding_days_sensitivity: [...(s?.holding_days_sensitivity ?? [10, 20])],
    entry_timing: 'next_open',
    cost_bps: s?.cost_bps ?? 10.0,
    allow_overlapping_positions: false,
    test_period_start: s?.test_period_start ?? NIFTY_DEFAULT_TEST_START,
    test_period_end: s?.test_period_end ?? NIFTY_DEFAULT_TEST_END,
  };
}
