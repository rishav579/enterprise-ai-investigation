import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { NiftyWorkflow } from './NiftyWorkflow';
import { niftyApi } from './api';
import type {
  NiftyExplainResponse,
  NiftyInterpretResponse,
  NiftyRunResponse,
} from './types';

vi.mock('./api', () => {
  class NiftyApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
      super(message);
      this.name = 'NiftyApiError';
      this.status = status;
    }
  }
  return {
    NiftyApiError,
    niftyApi: {
      interpret: vi.fn(),
      validateExperiment: vi.fn(),
      run: vi.fn(),
      explain: vi.fn(),
    },
  };
});

const mockInterpret: NiftyInterpretResponse = {
  question: 'Does buying NIFTY after a sharp fall work?',
  market: 'NIFTY50',
  recognized: true,
  note: 'Recognized as the NIFTY dip-buy prototype question.',
  ambiguities: [
    { field: 'sharp_fall_threshold_pct', label: 'What counts as a sharp fall?', why_it_matters: 'Decides the sample.' },
    { field: 'work_definition', label: "What does 'work' mean?", why_it_matters: 'Defines success.' },
    { field: 'holding_days_primary', label: 'How long to hold?', why_it_matters: 'Results are horizon-specific.' },
    { field: 'test_period', label: 'What period to test?', why_it_matters: 'Regimes differ.' },
  ],
  suggested_assumptions: {
    sharp_fall_threshold_pct: -3.0,
    work_definition: 'avg_return',
    holding_days_primary: 5,
    holding_days_sensitivity: [10, 20],
    entry_timing: 'next_open',
    cost_bps: 10.0,
    allow_overlapping_positions: false,
    test_period_start: '2015-01-01',
    test_period_end: '2024-12-31',
  },
  explanations: {
    sharp_fall_threshold_pct: 'Suggested: 3% decline qualifies.',
    work_definition: 'Suggested: positive average net return.',
    holding_days_primary: 'Suggested: 5-day primary hold.',
    test_period: 'Suggested: full mock-data range.',
  },
};

const mockRun: NiftyRunResponse = {
  experiment: {
    market: 'NIFTY50',
    sharp_fall_threshold_pct: -3.0,
    work_definition: 'avg_return',
    holding_days_primary: 5,
    holding_days_sensitivity: [10, 20],
    entry_timing: 'next_open',
    cost_bps: 10.0,
    allow_overlapping_positions: false,
    test_period_start: '2015-01-01',
    test_period_end: '2024-12-31',
  },
  dataset: {
    type: 'synthetic_mock',
    source_note: 'Synthetic mock NIFTY daily OHLC (seed 42). Not real market data.',
    rows_in_period: 2609,
    coverage_start: '2015-01-01',
    coverage_end: '2024-12-31',
  },
  signals_detected: 39,
  primary: {
    holding_days: 5,
    is_primary: true,
    trade_count: 34,
    average_net_return: 0.0042,
    median_net_return: 0.0021,
    win_rate: 0.558,
  },
  sensitivity: [
    { holding_days: 10, is_primary: false, trade_count: 33, average_net_return: 0.0061, median_net_return: 0.003, win_rate: 0.575 },
    { holding_days: 20, is_primary: false, trade_count: 31, average_net_return: -0.0012, median_net_return: 0.0004, win_rate: 0.5 },
  ],
  warnings: ['Low sample size (n=34) — interpret with caution.'],
  trades: [
    {
      signal_date: '2015-03-02',
      entry_date: '2015-03-03',
      exit_date: '2015-03-09',
      holding_days: 5,
      entry_price: 8900.1,
      exit_price: 8950.5,
      gross_return: 0.0056,
      net_return: 0.0046,
    },
  ],
  returns_by_holding: { '5': [0.0046, -0.01, 0.02], '10': [0.006], '20': [-0.001] },
};

const mockExplain: NiftyExplainResponse = {
  what_data_shows: '39 qualifying signal(s) were detected; 34 completed 5-day trade(s). The average 5-day net return was +0.42%.',
  what_we_conclude: 'Under this definition the setup showed a positive historical tendency. This does not establish future performance.',
  what_to_investigate_next: [
    'What happens if the sharp-fall threshold changes (e.g. −2% or −5%)?',
    'Does the result persist in different market regimes or sub-periods?',
    'Would a matched random-entry benchmark change the conclusion?',
  ],
};

describe('NiftyWorkflow Phase 4', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(niftyApi.interpret).mockResolvedValue(mockInterpret);
    vi.mocked(niftyApi.validateExperiment).mockImplementation(async (intent) => intent);
    vi.mocked(niftyApi.run).mockResolvedValue(mockRun);
    vi.mocked(niftyApi.explain).mockResolvedValue(mockExplain);
  });

  it('renders ASK stage with the default prototype question', () => {
    render(<NiftyWorkflow />);
    expect(screen.getByText('NIFTY Dip-Buy Research Lab')).toBeInTheDocument();
    expect(screen.getByLabelText('Research question')).toHaveValue('Does buying NIFTY after a sharp fall work?');
    expect(screen.getByRole('button', { name: /clarify assumptions/i })).toBeInTheDocument();
  });

  it('walks ASK → CLARIFY → DEFINE → TEST → LEARN without touching results early', async () => {
    render(<NiftyWorkflow />);

    // ASK → CLARIFY
    fireEvent.click(screen.getByRole('button', { name: /clarify assumptions/i }));
    await waitFor(() => {
      expect(screen.getByText('CLARIFY — What needs pinning down')).toBeInTheDocument();
    });
    expect(vi.mocked(niftyApi.interpret)).toHaveBeenCalledTimes(1);
    // No backtest on the interpret path
    expect(vi.mocked(niftyApi.run)).not.toHaveBeenCalled();

    // CLARIFY → DEFINE
    fireEvent.click(screen.getByRole('button', { name: /accept & define experiment/i }));
    expect(screen.getByText('DEFINE — Lock the experiment before seeing results')).toBeInTheDocument();

    // DEFINE → TEST (validate then run)
    fireEvent.click(screen.getByRole('button', { name: /lock & run test/i }));
    await waitFor(() => {
      expect(screen.getByText('Sensitivity — holding-period comparison')).toBeInTheDocument();
    });
    expect(vi.mocked(niftyApi.validateExperiment)).toHaveBeenCalledTimes(1);
    expect(vi.mocked(niftyApi.run)).toHaveBeenCalledTimes(1);
    // Synthetic disclaimer is always visible on TEST
    expect(screen.getAllByText(/synthetic mock data/i).length).toBeGreaterThan(0);

    // TEST → LEARN
    fireEvent.click(screen.getByRole('button', { name: /continue to learn/i }));
    await waitFor(() => {
      expect(screen.getByText('LEARN — Grounded summary (deterministic, advice-free)')).toBeInTheDocument();
    });
    expect(vi.mocked(niftyApi.explain)).toHaveBeenCalledTimes(1);
    expect(screen.getByText(/39 qualifying signal/i)).toBeInTheDocument();
    expect(screen.getByText(/what to investigate next/i)).toBeInTheDocument();
  });

  it('blocks a non-negative threshold in DEFINE with an inline message', async () => {
    render(<NiftyWorkflow />);
    fireEvent.click(screen.getByRole('button', { name: /clarify assumptions/i }));
    await waitFor(() => screen.getByRole('button', { name: /accept & define experiment/i }));
    fireEvent.click(screen.getByRole('button', { name: /accept & define experiment/i }));

    const threshold = screen.getByLabelText('Sharp-fall threshold percent');
    fireEvent.change(threshold, { target: { value: '3' } });
    expect(screen.getByText(/threshold must be negative/i)).toBeInTheDocument();
    expect(vi.mocked(niftyApi.run)).not.toHaveBeenCalled();
  });

  it('surfaces backend failures with a retryable error banner', async () => {
    const { NiftyApiError } = await import('./api');
    vi.mocked(niftyApi.interpret).mockRejectedValueOnce(new NiftyApiError('Dataset unavailable: missing CSV', 503));
    render(<NiftyWorkflow />);
    fireEvent.click(screen.getByRole('button', { name: /clarify assumptions/i }));
    await waitFor(() => {
      expect(screen.getByText(/dataset unavailable/i)).toBeInTheDocument();
    });
    // Still on ASK after failure
    expect(screen.getByLabelText('Research question')).toBeInTheDocument();
  });

  it('handles the empty-sample path without fabricating an average', async () => {
    const emptyRun: NiftyRunResponse = {
      ...mockRun,
      signals_detected: 0,
      primary: { holding_days: 5, is_primary: true, trade_count: 0, average_net_return: null, median_net_return: null, win_rate: null },
      trades: [],
      returns_by_holding: { '5': [] },
      warnings: ['No qualifying signals were found for the selected parameters. No conclusion can be drawn.'],
    };
    vi.mocked(niftyApi.run).mockResolvedValueOnce(emptyRun);
    vi.mocked(niftyApi.explain).mockResolvedValueOnce({
      what_data_shows: '0 qualifying signal(s) were detected but no complete 5-day trade could be formed. No conclusion can be drawn.',
      what_we_conclude: 'With no measurable sample there is nothing to conclude.',
      what_to_investigate_next: ['a', 'b', 'c'],
    });

    render(<NiftyWorkflow />);
    fireEvent.click(screen.getByRole('button', { name: /clarify assumptions/i }));
    await waitFor(() => screen.getByRole('button', { name: /accept & define experiment/i }));
    fireEvent.click(screen.getByRole('button', { name: /accept & define experiment/i }));
    fireEvent.click(screen.getByRole('button', { name: /lock & run test/i }));
    await waitFor(() => {
      expect(screen.getByText(/no complete 5-day trade could be formed/i)).toBeInTheDocument();
    });
  });
});
