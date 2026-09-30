import React from 'react';
import { CheckCircle2, XCircle, Loader2, RefreshCw, Server, Globe } from 'lucide-react';
import type { ConnectionStatus, HealthResponse, ApiInfoResponse } from '../types';

interface Props {
  status: ConnectionStatus;
  healthData: HealthResponse | null;
  apiInfo: ApiInfoResponse | null;
  errorMessage: string | null;
  apiUrl: string;
  latencyMs: number | null;
  onRefresh: () => void;
  isLoading: boolean;
}

export const ConnectionStatusCard: React.FC<Props> = ({
  status,
  healthData,
  apiInfo,
  errorMessage,
  apiUrl,
  latencyMs,
  onRefresh,
  isLoading,
}) => {
  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div>
          <div className="text-xs uppercase tracking-wider text-slate-400 font-semibold mb-1">
            System Connectivity
          </div>
          <div className="flex items-center gap-3">
            <span className="text-2xl font-bold text-white">Backend Status:</span>
            {status === 'connected' && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                <CheckCircle2 className="w-4 h-4" />
                Connected
              </span>
            )}
            {status === 'error' && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">
                <XCircle className="w-4 h-4" />
                Disconnected/Error
              </span>
            )}
            {status === 'checking' && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                <Loader2 className="w-4 h-4 animate-spin" />
                Checking...
              </span>
            )}
          </div>
        </div>

        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium transition-all duration-200 border border-slate-700 disabled:opacity-50 disabled:cursor-not-allowed hover:border-slate-600 active:scale-95"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          {isLoading ? 'Pinging API...' : 'Test Connection'}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
          <div className="flex items-center gap-2 text-xs font-medium text-slate-400 mb-2">
            <Globe className="w-4 h-4 text-blue-400" />
            Configured Backend URL
          </div>
          <div className="font-mono text-sm text-slate-200 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800 inline-block">
            {apiUrl}
          </div>
          <div className="mt-3 text-xs text-slate-500 flex items-center justify-between">
            <span>GET /health</span>
            {latencyMs !== null && (
              <span className="text-emerald-400 font-mono">Response: {latencyMs}ms</span>
            )}
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
          <div className="flex items-center gap-2 text-xs font-medium text-slate-400 mb-2">
            <Server className="w-4 h-4 text-purple-400" />
            API Response Payload
          </div>
          {status === 'connected' && healthData && (
            <pre className="font-mono text-xs text-emerald-300 bg-slate-900 p-2.5 rounded-lg border border-slate-800 overflow-x-auto">
              {JSON.stringify(
                {
                  health: healthData,
                  api: apiInfo || { note: 'GET /api available' },
                },
                null,
                2
              )}
            </pre>
          )}
          {status === 'error' && (
            <div className="text-xs text-rose-300 bg-rose-950/30 p-2.5 rounded-lg border border-rose-900/50">
              {errorMessage || 'Failed to connect to backend service. Ensure backend is running.'}
            </div>
          )}
          {status === 'checking' && (
            <div className="text-xs text-slate-400 italic py-2">
              Sending ping to {apiUrl}/health...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
