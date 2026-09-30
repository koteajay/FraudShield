/**
 * Centralized Axios HTTP client configuration.
 * Normalizes requests, timeouts, and error handling.
 */

import axios, { AxiosError } from 'axios';
import type { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios';
import { API_BASE_URL } from '../../config/env';
import type { ApiError } from '../../types/api';

/**
 * Transforms raw Axios or unknown errors into clean, user-friendly ApiError objects.
 */
export function normalizeApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const axiosErr = error as AxiosError<{ detail?: string | unknown; message?: string }>;
    const status = axiosErr.response?.status;
    const responseData = axiosErr.response?.data;

    // Network / connection errors
    if (!axiosErr.response) {
      if (axiosErr.code === 'ECONNABORTED' || axiosErr.message.includes('timeout')) {
        return {
          message: 'Request timed out. The server took too long to respond.',
          code: axiosErr.code,
        };
      }
      return {
        message: 'Unable to connect to the backend server. Please verify the service is running at ' + API_BASE_URL,
        code: axiosErr.code || 'NETWORK_ERROR',
      };
    }

    // Specific HTTP status code mappings
    let message = 'An unexpected server error occurred.';

    if (responseData) {
      if (typeof responseData.detail === 'string') {
        message = responseData.detail;
      } else if (Array.isArray(responseData.detail) && responseData.detail.length > 0) {
        // Handle FastAPI validation error structure: [{ msg: "..." }]
        const first = responseData.detail[0];
        message = typeof first === 'object' && first?.msg ? String(first.msg) : 'Invalid input parameters.';
      } else if (typeof responseData.message === 'string') {
        message = responseData.message;
      }
    }

    if (!responseData || (!responseData.detail && !responseData.message)) {
      switch (status) {
        case 400:
          message = 'Bad request. Please review the submitted data.';
          break;
        case 401:
          message = 'Unauthorized access. Please log in.';
          break;
        case 403:
          message = 'Forbidden. You do not have permission to perform this action.';
          break;
        case 404:
          message = 'Requested resource was not found on the server.';
          break;
        case 422:
          message = 'Validation failed for request data.';
          break;
        case 500:
        case 502:
        case 503:
          message = 'Backend server encountered an error. Please try again later.';
          break;
        default:
          message = `Request failed with status code ${status}.`;
          break;
      }
    }

    return {
      message,
      statusCode: status,
      details: responseData,
      code: axiosErr.code,
    };
  }

  if (error instanceof Error) {
    return {
      message: error.message,
    };
  }

  return {
    message: 'An unknown error occurred while processing the request.',
  };
}

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    return config;
  },
  (error) => {
    return Promise.reject(normalizeApiError(error));
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error) => {
    return Promise.reject(normalizeApiError(error));
  }
);

export default apiClient;
