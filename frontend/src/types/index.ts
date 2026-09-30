export interface HealthResponse {
  status: string;
  database?: string;
}

export interface ApiInfoResponse {
  name: string;
  version: string;
  environment: string;
  status: string;
}

export type ConnectionStatus = 'checking' | 'connected' | 'error';

export * from './dashboard';
export * from './transaction';
export * from './profile';
export * from './review';
