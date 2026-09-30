import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { RiskScoreCard } from '../components/investigation/RiskScoreCard';

describe('RiskScoreCard Component', () => {
  it('renders critical score, gauge, and explanation accurately', () => {
    render(
      <RiskScoreCard
        score={90}
        level="CRITICAL"
        explanation="Multiple suspicious signals were detected across transaction behaviour, location, and device activity."
        ruleCount={3}
      />
    );

    // Score
    expect(screen.getByText('90')).toBeInTheDocument();
    expect(screen.getByText('/ 100')).toBeInTheDocument();

    // Level badge
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();

    // Progress bar
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '90');

    // Explanation
    expect(
      screen.getByText(/multiple suspicious signals were detected/i)
    ).toBeInTheDocument();

    // Triggered rules counter
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('clamps scores between 0 and 100', () => {
    render(<RiskScoreCard score={115} level="HIGH" />);
    expect(screen.getByText('100')).toBeInTheDocument();
  });
});
