import { describe, it, expect } from 'vitest';
import { formatCurrency, formatTimestamp } from '../utils/formatters';

describe('Formatters Utility', () => {
  it('formats INR amounts cleanly', () => {
    const formatted = formatCurrency(75000, 'INR');
    expect(formatted).toContain('75,000');
  });

  it('formats USD amounts cleanly', () => {
    const formatted = formatCurrency(2500, 'USD');
    expect(formatted).toContain('2,500');
  });

  it('handles unknown currencies gracefully without crashing', () => {
    const formatted = formatCurrency(500, 'XYZ');
    expect(formatted).toContain('500');
    expect(formatted).toContain('XYZ');
  });

  it('formats timestamps into localized readable format', () => {
    const formatted = formatTimestamp('2026-09-30T10:21:00Z');
    expect(formatted).toContain('2026');
    expect(formatted).toContain('Sep');
  });

  it('handles invalid timestamp gracefully', () => {
    expect(formatTimestamp('')).toBe('—');
    expect(formatTimestamp('invalid-date')).toBe('invalid-date');
  });
});
