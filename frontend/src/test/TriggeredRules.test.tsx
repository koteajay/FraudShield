import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { TriggeredRules } from '../components/investigation/TriggeredRules';
import type { RuleResultDetail } from '../types/transaction';

const mockRules: RuleResultDetail[] = [
  {
    rule_id: 'VELOCITY_CHECK',
    rule_name: 'Transaction Velocity',
    is_triggered: true,
    severity: 'HIGH',
    reason: '5 transactions occurred within 4 minutes.',
    score_contribution: 25,
    evidence: { transaction_count: 5, window_minutes: 4 },
  },
  {
    rule_id: 'AMOUNT_ANOMALY',
    rule_name: 'Unusual Transaction Amount',
    is_triggered: true,
    severity: 'CRITICAL',
    reason: 'Amount is 12x user normal average.',
    score_contribution: 30,
    evidence: { amount: 75000, user_average: 6250, ratio: 12.0 },
  },
  {
    rule_id: 'LOCATION_ANOMALY',
    rule_name: 'Impossible Geographical Location',
    is_triggered: true,
    severity: 'CRITICAL',
    reason: 'Impossible travel detected between Hyderabad and Delhi.',
    score_contribution: 35,
    evidence: { previous_location: 'Hyderabad', current_location: 'Delhi', travel_time_minutes: 8 },
  },
  {
    rule_id: 'NEW_MERCHANT',
    rule_name: 'New Merchant Category',
    is_triggered: false,
    severity: 'LOW',
    reason: 'Merchant is known.',
  },
];

describe('TriggeredRules Component', () => {
  it('renders all triggered rules with score contributions and reasons', () => {
    render(<TriggeredRules rules={mockRules} />);

    // Header count
    expect(screen.getByText('Triggered Rules (3)')).toBeInTheDocument();

    // Rule names
    expect(screen.getByText('Transaction Velocity')).toBeInTheDocument();
    expect(screen.getByText('Unusual Transaction Amount')).toBeInTheDocument();
    expect(screen.getByText('Impossible Geographical Location')).toBeInTheDocument();

    // Non-triggered rule should NOT appear
    expect(screen.queryByText('New Merchant Category')).not.toBeInTheDocument();

    // Score contributions
    expect(screen.getByText('+25')).toBeInTheDocument();
    expect(screen.getByText('+30')).toBeInTheDocument();
    expect(screen.getByText('+35')).toBeInTheDocument();
  });

  it('allows collapsing and expanding individual rule cards', () => {
    render(<TriggeredRules rules={mockRules} />);

    // Initially first rule is expanded; collapse all button closes them
    const collapseAllBtn = screen.getByRole('button', { name: /collapse all/i });
    fireEvent.click(collapseAllBtn);

    // After collapsing, evidence block is unmounted
    expect(screen.queryByText('Captured Evidence:')).not.toBeInTheDocument();

    // Click on the first rule header to re-expand it
    const firstRuleHeader = screen.getByRole('button', { name: /transaction velocity/i });
    fireEvent.click(firstRuleHeader);

    expect(screen.getByText('Captured Evidence:')).toBeInTheDocument();
    expect(screen.getByText('Transaction Count')).toBeInTheDocument();
  });

  it('renders clean placeholder when no rules triggered', () => {
    render(<TriggeredRules rules={[]} />);
    expect(screen.getByText('No Triggered Fraud Rules')).toBeInTheDocument();
  });
});
