import { API_BASE_URL } from './api';
import type { TransactionJourneyResponse } from '../components/transaction-journey/journey.types';

export async function fetchTransactionJourney(
  transactionId: string,
  beforeMinutes: number = 30,
  afterMinutes: number = 30
): Promise<TransactionJourneyResponse> {
  const url = new URL(`${API_BASE_URL}/api/transactions/${encodeURIComponent(transactionId)}/journey`);
  url.searchParams.append('before_minutes', beforeMinutes.toString());
  url.searchParams.append('after_minutes', afterMinutes.toString());

  const response = await fetch(url.toString(), {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    let errorDetail = `Failed to fetch journey (${response.status})`;
    try {
      const errorJson = await response.json();
      if (errorJson.detail) {
        errorDetail = errorJson.detail;
      } else if (errorJson.error?.message) {
        errorDetail = errorJson.error.message;
      }
    } catch {
      // Use fallback error string
    }
    throw new Error(errorDetail);
  }

  return response.json();
}
