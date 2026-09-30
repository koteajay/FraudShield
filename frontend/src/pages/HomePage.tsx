import React, { useState, useEffect, useCallback } from 'react';
import { ConnectionStatusCard } from '../components/ConnectionStatusCard';
import { ArchitectureCard } from '../components/ArchitectureCard';
import { TransactionJourney } from '../components/transaction-journey';
import { checkBackendHealth, fetchApiInfo, API_BASE_URL } from '../services/api';
import type { ConnectionStatus, HealthResponse, ApiInfoResponse } from '../types';
import { ShieldCheck } from 'lucide-react';

export const HomePage: React.FC = () => {
  const [status, setStatus] = useState<ConnectionStatus>('checking');
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  const [apiInfo, setApiInfo] = useState<ApiInfoResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const testConnection = useCallback(async () => {
    setIsLoading(true);
    setStatus('checking');
    setErrorMessage(null);

    const startTime = performance.now();
    try {
      const health = await checkBackendHealth();
      const elapsed = Math.round(performance.now() - startTime);
      setLatencyMs(elapsed);
      setHealthData(health);

      // Attempt to load API info as well
      try {
        const info = await fetchApiInfo();
        setApiInfo(info);
      } catch {
        // GET /api is optional extra info
      }

      setStatus('connected');
    } catch (err: unknown) {
      setStatus('error');
      setHealthData(null);
      setApiInfo(null);
      setLatencyMs(null);
      if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Failed to connect to backend server');
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    testConnection();
  }, [testConnection]);

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-10">
      {/* Hero Banner */}
      <div className="text-center max-w-2xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs font-semibold mb-4">
          <ShieldCheck className="w-3.5 h-3.5" />
          FraudShield Platform Active
        </div>
        <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
          Fraud Detection &amp; Investigation Platform
        </h2>
        <p className="mt-3 text-slate-400 text-sm leading-relaxed">
          Comprehensive fraud review platform featuring extensible heuristic rules, explainable risk scoring, user behaviour baselines, and chronological transaction journeys.
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
        onRefresh={testConnection}
        isLoading={isLoading}
      />

      {/* Transaction Journey Reviewer Tool (Phase 8) */}
      <TransactionJourney />

      {/* Architecture Overview */}
      <ArchitectureCard />
    </div>
  );
};
