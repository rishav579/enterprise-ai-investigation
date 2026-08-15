import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { FindingsSection } from '../components/FindingsSection';
import { mockFullInvestigationResponse } from './mockData';

describe('FindingsSection component', () => {
  it('renders executive summary and verified citation badge', () => {
    render(
      <FindingsSection
        report={mockFullInvestigationResponse.report}
        onSelectEvidenceId={vi.fn()}
      />
    );

    expect(
      screen.getByText(/Customer cancellations surged 12x in September 2025/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/Citations 100% Verified/i)).toBeInTheDocument();
  });

  it('renders root cause box with identified cause', () => {
    render(
      <FindingsSection
        report={mockFullInvestigationResponse.report}
        onSelectEvidenceId={vi.fn()}
      />
    );

    expect(
      screen.getByText(/Deployment of billing-gateway v2.4.0 introduced a webhook parsing regression/i)
    ).toBeInTheDocument();
  });

  it('renders findings list and fires onSelectEvidenceId on citation click', () => {
    const handleSelectEvidence = vi.fn();
    render(
      <FindingsSection
        report={mockFullInvestigationResponse.report}
        onSelectEvidenceId={handleSelectEvidence}
      />
    );

    expect(screen.getByText('FND-001')).toBeInTheDocument();
    expect(
      screen.getByText(/Customer cancellations spiked significantly in September 2025 reaching 148 cancellations/i)
    ).toBeInTheDocument();

    const citationBtns = screen.getAllByText(/EVID-001/i);
    fireEvent.click(citationBtns[0]);
    expect(handleSelectEvidence).toHaveBeenCalledWith('EVID-001');
  });

  it('renders insufficient evidence state properly when report is insufficient', () => {
    const insufficientReport = {
      ...mockFullInvestigationResponse.report,
      root_cause: null,
      citation_valid: false,
      synthesis_status: 'insufficient_evidence' as const,
      findings: [],
    };

    render(
      <FindingsSection
        report={insufficientReport}
        onSelectEvidenceId={vi.fn()}
      />
    );

    expect(screen.getByText(/Insufficient Evidence/i)).toBeInTheDocument();
    expect(screen.getByText(/No root cause could be established/i)).toBeInTheDocument();
  });
});
