/**
 * User and entity profile domain models.
 */

import type { RiskLevel } from './transaction';

export interface UserProfile {
  userId: string;
  email: string;
  name?: string;
  accountCreatedAt: string;
  riskLevel?: RiskLevel;
  totalTransactions?: number;
  flaggedCount?: number;
  isSuspended?: boolean;
  phoneNumber?: string;
  country?: string;
}
