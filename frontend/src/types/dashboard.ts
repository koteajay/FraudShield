/**
 * Types for Reviewer Dashboard Statistics and KPIs
 */

export interface DashboardStats {
  total_transactions: number;
  flagged: number;
  pending_review: number;
  high_risk_transactions: number;
  critical_risk_transactions: number;
  cleared_transactions: number;
  reviewed_transactions: number;
  average_risk_score: number;
  new_devices: number;
  account_takeover_risk_events: number;
}
