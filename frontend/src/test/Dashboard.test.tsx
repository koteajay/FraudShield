import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Dashboard } from '../components/dashboard/Dashboard';
import type { DashboardStats } from '../types/dashboard';

const mockStats: DashboardStats = {
  total_transactions: 1250,
  flagged: 180,
  high_risk_transactions: 31,
  critical_risk_transactions: 12,
  pending_review: 42,
  reviewed_transactions: 95,
  cleared_transactions: 180,
  average_risk_score: 38.4,
  new_devices: 24,
  account_takeover_risk_events: 8,
};

describe('Dashboard Component', () => {
  it('renders all 7 core operational metrics with exact numbers', () => {
    render(
      <Dashboard
        stats={mockStats}
        isLoading={false}
        error={null}
        onRetry={vi.fn()}
      />
    );

    // Titles
    expect(screen.getByText('Total')).toBeInTheDocument();
    expect(screen.getByText('Flagged')).toBeInTheDocument();
    expect(screen.getByText('High Risk')).toBeInTheDocument();
    expect(screen.getByText('Critical')).toBeInTheDocument();
    expect(screen.getByText('Pending')).toBeInTheDocument();
    expect(screen.getByText('Reviewed')).toBeInTheDocument();
    expect(screen.getByText('Cleared')).toBeInTheDocument();

    // Values
    expect(screen.getByText('1,250')).toBeInTheDocument();
    expect(screen.getAllByText('180').length).toBeGreaterThanOrEqual(2); // Flagged & Cleared
    expect(screen.getByText('31')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('95')).toBeInTheDocument();
  });

  it('triggers onFilterSelect when a stat card is clicked', () => {
    const handleFilter = vi.fn();
    render(
      <Dashboard
        stats={mockStats}
        isLoading={false}
        error={null}
        onRetry={vi.fn()}
        onFilterSelect={handleFilter}
      />
    );

    const criticalCard = screen.getByText('Critical').closest('div[role="button"]')!;
    fireEvent.click(criticalCard);
    expect(handleFilter).toHaveBeenCalledWith({ risk_level: 'CRITICAL' });

    const pendingCard = screen.getByText('Pending').closest('div[role="button"]')!;
    fireEvent.click(pendingCard);
    expect(handleFilter).toHaveBeenCalledWith({ status: 'PENDING_REVIEW' });
  });

  it('renders skeleton during initial loading', () => {
    render(
      <Dashboard
        stats={null}
        isLoading={true}
        error={null}
        onRetry={vi.fn()}
      />
    );

    expect(screen.getByRole('status', { name: /loading dashboard statistics/i })).toBeInTheDocument();
  });

  it('renders error state when stats request fails', () => {
    const handleRetry = vi.fn();
    render(
      <Dashboard
        stats={null}
        isLoading={false}
        error="Server 500 error"
        onRetry={handleRetry}
      />
    );

    expect(screen.getByText('Unable to load dashboard statistics')).toBeInTheDocument();
    expect(screen.getByText('Server 500 error')).toBeInTheDocument();

    const retryBtn = screen.getByRole('button', { name: /retry/i });
    fireEvent.click(retryBtn);
    expect(handleRetry).toHaveBeenCalled();
  });
});
