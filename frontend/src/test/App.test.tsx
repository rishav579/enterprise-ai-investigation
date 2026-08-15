import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { App } from '../App';
import { apiClient } from '../api/client';
import { mockFullInvestigationResponse, mockScenarioList } from './mockData';

vi.mock('../api/client', () => ({
  apiClient: {
    checkHealth: vi.fn(),
    fetchScenarios: vi.fn(),
    runInvestigation: vi.fn(),
    fetchLatestEvaluation: vi.fn(),
  },
}));

describe('App component integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(apiClient.checkHealth).mockResolvedValue({
      status: 'ok',
      version: '0.1.0',
      app: 'Enterprise AI Investigation System',
    });
    vi.mocked(apiClient.fetchScenarios).mockResolvedValue(mockScenarioList);
    vi.mocked(apiClient.runInvestigation).mockResolvedValue(mockFullInvestigationResponse);
  });

  it('renders header, guardrails, and empty state initially', async () => {
    render(<App />);

    expect(
      screen.getByText('Enterprise AI Investigation & Decision System')
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Backend Online')).toBeInTheDocument();
    });

    expect(
      screen.getByText('No Active Investigation Dispatched')
    ).toBeInTheDocument();
  });

  it('executes full investigation workflow when Run Investigation is clicked', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('Backend Online')).toBeInTheDocument();
    });

    const runBtn = screen.getByRole('button', { name: /run investigation/i });
    fireEvent.click(runBtn);

    await waitFor(() => {
      expect(
        screen.getByText(/Customer cancellations surged 12x in September 2025/i)
      ).toBeInTheDocument();
    });

    // Check KPIs
    expect(screen.getByText(/2 \/ 2 Completed/i)).toBeInTheDocument();
    expect(screen.getByText(/2 Hashed Artifacts/i)).toBeInTheDocument();

    // Check Findings
    expect(screen.getByText('FND-001')).toBeInTheDocument();

    // Check Recommendations & Human review
    expect(screen.getByText('REC-001')).toBeInTheDocument();
    expect(screen.getByText('HUMAN REVIEW — SIMULATION')).toBeInTheDocument();

    // Switch to Timeline tab
    const timelineTab = screen.getByRole('button', { name: /investigation steps/i });
    fireEvent.click(timelineTab);
    expect(screen.getByText('Establish monthly cancellation baseline')).toBeInTheDocument();

    // Switch to Audit tab
    const auditTab = screen.getByRole('button', { name: /immutable audit trail/i });
    fireEvent.click(auditTab);
    expect(screen.getByText('AUDIT-001')).toBeInTheDocument();
    expect(screen.getByText('investigation_started')).toBeInTheDocument();
  });

  it('opens EvidenceInspector when evidence token is clicked and closes on close button', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('Backend Online')).toBeInTheDocument();
    });

    const runBtn = screen.getByRole('button', { name: /run investigation/i });
    fireEvent.click(runBtn);

    await waitFor(() => {
      expect(screen.getByText('FND-001')).toBeInTheDocument();
    });

    const citationBtns = screen.getAllByText(/EVID-001/i);
    fireEvent.click(citationBtns[0]);

    // Check inspector is open
    expect(screen.getByText('SHA-256 CONTENT INTEGRITY FINGERPRINT')).toBeInTheDocument();
    expect(screen.getByText('total_cancellations')).toBeInTheDocument();

    // Close inspector
    const closeBtn = screen.getByRole('button', { name: /close evidence inspector/i });
    fireEvent.click(closeBtn);

    expect(screen.queryByText('SHA-256 CONTENT INTEGRITY FINGERPRINT')).not.toBeInTheDocument();
  });

  it('displays ErrorBanner when investigation fails', async () => {
    vi.mocked(apiClient.runInvestigation).mockRejectedValueOnce(
      new Error('Prohibited SQL keyword detected: DROP')
    );

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('Backend Online')).toBeInTheDocument();
    });

    const runBtn = screen.getByRole('button', { name: /run investigation/i });
    fireEvent.click(runBtn);

    await waitFor(() => {
      expect(
        screen.getByText(/Prohibited SQL keyword detected: DROP/i)
      ).toBeInTheDocument();
    });
  });
});
