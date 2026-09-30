import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { StatusBadge } from '../components/transactions/StatusBadge';

describe('StatusBadge Component', () => {
  it('renders PENDING_REVIEW as "Pending Review"', () => {
    render(<StatusBadge status="PENDING_REVIEW" />);
    expect(screen.getByText('Pending Review')).toBeInTheDocument();
  });

  it('renders REVIEWED as "Reviewed"', () => {
    render(<StatusBadge status="REVIEWED" />);
    expect(screen.getByText('Reviewed')).toBeInTheDocument();
  });

  it('renders CLEARED as "Cleared"', () => {
    render(<StatusBadge status="CLEARED" />);
    expect(screen.getByText('Cleared')).toBeInTheDocument();
  });

  it('renders ESCALATED as "Escalated"', () => {
    render(<StatusBadge status="ESCALATED" />);
    expect(screen.getByText('Escalated')).toBeInTheDocument();
  });

  it('renders FLAGGED as "Flagged"', () => {
    render(<StatusBadge status="FLAGGED" />);
    expect(screen.getByText('Flagged')).toBeInTheDocument();
  });

  it('handles custom or unknown status gracefully', () => {
    render(<StatusBadge status="CUSTOM_STATUS" />);
    expect(screen.getByText('CUSTOM STATUS')).toBeInTheDocument();
  });
});
