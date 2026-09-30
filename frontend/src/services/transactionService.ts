import { API_BASE_URL } from './api';
import type {
  PaginatedTransactionsResponse,
  TransactionDetail,
  TransactionFilterParams,
  ReviewStatusUpdateResponse,
} from '../types/transaction';

/**
 * Service for fetching and updating transactions.
 */
export async function getTransactions(
  params?: TransactionFilterParams
): Promise<PaginatedTransactionsResponse> {
  const query = new URLSearchParams();

  if (params?.page != null) query.set('page', params.page.toString());
  if (params?.page_size != null) query.set('page_size', params.page_size.toString());
  if (params?.risk_level) query.set('risk_level', params.risk_level);
  if (params?.status) query.set('status', params.status);
  if (params?.user_id) query.set('user_id', params.user_id);
  if (params?.start_date) query.set('start_date', params.start_date);
  if (params?.end_date) query.set('end_date', params.end_date);
  if (params?.min_score != null) query.set('min_score', params.min_score.toString());
  if (params?.max_score != null) query.set('max_score', params.max_score.toString());
  if (params?.merchant) query.set('merchant', params.merchant);
  if (params?.location) query.set('location', params.location);

  const qs = query.toString() ? `?${query.toString()}` : '';
  const response = await fetch(`${API_BASE_URL}/api/transactions${qs}`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    let errorMsg = `Transactions request failed with status ${response.status}`;
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

export async function getTransaction(id: string): Promise<TransactionDetail> {
  const response = await fetch(`${API_BASE_URL}/api/transactions/${encodeURIComponent(id)}`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    let errorMsg = `Transaction '${id}' request failed with status ${response.status}`;
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
  id: string,
  status: string,
  note?: string
): Promise<ReviewStatusUpdateResponse> {
  const payload: Record<string, string> = { status };
  if (note != null && note.trim().length > 0) {
    payload.note = note.trim();
  }

  const response = await fetch(
    `${API_BASE_URL}/api/transactions/${encodeURIComponent(id)}/status`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        'X-Reviewer-ID': 'reviewer-demo',
      },
      body: JSON.stringify(payload),
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
