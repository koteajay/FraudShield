export interface HealthResponse {
  status: string;
}

export interface ApiInfoResponse {
  name: string;
  version: string;
  environment: string;
  status: string;
}

export type ConnectionStatus = 'checking' | 'connected' | 'error';
