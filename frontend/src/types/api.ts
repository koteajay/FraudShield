/**
 * Standard API-related types and responses.
 */

export interface ApiError {
  message: string;
  statusCode?: number;
  details?: unknown;
  code?: string;
}

export interface HealthResponse {
  status: string;
  timestamp?: string;
  database?: string;
}

export interface ApiInfoResponse {
  name: string;
  version: string;
  environment: string;
  status: string;
}

export type ConnectionStatus = 'checking' | 'connected' | 'error';

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}
