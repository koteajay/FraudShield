import { API_BASE_URL } from './api';
import type { DashboardStats } from '../types/dashboard';

/**
 * Service for fetching reviewer dashboard statistics and KPIs.
 */
export async function getDashboardStats(params?: {
  start_date?: string;
  end_date?: string;
}): Promise<DashboardStats> {
  const query = new URLSearchParams();
  if (params?.start_date) query.set('start_date', params.start_date);
  if (params?.end_date) query.set('end_date', params.end_date);

  const qs = query.toString() ? `?${query.toString()}` : '';
  const response = await fetch(`${API_BASE_URL}/api/dashboard/stats${qs}`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    let errorMsg = `Dashboard stats request failed with status ${response.status}`;
    try {
      const errorData = await response.json();
      if (errorData?.detail) errorMsg = errorData.detail;
      else if (errorData?.error?.message) errorMsg = errorData.error.message;
    } catch {
      // fallback to status code message
    }
    throw new Error(errorMsg);
  }

  return response.json();
}
