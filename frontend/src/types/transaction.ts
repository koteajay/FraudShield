/**
 * Transaction domain models and query parameters.
 */

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type TransactionStatus = 'PENDING' | 'REVIEWED' | 'CLEARED' | 'FLAGGED';

export interface DeviceInfo {
  browser?: string;
  os?: string;
  deviceId?: string;
  ipAddress?: string;
  deviceType?: string;
}

export interface Transaction {
  id: string;
  userId: string;
  amount: number;
  currency: string;
  timestamp: string;
  status: TransactionStatus;
  riskLevel: RiskLevel;
  riskScore?: number;
  merchant?: string;
  category?: string;
  paymentMethod?: string;
  ipAddress?: string;
  deviceFingerprint?: string;
  deviceInfo?: DeviceInfo | string;
  location?: string;
  isFlagged?: boolean;
  notes?: string;
}

export interface CreateTransactionPayload {
  userId: string;
  amount: number;
  currency?: string;
  merchant?: string;
  category?: string;
  paymentMethod?: string;
  ipAddress?: string;
  deviceFingerprint?: string;
  location?: string;
}

export interface TransactionFilterParams {
  limit?: number;
  offset?: number;
  status?: TransactionStatus | 'ALL';
  riskLevel?: RiskLevel | 'ALL';
  search?: string;
  startDate?: string;
  endDate?: string;
}
