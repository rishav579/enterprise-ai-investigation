import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { EvidenceInspector } from '../components/EvidenceInspector';
import { mockFullInvestigationResponse } from './mockData';

describe('EvidenceInspector component', () => {
  const sqlEvidence = mockFullInvestigationResponse.evidence_items[0];
  const docEvidence = mockFullInvestigationResponse.evidence_items[1];

  it('renders nothing when evidenceItem is null', () => {
    const { container } = render(
      <EvidenceInspector evidenceItem={null} onClose={vi.fn()} />
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('renders SQL evidence table, column headers, and row data', () => {
    render(
      <EvidenceInspector evidenceItem={sqlEvidence} onClose={vi.fn()} />
    );

    expect(screen.getByText('EVID-001')).toBeInTheDocument();
    expect(screen.getByText('sql_result')).toBeInTheDocument();
    expect(screen.getByText('churn_month')).toBeInTheDocument();
    expect(screen.getByText('total_cancellations')).toBeInTheDocument();
    expect(screen.getByText('2025-09')).toBeInTheDocument();
    expect(screen.getByText('148')).toBeInTheDocument();
  });

  it('renders SHA-256 content hash', () => {
    render(
      <EvidenceInspector evidenceItem={sqlEvidence} onClose={vi.fn()} />
    );

    expect(screen.getByText(sqlEvidence.content_hash)).toBeInTheDocument();
  });

  it('renders document full text for document evidence', () => {
    render(
      <EvidenceInspector evidenceItem={docEvidence} onClose={vi.fn()} />
    );

    expect(screen.getByText('EVID-002')).toBeInTheDocument();
    expect(screen.getByText('document_text')).toBeInTheDocument();
    expect(
      screen.getByText(/Incident Postmortem: billing-gateway v2.4.0 introduced webhook confirmation bug/i)
    ).toBeInTheDocument();
  });

  it('switches between structured view and raw JSON view', () => {
    render(
      <EvidenceInspector evidenceItem={sqlEvidence} onClose={vi.fn()} />
    );

    const rawTab = screen.getByRole('button', { name: /raw json content/i });
    fireEvent.click(rawTab);

    expect(screen.getByText(/"query_reference":/i)).toBeInTheDocument();
  });

  it('fires onClose when close button is clicked', () => {
    const handleClose = vi.fn();
    render(
      <EvidenceInspector evidenceItem={sqlEvidence} onClose={handleClose} />
    );

    const closeBtn = screen.getByRole('button', { name: /close evidence inspector/i });
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});
