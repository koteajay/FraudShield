import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { BehaviourProfileCard } from '../components/investigation/BehaviourProfileCard';
import type { UserBehaviourProfile } from '../types/profile';
import type { TransactionDetail } from '../types/transaction';

const mockProfile: UserBehaviourProfile = {
  user_id: 'user-123',
  profile_status: 'ESTABLISHED',
  average_transaction_amount: 6250,
  minimum_transaction_amount: 1000,
  maximum_transaction_amount: 15000,
  normal_amount_range: { min: 1000, max: 15000 },
  average_transactions_per_day: 3.2,
  total_active_days: 45,
  profile_transaction_count: 144,
  normal_transaction_hours: {
    start: '08:00',
    end: '22:00',
    start_hour: 8,
    end_hour: 22,
  },
  known_locations: ['Hyderabad', 'Bengaluru'],
  known_merchants: ['Amazon India', 'Swiggy', 'Flipkart'],
  known_devices: 2,
  known_device_ids: ['device-a', 'device-b'],
  failed_login_count: 1,
  recent_failed_login_count: 0,
  profile_period_days: 60,
};

const mockTx: TransactionDetail = {
  id: 'txn-123',
  transaction_reference: 'TXN-REF-123',
  user_id: 'user-123',
  amount: 75000,
  currency: 'INR',
  timestamp: '2026-09-30T03:15:00',
  location: 'Delhi',
  city: 'Delhi',
  risk_score: 90,
  risk_level: 'CRITICAL',
  status: 'PENDING_REVIEW',
  review_status: 'PENDING_REVIEW',
  risk: { score: 90, level: 'CRITICAL' },
};

describe('BehaviourProfileCard Component', () => {
  it('renders established user profile baseline data and deviation indicators', () => {
    render(
      <BehaviourProfileCard
        profile={mockProfile}
        transaction={mockTx}
        isLoading={false}
      />
    );

    // Profile status
    expect(screen.getByText('ESTABLISHED')).toBeInTheDocument();

    // Baseline metrics
    expect(screen.getByText('₹6,250')).toBeInTheDocument();
    expect(screen.getByText(/3.2/)).toBeInTheDocument();
    expect(screen.getByText('08:00 – 22:00')).toBeInTheDocument();

    // Inventory chips
    expect(screen.getByText('Hyderabad')).toBeInTheDocument();
    expect(screen.getByText('device-a')).toBeInTheDocument();
    expect(screen.getByText('Amazon India')).toBeInTheDocument();

    // Visual deviation alerts (₹75,000 is 12x average, Delhi is unknown location, 03:15 is outside normal hours)
    expect(screen.getByText('Observed Deviations from Baseline')).toBeInTheDocument();
    expect(screen.getByText(/Amount is 12.0× user average/i)).toBeInTheDocument();
    expect(screen.getByText(/Unrecognized location: “Delhi”/i)).toBeInTheDocument();
    expect(screen.getByText(/Transaction time is outside established activity window/i)).toBeInTheDocument();
  });

  it('renders error state and retry button when profile fetch fails', () => {
    const handleRetry = vi.fn();
    render(
      <BehaviourProfileCard
        profile={null}
        transaction={mockTx}
        isLoading={false}
        error="Profile service unavailable"
        onRetry={handleRetry}
      />
    );

    expect(screen.getByText('Profile service unavailable')).toBeInTheDocument();
    const retryBtn = screen.getByRole('button', { name: /retry profile/i });
    fireEvent.click(retryBtn);
    expect(handleRetry).toHaveBeenCalled();
  });
});
