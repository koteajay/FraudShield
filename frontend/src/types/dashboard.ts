/**
 * Dashboard statistics domain models.
 */

export interface DashboardStats {
  totalTransactions: number;
  flaggedTransactions: number;
  highRisk: number;
  critical: number;
  pendingReview: number;
  cleared: number;
  averageRiskScore?: number;
  fraudRatePercentage?: number;
}
