/**
 * Frontend environment configuration module.
 * Centralizes and validates environment variables.
 */

const rawApiUrl = import.meta.env.VITE_API_BASE_URL;

if (!rawApiUrl && import.meta.env.PROD) {
  // eslint-disable-next-line no-console
  console.error(
    '[FraudShield Config Error] Missing VITE_API_BASE_URL. Please set VITE_API_BASE_URL in your environment.'
  );
  throw new Error('Missing environment variable: VITE_API_BASE_URL is required.');
}

/**
 * Normalizes the API base URL by trimming trailing slashes,
 * falling back to http://localhost:8000 in development if unset.
 */
export const API_BASE_URL: string = (
  rawApiUrl || 'http://localhost:8000'
).replace(/\/+$/, '');

export const APP_CONFIG = {
  apiBaseUrl: API_BASE_URL,
  isDev: import.meta.env.DEV,
  isProd: import.meta.env.PROD,
  mode: import.meta.env.MODE,
} as const;

export default APP_CONFIG;
