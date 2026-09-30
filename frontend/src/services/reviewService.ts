import { API_BASE_URL } from './api';
import type {
  ReviewHistoryResponse,
  ReviewStatusUpdateResponse,
} from '../types/review';

/**
 * Service for reviewer workflow actions and audit history.
 */

export async function getTransactionReviews(
  transactionId: string
): Promise<ReviewHistoryResponse> {
  const cleanId = transactionId.trim();
  const response = await fetch(
    `${API_BASE_URL}/api/transactions/${encodeURIComponent(cleanId)}/reviews`,
    {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
    }
  );

  if (!response.ok) {
    let errorMsg = `Reviews request failed with status ${response.status}`;
    try {
      const errorData = await response.json();
      if (errorData?.detail) errorMsg = errorData.detail;
      else if (errorData?.error?.message) errorMsg = errorData.error.message;
    } catch {
      // fallback
    }
    throw new Error(errorMsg);
  }

  return response.json();
}

export async function updateTransactionStatus(
  transactionId: string,
  status: string,
  note?: string
): Promise<ReviewStatusUpdateResponse> {
  const cleanId = transactionId.trim();
  const body: Record<string, string> = { status };
  if (note != null && note.trim().length > 0) {
    body.note = note.trim();
  }

  const response = await fetch(
    `${API_BASE_URL}/api/transactions/${encodeURIComponent(cleanId)}/status`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        'X-Reviewer-ID': 'reviewer-demo',
      },
      body: JSON.stringify(body),
    }
  );

  if (!response.ok) {
    let errorMsg = `Failed to update status to '${status}' (HTTP ${response.status})`;
    try {
      const errorData = await response.json();
      if (errorData?.detail) errorMsg = errorData.detail;
      else if (errorData?.error?.message) errorMsg = errorData.error.message;
    } catch {
      // fallback
    }
    throw new Error(errorMsg);
  }

  return response.json();
}
