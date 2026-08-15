import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { AuditTrailStream } from '../components/AuditTrailStream';
import { mockFullInvestigationResponse } from './mockData';

describe('AuditTrailStream component', () => {
  it('renders all audit events with sequential IDs and event types', () => {
    render(
      <AuditTrailStream
        auditEvents={mockFullInvestigationResponse.audit_events}
      />
    );

    expect(screen.getByText('AUDIT-001')).toBeInTheDocument();
    expect(screen.getByText('AUDIT-002')).toBeInTheDocument();
    expect(screen.getByText('AUDIT-003')).toBeInTheDocument();
    expect(screen.getByText('investigation_started')).toBeInTheDocument();
    expect(screen.getByText('plan_created')).toBeInTheDocument();
    expect(screen.getByText('synthesis_validated')).toBeInTheDocument();
  });

  it('filters events when filter pills are clicked', () => {
    render(
      <AuditTrailStream
        auditEvents={mockFullInvestigationResponse.audit_events}
      />
    );

    const evidenceFilter = screen.getByRole('button', { name: /evidence/i });
    fireEvent.click(evidenceFilter);

    expect(screen.getByText('evidence_collected')).toBeInTheDocument();
    expect(screen.queryByText('plan_created')).not.toBeInTheDocument();
  });
});
