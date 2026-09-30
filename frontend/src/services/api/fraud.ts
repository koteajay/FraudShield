/**
 * Fraud Analysis & Flags API service module.
 * Endpoints for explainable rules and fraud flags.
 */

import apiClient from './client';
import type { FraudFlag, FraudAssessment } from '../../types/fraud';

/**
 * Fetch all triggered fraud flags for a given transaction.
 * Endpoint: GET /api/fraud/flags
 */
export async function getFraudFlags(
  transactionId: string
): Promise<FraudFlag[]> {
  const response = await apiClient.get<FraudFlag[] | { flags: FraudFlag[] }>(
    '/api/fraud/flags',
    {
      params: { transaction_id: transactionId },
    }
  );

  const data = response.data;
  if (Array.isArray(data)) {
    return data;
  }
  if (data && Array.isArray(data.flags)) {
    return data.flags;
  }
  return [];
}

/**
 * Fetch comprehensive fraud assessment including risk score, factors, and explanations.
 * Endpoint: GET /api/fraud/assessments/:transactionId
 */
export async function getFraudAssessment(
  transactionId: string
): Promise<FraudAssessment> {
  const response = await apiClient.get<FraudAssessment | { assessment: FraudAssessment }>(
    `/api/fraud/assessments/${encodeURIComponent(transactionId)}`
  );

  const data = response.data;
  if (data && 'assessment' in data && data.assessment) {
    return data.assessment;
  }
  return data as FraudAssessment;
}
