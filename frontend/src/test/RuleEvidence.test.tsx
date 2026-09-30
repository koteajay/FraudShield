import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { RuleEvidence } from '../components/investigation/RuleEvidence';

describe('RuleEvidence Component', () => {
  it('renders string, number, and boolean evidence attributes cleanly', () => {
    const evidence = {
      transaction_count: 5,
      window_minutes: 4,
      threshold: 5,
      is_flagged: true,
      note: 'Rapid succession',
    };

    render(<RuleEvidence evidence={evidence} />);

    // Labels
    expect(screen.getByText('Transaction Count')).toBeInTheDocument();
    expect(screen.getByText('Window Minutes')).toBeInTheDocument();
    expect(screen.getByText('Threshold')).toBeInTheDocument();
    expect(screen.getByText('Is Flagged')).toBeInTheDocument();
    expect(screen.getByText('Note')).toBeInTheDocument();

    // Values
    expect(screen.getAllByText('5').length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText('4')).toBeInTheDocument();
    expect(screen.getByText('Yes')).toBeInTheDocument();
    expect(screen.getByText('Rapid succession')).toBeInTheDocument();
  });

  it('renders array and nested object evidence values safely', () => {
    const evidence = {
      known_cities: ['Hyderabad', 'Bengaluru'],
      telemetry: { isp: 'Jio', asn: 12345 },
    };

    render(<RuleEvidence evidence={evidence} />);

    expect(screen.getByText('Known Cities')).toBeInTheDocument();
    expect(screen.getByText('Hyderabad, Bengaluru')).toBeInTheDocument();
    expect(screen.getByText('Telemetry')).toBeInTheDocument();
    expect(screen.getByText(JSON.stringify({ isp: 'Jio', asn: 12345 }))).toBeInTheDocument();
  });

  it('renders placeholder when evidence is empty or null', () => {
    render(<RuleEvidence evidence={null} />);
    expect(
      screen.getByText(/no specific telemetry evidence captured for this rule/i)
    ).toBeInTheDocument();
  });

  it('toggles technical details raw JSON view on button click', () => {
    const evidence = { ratio: 12.0, user_avg: 6250 };
    render(<RuleEvidence evidence={evidence} />);

    const toggleButton = screen.getByRole('button', { name: /technical details/i });
    expect(toggleButton).toBeInTheDocument();

    // Raw JSON should not be visible initially
    expect(screen.queryByText(/"ratio": 12/)).not.toBeInTheDocument();

    // Click to show
    fireEvent.click(toggleButton);
    expect(screen.getByText(/"ratio": 12/)).toBeInTheDocument();

    // Click to hide
    fireEvent.click(toggleButton);
    expect(screen.queryByText(/"ratio": 12/)).not.toBeInTheDocument();
  });
});
