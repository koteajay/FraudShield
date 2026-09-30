/**
 * System and Health check service module.
 * Communicates with backend /health and /api endpoints.
 */

import apiClient from './client';
import type { HealthResponse, ApiInfoResponse } from '../../types/api';

/**
 * Checks connectivity and system status against GET /health.
 */
export async function checkBackendHealth(): Promise<HealthResponse> {
  const response = await apiClient.get<HealthResponse>('/health');
  return response.data;
}

/**
 * Fetches backend service metadata against GET /api.
 */
export async function fetchApiInfo(): Promise<ApiInfoResponse> {
  const response = await apiClient.get<ApiInfoResponse>('/api');
  return response.data;
}
