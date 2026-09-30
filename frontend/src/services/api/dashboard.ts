/**
 * Dashboard API service module.
 * Provides aggregated metrics and summary fraud statistics.
 */

import apiClient from './client';
import type { DashboardStats } from '../../types/dashboard';

interface RawDashboardResponse {
  totalTransactions?: number;
  total_transactions?: number;
  flaggedTransactions?: number;
  flagged_transactions?: number;
  highRisk?: number;
  high_risk?: number;
  highRiskAlerts?: number;
  critical?: number;
  critical_count?: number;
  criticalAlerts?: number;
  pendingReview?: number;
  pending_review?: number;
  pendingReviews?: number;
  cleared?: number;
  cleared_transactions?: number;
  clearedTransactions?: number;
  averageRiskScore?: number;
  average_risk_score?: number;
  fraudRatePercentage?: number;
  fraud_rate_percentage?: number;
}

/**
 * Fetch aggregated statistics for fraud dashboard visualizations and KPIs.
 * Endpoint: GET /api/dashboard/stats
 */
export async function getDashboardStats(): Promise<DashboardStats> {
  const response = await apiClient.get<RawDashboardResponse>('/api/dashboard/stats');
  const raw = response.data || {};

  return {
    totalTransactions: raw.totalTransactions ?? raw.total_transactions ?? 0,
    flaggedTransactions: raw.flaggedTransactions ?? raw.flagged_transactions ?? 0,
    highRisk: raw.highRisk ?? raw.high_risk ?? raw.highRiskAlerts ?? 0,
    critical: raw.critical ?? raw.critical_count ?? raw.criticalAlerts ?? 0,
    pendingReview: raw.pendingReview ?? raw.pending_review ?? raw.pendingReviews ?? 0,
    cleared: raw.cleared ?? raw.cleared_transactions ?? raw.clearedTransactions ?? 0,
    averageRiskScore: raw.averageRiskScore ?? raw.average_risk_score,
    fraudRatePercentage: raw.fraudRatePercentage ?? raw.fraud_rate_percentage,
  };
}
