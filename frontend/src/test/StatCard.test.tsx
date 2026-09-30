import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { StatCard } from '../components/dashboard/StatCard';
import { Flame } from 'lucide-react';

describe('StatCard Component', () => {
  it('renders title and formatted numeric value', () => {
    render(
      <StatCard
        title="Critical Risk"
        value={12}
        description="High urgency items"
        icon={Flame}
        variant="critical"
      />
    );

    expect(screen.getByText('Critical Risk')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('High urgency items')).toBeInTheDocument();
  });

  it('renders string values and badge text', () => {
    render(
      <StatCard
        title="Pending Review"
        value="42"
        badgeText="Urgent"
        icon={Flame}
        variant="info"
      />
    );

    expect(screen.getByText('Pending Review')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('Urgent')).toBeInTheDocument();
  });

  it('triggers onClick handler when interactive', () => {
    const handleClick = vi.fn();
    render(
      <StatCard
        title="Flagged"
        value={180}
        icon={Flame}
        onClick={handleClick}
      />
    );

    const card = screen.getByRole('button');
    fireEvent.click(card);
    expect(handleClick).toHaveBeenCalledTimes(1);

    fireEvent.keyDown(card, { key: 'Enter' });
    expect(handleClick).toHaveBeenCalledTimes(2);
  });
});
