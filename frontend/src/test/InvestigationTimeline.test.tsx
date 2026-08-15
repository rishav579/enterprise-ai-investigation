import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { InvestigationTimeline } from '../components/InvestigationTimeline';
import { mockFullInvestigationResponse } from './mockData';

describe('InvestigationTimeline component', () => {
  it('renders all planned steps with objectives and tool badges', () => {
    render(
      <InvestigationTimeline
        plan={mockFullInvestigationResponse.run_result.plan}
        stepResults={mockFullInvestigationResponse.run_result.step_results}
        onSelectEvidenceId={vi.fn()}
      />
    );

    expect(screen.getAllByText('STEP-01').length).toBeGreaterThan(0);
    expect(screen.getByText('STEP-02')).toBeInTheDocument();
    expect(
      screen.getByText('Establish monthly cancellation baseline')
    ).toBeInTheDocument();
    expect(screen.getByText('sql_investigation')).toBeInTheDocument();
    expect(screen.getByText('document_retrieval')).toBeInTheDocument();
  });

  it('renders evidence artifacts and fires onSelectEvidenceId on click', () => {
    const handleSelectEvidence = vi.fn();
    render(
      <InvestigationTimeline
        plan={mockFullInvestigationResponse.run_result.plan}
        stepResults={mockFullInvestigationResponse.run_result.step_results}
        onSelectEvidenceId={handleSelectEvidence}
      />
    );

    const evidBtn = screen.getByText('🔍 EVID-001');
    expect(evidBtn).toBeInTheDocument();
    fireEvent.click(evidBtn);
    expect(handleSelectEvidence).toHaveBeenCalledWith('EVID-001');
  });

  it('toggles step collapse and expand', () => {
    render(
      <InvestigationTimeline
        plan={mockFullInvestigationResponse.run_result.plan}
        stepResults={mockFullInvestigationResponse.run_result.step_results}
        onSelectEvidenceId={vi.fn()}
      />
    );

    expect(screen.getByText(/Verify whether an anomaly exists/i)).toBeInTheDocument();
    const step1Header = screen.getByText('Establish monthly cancellation baseline');
    fireEvent.click(step1Header);
    expect(screen.queryByText(/Verify whether an anomaly exists/i)).not.toBeInTheDocument();
  });
});
