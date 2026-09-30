/**
 * Types for User Behaviour Profile and baseline telemetry.
 */

export interface LocationSummary {
  city?: string;
  country?: string;
  transaction_count: number;
  latitude?: number;
  longitude?: number;
}

export interface DeviceSummary {
  device_id: string;
  fingerprint?: string;
  device_type?: string;
  first_seen_at?: string;
  last_seen_at?: string;
}

export interface MerchantSummary {
  merchant_id?: string;
  merchant_name?: string;
  merchant_category?: string;
  transaction_count: number;
}

export interface AmountRange {
  min: number;
  max: number;
}

export interface TimeWindow {
  start: string;
  end: string;
  start_hour: number;
  end_hour: number;
}

export interface UserBehaviourProfile {
  user_id: string;
  profile_status: 'INSUFFICIENT_DATA' | 'DEVELOPING' | 'ESTABLISHED' | string;

  average_transaction_amount?: number;
  minimum_transaction_amount?: number;
  maximum_transaction_amount?: number;
  normal_amount_range?: AmountRange;

  average_transactions_per_day: number;
  total_active_days: number;
  profile_transaction_count: number;

  normal_transaction_hours?: TimeWindow;
  known_locations: string[];
  detailed_locations?: LocationSummary[];

  known_merchants: string[];
  known_categories?: string[];
  detailed_merchants?: MerchantSummary[];

  known_devices: number;
  known_device_ids: string[];
  detailed_devices?: DeviceSummary[];

  failed_login_count: number;
  recent_failed_login_count: number;
  latest_failed_login_at?: string;

  profile_period_days: number;
  profile_period_start?: string;
  profile_period_end?: string;
}
