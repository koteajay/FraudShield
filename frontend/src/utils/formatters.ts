/**
 * Utility functions for formatting amounts, currencies, and timestamps.
 */

/**
 * Formats a monetary amount into a clean, localized currency string.
 * Supports INR (₹), USD ($), EUR (€), GBP (£), and gracefully falls back to code + amount.
 */
export function formatCurrency(amount: number, currency: string = 'INR'): string {
  if (amount == null || isNaN(amount)) {
    return '0';
  }

  const cleanCurrency = (currency || 'INR').toUpperCase().trim();

  try {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: cleanCurrency,
      maximumFractionDigits: amount % 1 === 0 ? 0 : 2,
    }).format(amount);
  } catch {
    // Fallback if the currency code is unrecognized
    const formattedAmount = amount.toLocaleString('en-US', {
      maximumFractionDigits: 2,
    });
    return `${cleanCurrency} ${formattedAmount}`;
  }
}

/**
 * Formats an ISO datetime string into human-readable reviewer format.
 * Example: "30 Sep 2026, 10:21 AM"
 */
export function formatTimestamp(isoString: string): string {
  if (!isoString) return '—';

  try {
    const date = new Date(isoString);
    if (isNaN(date.getTime())) {
      return isoString;
    }

    return new Intl.DateTimeFormat('en-US', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    }).format(date);
  } catch {
    return isoString;
  }
}

/**
 * Formats time only for compact table display.
 * Example: "10:21 AM"
 */
export function formatTimeOnly(isoString: string): string {
  if (!isoString) return '—';

  try {
    const date = new Date(isoString);
    if (isNaN(date.getTime())) {
      return isoString;
    }

    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    }).format(date);
  } catch {
    return isoString;
  }
}
