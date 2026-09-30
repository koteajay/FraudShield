import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { TransactionInvestigation } from '../pages/TransactionInvestigation';
import * as transactionService from '../services/transactionService';
import * as profileService from '../services/profileService';
import * as journeyService from '../services/journeyService';
import type { TransactionDetail } from '../types/transaction';
import type { UserBehaviourProfile } from '../types/profile';
import type { TransactionJourneyResponse } from '../components/transaction-journey/journey.types';

const mockTxDetail: TransactionDetail = {
  id: 'txn-demo-123',
  transaction_reference: 'TXN-REF-123',
  user_id: 'user-demo-456',
  amount: 75000,
  currency: 'INR',
  merchant_name: 'Luxury Electronics Delhi',
  location: 'Delhi',
  city: 'Delhi',
  timestamp: '2026-09-30T10:21:00Z',
  risk_score: 90,
  risk_level: 'CRITICAL',
  status: 'PENDING_REVIEW',
  review_status: 'PENDING_REVIEW',
  risk: {
    score: 90,
    level: 'CRITICAL',
    explanation: 'Multiple suspicious signals were detected across transaction behaviour, location, and device activity.',
  },
  device: {
    device_id: 'device-x',
    browser: 'Chrome',
    operating_system: 'Windows',
    ip_address: '103.21.144.12',
    is_new: true,
    is_trusted: false,
    first_seen_at: '2026-09-30T10:21:00Z',
    last_seen_at: '2026-09-30T10:21:00Z',
  },
  account_takeover: {
    is_at_risk: true,
    risk_level: 'HIGH',
    signal_count: 3,
    signals: {
      new_device: true,
      unusual_time: false,
      new_location: true,
      failed_login: true,
      unusual_amount: true,
    },
    explanation: 'Potential account takeover risk detected because multiple suspicious signals were observed.',
  },
  rule_results: [
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
      reason: 'Amount is 12x user average.',
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
      evidence: { previous_location: 'Hyderabad', current_location: 'Delhi' },
    },
  ],
};

const mockProfile: UserBehaviourProfile = {
  user_id: 'user-demo-456',
  profile_status: 'ESTABLISHED',
  average_transaction_amount: 6250,
  average_transactions_per_day: 3.2,
  total_active_days: 30,
  profile_transaction_count: 96,
  normal_amount_range: { min: 1000, max: 15000 },
  normal_transaction_hours: {
    start: '08:00',
    end: '22:00',
    start_hour: 8,
    end_hour: 22,
  },
  known_locations: ['Hyderabad'],
  known_merchants: ['Swiggy', 'Amazon India'],
  known_devices: 1,
  known_device_ids: ['device-a'],
  failed_login_count: 1,
  recent_failed_login_count: 1,
  profile_period_days: 30,
};

const mockJourney: TransactionJourneyResponse = {
  transaction_id: 'txn-demo-123',
  user_id: 'user-demo-456',
  window: {
    start: '2026-09-30T09:51:00Z',
    end: '2026-09-30T10:51:00Z',
  },
  events: [
    {
      event_id: 'event-1',
      timestamp: '2026-09-30T10:02:00Z',
      event_type: 'TRANSACTION',
      title: 'Normal Transaction',
      description: 'Transaction of ₹2,000 at Grocery Store',
      amount: 2000,
      currency: 'INR',
      location: 'Hyderabad',
      device_id: 'device-a',
      severity: 'LOW',
      risk_score: 10,
      metadata: {},
      user_id: 'user-demo-456',
    },
    {
      event_id: 'event-2',
      timestamp: '2026-09-30T10:21:00Z',
      event_type: 'TRANSACTION',
      title: 'Suspicious Target Transaction',
      description: 'Transaction of ₹75,000 at Luxury Electronics Delhi',
      amount: 75000,
      currency: 'INR',
      location: 'Delhi',
      device_id: 'device-x',
      severity: 'CRITICAL',
      risk_score: 90,
      metadata: {},
      user_id: 'user-demo-456',
    },
    {
      event_id: 'event-3',
      timestamp: '2026-09-30T10:23:00Z',
      event_type: 'LOGIN_ATTEMPT',
      title: 'Failed Login Attempt',
      description: 'Failed login password attempt on device-x',
      location: 'Delhi',
      device_id: 'device-x',
      severity: 'HIGH',
      risk_score: 65,
      metadata: {},
      user_id: 'user-demo-456',
    },
  ],
  summary: {
    transaction_count: 2,
    login_attempt_count: 1,
    rule_trigger_count: 3,
    risk_event_count: 2,
    new_device_detected: true,
    locations: ['Hyderabad', 'Delhi'],
    devices: ['device-a', 'device-x'],
  },
};

describe('TransactionInvestigation Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(transactionService, 'getTransaction').mockResolvedValue(mockTxDetail);
    vi.spyOn(profileService, 'getUserProfile').mockResolvedValue(mockProfile);
    vi.spyOn(journeyService, 'fetchTransactionJourney').mockResolvedValue(mockJourney);
    vi.spyOn(transactionService, 'updateTransactionStatus').mockResolvedValue({
      id: 'txn-demo-123',
      transaction_reference: 'TXN-REF-123',
      previous_review_status: 'PENDING_REVIEW',
      review_status: 'REVIEWED',
      updated_at: new Date().toISOString(),
    });
  });

  const renderWithRouter = (initialEntry = '/transactions/txn-demo-123') => {
    return render(
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="/transactions/:id" element={<TransactionInvestigation />} />
          <Route path="/dashboard" element={<div>Dashboard Page</div>} />
        </Routes>
      </MemoryRouter>
    );
  };

  it('renders all investigation sections and data from the backend APIs', async () => {
    renderWithRouter();

    // 1. Header Information
    expect(await screen.findByText('TXN-REF-123')).toBeInTheDocument();
    expect(screen.getByText('user-demo-456')).toBeInTheDocument();
    expect(screen.getAllByText('Delhi').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Luxury Electronics Delhi')).toBeInTheDocument();
    expect(screen.getByText('₹75,000')).toBeInTheDocument();

    // 2. Why Flagged & Risk Score
    expect(screen.getByText('Why Flagged?')).toBeInTheDocument();
    expect(screen.getByText('90')).toBeInTheDocument();
    expect(screen.getAllByText('CRITICAL').length).toBeGreaterThanOrEqual(1);
    expect(
      screen.getByText(/multiple suspicious signals were detected/i)
    ).toBeInTheDocument();

    // Triggered rules
    expect(screen.getByText('Transaction Velocity')).toBeInTheDocument();
    expect(screen.getByText('Unusual Transaction Amount')).toBeInTheDocument();
    expect(screen.getByText('Impossible Geographical Location')).toBeInTheDocument();
    expect(screen.getByText('+25')).toBeInTheDocument();
    expect(screen.getByText('+30')).toBeInTheDocument();
    expect(screen.getByText('+35')).toBeInTheDocument();

    // 3. Behaviour Profile
    expect(screen.getByText('User Behaviour Profile')).toBeInTheDocument();
    expect(screen.getByText('ESTABLISHED')).toBeInTheDocument();
    expect(screen.getByText('₹6,250')).toBeInTheDocument();

    // 4. Device Information
    expect(screen.getByText('Device Information')).toBeInTheDocument();
    expect(screen.getByText('NEW DEVICE ⚠️')).toBeInTheDocument();
    expect(screen.getByText('device-x')).toBeInTheDocument();
    expect(screen.getByText('Chrome')).toBeInTheDocument();

    // 5. Account Takeover
    expect(screen.getByText('Account Takeover (ATO) Assessment')).toBeInTheDocument();
    expect(screen.getByText('3 signals')).toBeInTheDocument();

    // 6. Transaction Journey
    expect(await screen.findByText('Chronological Transaction Journey')).toBeInTheDocument();
    expect(screen.getByText('Suspicious Target Transaction')).toBeInTheDocument();
  });

  it('allows updating review status from the header action', async () => {
    renderWithRouter();

    await screen.findByText('TXN-REF-123');

    const statusSelect = screen.getByRole('combobox', { name: /update review status/i });
    expect(statusSelect).toBeInTheDocument();

    fireEvent.change(statusSelect, { target: { value: 'REVIEWED' } });

    await waitFor(() => {
      expect(transactionService.updateTransactionStatus).toHaveBeenCalledWith(
        'txn-demo-123',
        'REVIEWED'
      );
    });
  });

  it('renders not found error screen when transaction fetch rejects', async () => {
    vi.spyOn(transactionService, 'getTransaction').mockRejectedValue(
      new Error('Transaction does not exist')
    );

    renderWithRouter('/transactions/txn-unknown');

    expect(await screen.findByText('Transaction Not Found')).toBeInTheDocument();
    expect(screen.getByText('Transaction does not exist')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /back to transactions/i })).toBeInTheDocument();
  });
});
