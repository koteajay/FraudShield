import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { AccountTakeoverCard } from '../components/investigation/AccountTakeoverCard';
import type { AccountTakeoverDetail } from '../types/transaction';

describe('AccountTakeoverCard Component', () => {
  it('renders ATO threat level, signal count, checklist, and explanation', () => {
    const ato: AccountTakeoverDetail = {
      is_at_risk: true,
      risk_level: 'HIGH',
      signal_count: 3,
      signals: {
        new_device: true,
        unusual_time: true,
        new_location: true,
        failed_login: false,
        unusual_amount: false,
      },
      explanation: 'Potential account takeover risk detected because multiple suspicious signals were observed.',
    };

    render(<AccountTakeoverCard ato={ato} />);

    expect(screen.getByText('Account Takeover (ATO) Assessment')).toBeInTheDocument();
    expect(screen.getByText('HIGH')).toBeInTheDocument();
    expect(screen.getByText('3 signals')).toBeInTheDocument();
    expect(
      screen.getByText(/potential account takeover risk detected/i)
    ).toBeInTheDocument();

    // Checklist items
    expect(screen.getByText('New Device Detected')).toBeInTheDocument();
    expect(screen.getByText('Unusual Transaction Time')).toBeInTheDocument();
    expect(screen.getByText('Unrecognized Location')).toBeInTheDocument();
    expect(screen.getByText('Recent Failed Login Activity')).toBeInTheDocument();
  });

  it('renders null when ato assessment is null or undefined', () => {
    const { container } = render(<AccountTakeoverCard ato={null} />);
    expect(container.firstChild).toBeNull();
  });
});
