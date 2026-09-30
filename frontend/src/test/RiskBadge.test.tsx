import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { RiskBadge } from '../components/transactions/RiskBadge';

describe('RiskBadge Component', () => {
  it('renders LOW risk level correctly with accessible text', () => {
    render(<RiskBadge level="LOW" score={15} />);
    expect(screen.getByText('LOW')).toBeInTheDocument();
  });

  it('renders MEDIUM risk level correctly', () => {
    render(<RiskBadge level="MEDIUM" score={45} />);
    expect(screen.getByText('MEDIUM')).toBeInTheDocument();
  });

  it('renders HIGH risk level correctly', () => {
    render(<RiskBadge level="HIGH" score={68} />);
    expect(screen.getByText('HIGH')).toBeInTheDocument();
  });

  it('renders CRITICAL risk level with emphasis', () => {
    render(<RiskBadge level="CRITICAL" score={92} showScore={true} />);
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();
    expect(screen.getByText('92')).toBeInTheDocument();
  });

  it('handles unknown or unexpected risk levels gracefully with fallback', () => {
    render(<RiskBadge level="SOME_UNEXPECTED_TIER" />);
    expect(screen.getByText('SOME_UNEXPECTED_TIER')).toBeInTheDocument();
  });

  it('handles empty or null risk level gracefully', () => {
    render(<RiskBadge level="" />);
    expect(screen.getByText('UNKNOWN')).toBeInTheDocument();
  });
});
