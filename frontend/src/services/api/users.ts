/**
 * User and entity profile API service module.
 * Endpoints for retrieving user behavioral context and history.
 */

import apiClient from './client';
import type { UserProfile } from '../../types/user';

/**
 * Fetch profile and risk summary for an entity/user.
 * Endpoint: GET /api/users/:userId
 */
export async function getUserProfile(userId: string): Promise<UserProfile> {
  const response = await apiClient.get<UserProfile>(
    `/api/users/${encodeURIComponent(userId)}`
  );
  return response.data;
}
