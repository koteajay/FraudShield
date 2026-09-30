import React, { useState, useEffect, useCallback } from 'react';
import { ConnectionStatusCard } from '../components/ConnectionStatusCard';
import { ArchitectureCard } from '../components/ArchitectureCard';
import { checkBackendHealth, fetchApiInfo } from '../services/api/health';
import { API_BASE_URL } from '../config/env';
import type { ConnectionStatus, HealthResponse, ApiInfoResponse } from '../types';
import { ShieldCheck, Info, Sparkles } from 'lucide-react';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { EmptyState } from '../components/common/EmptyState';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';

export const HomePage: React.FC = () => {
  const [status, setStatus] = useState<ConnectionStatus>('checking');
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  const [apiInfo, setApiInfo] = useState<ApiInfoResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [activeUiDemo, setActiveUiDemo] = useState<'loading' | 'error' | 'empty'>('loading');

  const executeHealthCheck = useCallback(async (isCancelled?: () => boolean) => {
    const startTime = performance.now();
    try {
      const health = await checkBackendHealth();
      if (isCancelled && isCancelled()) return;

      const elapsed = Math.round(performance.now() - startTime);
      setLatencyMs(elapsed);
      setHealthData(health);

      // Attempt to load API info as well
      try {
        const info = await fetchApiInfo();
        if (!isCancelled || !isCancelled()) {
          setApiInfo(info);
        }
      } catch {
        // GET /api is optional extra info
      }

      setStatus('connected');
    } catch (err: unknown) {
      if (isCancelled && isCancelled()) return;

      setStatus('error');
      setHealthData(null);
      setApiInfo(null);
      setLatencyMs(null);

      if (
        err &&
        typeof err === 'object' &&
        'message' in err &&
        typeof (err as { message: unknown }).message === 'string'
      ) {
        setErrorMessage((err as { message: string }).message);
      } else if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage(
          'Failed to connect to backend server. Ensure backend is running at ' + API_BASE_URL
        );
      }
    } finally {
      if (!isCancelled || !isCancelled()) {
        setIsLoading(false);
      }
    }
  }, []);

  const handleManualRefresh = useCallback(() => {
    setIsLoading(true);
    setStatus('checking');
    setErrorMessage(null);
    executeHealthCheck();
  }, [executeHealthCheck]);

  useEffect(() => {
    let cancelled = false;
    // oxlint-disable-next-line react/set-state-in-effect
    executeHealthCheck(() => cancelled);
    return () => {
      cancelled = true;
    };
  }, [executeHealthCheck]);

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-10">
      {/* Hero Banner */}
      <div className="text-center max-w-2xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs font-semibold mb-4">
          <ShieldCheck className="w-3.5 h-3.5" />
          FraudShield Foundation Active
        </div>
        <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
          Explainable Fraud Detection &amp; Investigation
        </h2>
        <p className="mt-3 text-slate-400 text-sm leading-relaxed">
          Phase F0 &amp; F1 — Foundational architecture, centralized Axios HTTP client, typed API contracts, and reusable UI states.
        </p>
      </div>

      {/* Connectivity Status Card */}
      <ConnectionStatusCard
        status={status}
        healthData={healthData}
        apiInfo={apiInfo}
        errorMessage={errorMessage}
        apiUrl={API_BASE_URL}
        latencyMs={latencyMs}
        onRefresh={handleManualRefresh}
        isLoading={isLoading}
      />

      {/* Common UI States Foundation Preview */}
      <Card variant="subtle" className="border-slate-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-blue-400" />
            <h3 className="font-semibold text-white text-sm">
              Foundation Common UI States Preview
            </h3>
            <Badge variant="info" size="sm">F0 Design System</Badge>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setActiveUiDemo('loading')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                activeUiDemo === 'loading'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              LoadingState
            </button>
            <button
              type="button"
              onClick={() => setActiveUiDemo('error')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                activeUiDemo === 'error'
                  ? 'bg-rose-600 text-white shadow-sm'
                  : 'bg-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              ErrorState
            </button>
            <button
              type="button"
              onClick={() => setActiveUiDemo('empty')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                activeUiDemo === 'empty'
                  ? 'bg-slate-700 text-white shadow-sm'
                  : 'bg-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              EmptyState
            </button>
          </div>
        </div>

        <div className="pt-4">
          {activeUiDemo === 'loading' && (
            <LoadingState message="Fetching system telemetry and transaction stream..." size="md" />
          )}

          {activeUiDemo === 'error' && (
            <ErrorState
              title="Unable to load investigation records"
              message="The server returned an error while processing the request. Please retry or contact support."
              onRetry={() => setActiveUiDemo('loading')}
              retryLabel="Simulate Retry"
            />
          )}

          {activeUiDemo === 'empty' && (
            <EmptyState
              title="No transactions flagged"
              message="There are currently no high-risk transactions requiring reviewer attention."
              actionLabel="Refresh Monitor"
              onAction={handleManualRefresh}
            />
          )}
        </div>
      </Card>

      {/* Architecture Overview */}
      <ArchitectureCard />

      {/* Notice Banner */}
      <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800 flex items-start gap-3 text-xs text-slate-400">
        <Info className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-300">Phase F0/F1 Scope Adherence:</span> Feature screens (dashboard analytics, transaction tables, reviewer workflow, why-flagged panels) and mock business records are strictly omitted in this phase.
        </div>
      </div>
    </div>
  );
};

export default HomePage;
