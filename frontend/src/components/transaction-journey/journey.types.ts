export type JourneyEventType =
  | 'TRANSACTION'
  | 'LOGIN_ATTEMPT'
  | 'DEVICE_EVENT'
  | 'RISK_EVENT'
  | 'RULE_TRIGGER';

export type JourneySeverity =
  | 'INFO'
  | 'LOW'
  | 'MEDIUM'
  | 'HIGH'
  | 'CRITICAL';

export interface JourneyEvent {
  event_id: string;
  event_type: JourneyEventType;
  timestamp: string;
  transaction_id?: string | null;
  user_id: string;
  title: string;
  description: string;
  location?: string | null;
  device_id?: string | null;
  amount?: number | null;
  currency?: string | null;
  risk_score?: number | null;
  risk_level?: string | null;
  rule_id?: string | null;
  severity: JourneySeverity | string;
  metadata?: Record<string, any> | null;
}

export interface JourneyWindow {
  start: string;
  end: string;
}

export interface JourneySummary {
  transaction_count: number;
  login_attempt_count: number;
  rule_trigger_count: number;
  risk_event_count: number;
  new_device_detected: boolean;
  locations: string[];
  devices: string[];
}

export interface TransactionJourneyResponse {
  transaction_id: string;
  user_id: string;
  window: JourneyWindow;
  events: JourneyEvent[];
  summary: JourneySummary;
}
