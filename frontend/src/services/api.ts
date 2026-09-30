/**
 * Backward compatibility re-export module for services/api.
 * Re-exports from centralized api client and service modules.
 */

export * from './api/client';
export * from './api/health';
export * from './api/transactions';
export * from './api/dashboard';
export * from './api/fraud';
export * from './api/users';
export { API_BASE_URL } from '../config/env';
