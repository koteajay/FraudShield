import { API_BASE_URL } from './api';
import type { UserBehaviourProfile } from '../types/profile';

/**
 * Service for retrieving user behavioural profiles and baseline metrics.
 */
export async function getUserProfile(userId: string): Promise<UserBehaviourProfile> {
  const cleanId = userId.trim();
  const response = await fetch(`${API_BASE_URL}/api/users/${encodeURIComponent(cleanId)}/profile`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    let errorMsg = `User profile request failed with status ${response.status}`;
    try {
      const errorData = await response.json();
      if (errorData?.detail) errorMsg = errorData.detail;
      else if (errorData?.error?.message) errorMsg = errorData.error.message;
    } catch {
      // fallback
    }
    throw new Error(errorMsg);
  }

  return response.json();
}
