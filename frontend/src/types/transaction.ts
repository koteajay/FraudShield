/**
 * Types for Transactions, Risk Evaluations, and Review Operations
 */

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type TransactionStatus =
  | 'PENDING'
  | 'APPROVED'
  | 'DECLINED'
  | 'FLAGGED'
  | 'UNDER_REVIEW';

export type ReviewStatus =
  | 'NOT_REQUIRED'
  | 'PENDING_REVIEW'
  | 'IN_REVIEW'
  | 'REVIEWED'
  | 'CLEARED'
  | 'RESOLVED_LEGITIMATE'
  | 'RESOLVED_FRAUD'
  | 'ESCALATED';

export interface Transaction {
  id: string;
  transaction_reference: string;
  user_id: string;
  amount: number;
  currency: string;
  merchant_name?: string;
  location?: string;
  city?: string;
  country?: string;
  timestamp: string;
  risk_score: number;
  risk_level: RiskLevel | string;
  status: TransactionStatus | string;
  review_status: ReviewStatus | string;
}

export interface PaginatedTransactionsResponse {
  items: Transaction[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface TransactionFilterParams {
  page?: number;
  page_size?: number;
  risk_level?: string;
  status?: string;
  user_id?: string;
  start_date?: string;
  end_date?: string;
  min_score?: number;
  max_score?: number;
  merchant?: string;
  location?: string;
}

export interface RuleResultDetail {
  rule_id: string;
  rule_name: string;
  is_triggered: boolean;
  severity: string;
  reason?: string;
  evidence?: Record<string, unknown>;
  score_contribution?: number;
  details?: {
    reason?: string;
    evidence?: Record<string, unknown>;
    score_contribution?: number;
  };
}

export interface FraudFlagDetail {
  id: string;
  flag_type: string;
  severity: string;
  reason: string;
  created_at: string | null;
}

export interface AccountTakeoverDetail {
  is_at_risk: boolean;
  risk_level: string;
  signal_count: number;
  signals: Record<string, boolean>;
  explanation: string;
}

export interface TransactionDetail extends Transaction {
  merchant_id?: string;
  merchant_category?: string;
  latitude?: number;
  longitude?: number;
  risk: {
    score: number;
    level: RiskLevel | string;
    explanation?: string;
  };
  device?: {
    device_id?: string;
    browser?: string;
    operating_system?: string;
    ip_address?: string;
    is_trusted?: boolean;
    is_new?: boolean;
    first_seen_at?: string;
    last_seen_at?: string;
  };
  account_takeover?: AccountTakeoverDetail;
  rule_results?: RuleResultDetail[];
  fraud_flags?: FraudFlagDetail[];
}

export interface ReviewStatusUpdateResponse {
  id: string;
  transaction_reference: string;
  previous_review_status: string;
  review_status: string;
  updated_at: string;
}
