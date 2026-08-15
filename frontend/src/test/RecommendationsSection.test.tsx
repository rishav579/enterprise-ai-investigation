import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { RecommendationsSection } from '../components/RecommendationsSection';
import { mockFullInvestigationResponse } from './mockData';

describe('RecommendationsSection component', () => {
  it('renders recommendations with action, rationale, and priority', () => {
    render(
      <RecommendationsSection
        recommendations={mockFullInvestigationResponse.report.recommendations}
        onSelectEvidenceId={vi.fn()}
      />
    );

    expect(screen.getByText('REC-001')).toBeInTheDocument();
    expect(screen.getByText('Critical Priority')).toBeInTheDocument();
    expect(
      screen.getByText(/Implement end-to-end webhook integration test suites/i)
    ).toBeInTheDocument();
  });

  it('displays clearly labeled HUMAN REVIEW — SIMULATION badge', () => {
    render(
      <RecommendationsSection
        recommendations={mockFullInvestigationResponse.report.recommendations}
        onSelectEvidenceId={vi.fn()}
      />
    );

    expect(screen.getByText('HUMAN REVIEW — SIMULATION')).toBeInTheDocument();
    expect(screen.getByText('Pending Human Sign-Off')).toBeInTheDocument();
  });

  it('simulates human approval when Approve Action is clicked', () => {
    render(
      <RecommendationsSection
        recommendations={mockFullInvestigationResponse.report.recommendations}
        onSelectEvidenceId={vi.fn()}
      />
    );

    const approveBtn = screen.getByRole('button', { name: /approve action/i });
    fireEvent.click(approveBtn);

    expect(screen.getByText(/Approved by Human Reviewer/i)).toBeInTheDocument();
    expect(screen.getByText(/Logged by/i)).toBeInTheDocument();
  });

  it('simulates rejection when Reject Action is clicked', () => {
    render(
      <RecommendationsSection
        recommendations={mockFullInvestigationResponse.report.recommendations}
        onSelectEvidenceId={vi.fn()}
      />
    );

    const rejectBtn = screen.getByRole('button', { name: /reject action/i });
    fireEvent.click(rejectBtn);

    expect(screen.getByText(/Rejected by Reviewer/i)).toBeInTheDocument();
  });
});
