/**
 * Transaction API service module.
 * Endpoints for transaction retrieval, ingestion, and status management.
 */

import apiClient from './client';
import type {
  Transaction,
  CreateTransactionPayload,
  TransactionFilterParams,
  TransactionStatus,
} from '../../types/transaction';

interface RawTransactionListResponse {
  transactions?: Transaction[];
  items?: Transaction[];
  data?: Transaction[];
}

/**
 * Fetch a list of transactions with optional filtering and pagination.
 * Endpoint: GET /api/transactions
 */
export async function getTransactions(
  params?: TransactionFilterParams
): Promise<Transaction[]> {
  const response = await apiClient.get<Transaction[] | RawTransactionListResponse>(
    '/api/transactions',
    { params }
  );

  const data = response.data;
  if (Array.isArray(data)) {
    return data;
  }
  if (data && Array.isArray(data.transactions)) {
    return data.transactions;
  }
  if (data && Array.isArray(data.items)) {
    return data.items;
  }
  if (data && Array.isArray(data.data)) {
    return data.data;
  }

  return [];
}

/**
 * Retrieve detailed data for a specific transaction by its unique identifier.
 * Endpoint: GET /api/transactions/:id
 */
export async function getTransactionById(id: string): Promise<Transaction> {
  const response = await apiClient.get<Transaction>(
    `/api/transactions/${encodeURIComponent(id)}`
  );
  return response.data;
}

/**
 * Submit a new transaction for ingestion and fraud evaluation.
 * Endpoint: POST /api/transactions
 */
export async function createTransaction(
  data: CreateTransactionPayload
): Promise<Transaction> {
  const response = await apiClient.post<Transaction>('/api/transactions', data);
  return response.data;
}

/**
 * Update the review or settlement status of a transaction.
 * Endpoint: PATCH /api/transactions/:id/status
 */
export async function updateTransactionStatus(
  id: string,
  status: TransactionStatus
): Promise<Transaction> {
  const response = await apiClient.patch<Transaction>(
    `/api/transactions/${encodeURIComponent(id)}/status`,
    { status }
  );
  return response.data;
}
