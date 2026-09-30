import React, { useState, useEffect, useCallback } from 'react';
import { ConnectionStatusCard } from '../components/ConnectionStatusCard';
import { ArchitectureCard } from '../components/ArchitectureCard';
import { checkBackendHealth, fetchApiInfo, API_BASE_URL } from '../services/api';
import type { ConnectionStatus, HealthResponse, ApiInfoResponse } from '../types';

export const SystemHealthPage: React.FC = () => {
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

      try {
        const info = await fetchApiInfo();
        setApiInfo(info);
      } catch {
        // optional info
      }

      setStatus('connected');
    } catch (err: unknown) {
      setStatus('error');
      setHealthData(null);
      setApiInfo(null);
      setLatencyMs(null);
      setErrorMessage(
        err instanceof Error ? err.message : 'Failed to connect to backend server'
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    testConnection();
  }, [testConnection]);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      <div className="text-center max-w-2xl mx-auto">
        <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          System Health &amp; Architecture
        </h2>
        <p className="mt-2 text-xs sm:text-sm text-slate-400">
          Backend service diagnostics, database ping, and platform layer topology.
        </p>
      </div>

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

      <ArchitectureCard />
    </div>
  );
};
