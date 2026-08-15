import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Header } from '../components/Header';

describe('Header component', () => {
  it('renders branding title and subtitle', () => {
    render(
      <Header
        health={{ status: 'ok', version: '0.1.0' }}
        healthLoading={false}
        onRefreshHealth={vi.fn()}
      />
    );

    expect(
      screen.getByText('Enterprise AI Investigation & Decision System')
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Deterministic Data Investigation/i)
    ).toBeInTheDocument();
  });

  it('renders online backend badge when health status is ok', () => {
    render(
      <Header
        health={{ status: 'ok', version: '0.1.0' }}
        healthLoading={false}
        onRefreshHealth={vi.fn()}
      />
    );

    expect(screen.getByText('Backend Online')).toBeInTheDocument();
  });

  it('renders offline backend badge when health is null', () => {
    render(
      <Header
        health={null}
        healthLoading={false}
        onRefreshHealth={vi.fn()}
      />
    );

    expect(screen.getByText('Backend Offline')).toBeInTheDocument();
  });

  it('renders active investigation ID when provided', () => {
    render(
      <Header
        health={{ status: 'ok' }}
        healthLoading={false}
        onRefreshHealth={vi.fn()}
        investigationId="INV-CHURN-2025"
      />
    );

    expect(screen.getByText('INV-CHURN-2025')).toBeInTheDocument();
  });

  it('calls onRefreshHealth when refresh icon button is clicked', () => {
    const handleRefresh = vi.fn();
    render(
      <Header
        health={{ status: 'ok' }}
        healthLoading={false}
        onRefreshHealth={handleRefresh}
      />
    );

    const refreshBtn = screen.getByRole('button', { name: /refresh backend status/i });
    fireEvent.click(refreshBtn);
    expect(handleRefresh).toHaveBeenCalledTimes(1);
  });
});
