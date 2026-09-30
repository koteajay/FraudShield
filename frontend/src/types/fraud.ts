/**
 * Fraud flags, rules, and explanation data models.
 */

import type { RiskLevel } from './transaction';

export interface FraudRuleResult {
  id?: string;
  ruleName: string;
  ruleCategory?: string;
  isTriggered: boolean;
  reason?: string;
  evidence?: string | Record<string, unknown> | null;
  scoreContribution?: number;
  severity?: RiskLevel;
}

export interface FraudFlag {
  id: string;
  transactionId: string;
  ruleName: string;
  ruleCategory?: string;
  severity: RiskLevel;
  scoreImpact?: number;
  description: string;
  triggeredAt: string;
  metadata?: Record<string, unknown>;
}

export interface FraudAssessment {
  transactionId: string;
  riskScore: number;
  riskLevel: RiskLevel;
  flags?: FraudFlag[];
  rules?: FraudRuleResult[];
  explanation?: string;
  summary?: string;
  evaluatedAt?: string;
}
