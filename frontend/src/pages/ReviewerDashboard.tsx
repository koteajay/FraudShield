import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Dashboard } from '../components/dashboard/Dashboard';
import { TransactionTable } from '../components/transactions/TransactionTable';
import { getDashboardStats } from '../services/dashboardService';
import { getTransactions, updateTransactionStatus } from '../services/transactionService';
import type { DashboardStats } from '../types/dashboard';
import type {
  Transaction,
  TransactionFilterParams,
  PaginatedTransactionsResponse,
} from '../types/transaction';
import { ShieldCheck, RefreshCw } from 'lucide-react';

export const ReviewerDashboard: React.FC = () => {
  const navigate = useNavigate();

  // Dashboard Stats State
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isStatsLoading, setIsStatsLoading] = useState<boolean>(true);
  const [statsError, setStatsError] = useState<string | null>(null);

  // Transactions Table State
  const [transactionsData, setTransactionsData] =
    useState<PaginatedTransactionsResponse | null>(null);
  const [isTxLoading, setIsTxLoading] = useState<boolean>(true);
  const [txError, setTxError] = useState<string | null>(null);

  // Active Filters & Pagination
  const [filters, setFilters] = useState<TransactionFilterParams>({
    page: 1,
    page_size: 20,
    risk_level: undefined,
    status: undefined,
    user_id: undefined,
  });

  // Load Dashboard Statistics
  const loadStats = useCallback(async () => {
    setIsStatsLoading(true);
    setStatsError(null);
    try {
      const data = await getDashboardStats();
      setStats(data);
    } catch (err: unknown) {
      setStatsError(
        err instanceof Error ? err.message : 'Failed to load dashboard statistics'
      );
    } finally {
      setIsStatsLoading(false);
    }
  }, []);

  // Load Transactions Table
  const loadTransactions = useCallback(async (currentFilters: TransactionFilterParams) => {
    setIsTxLoading(true);
    setTxError(null);
    try {
      const data = await getTransactions(currentFilters);
      setTransactionsData(data);
    } catch (err: unknown) {
      setTxError(
        err instanceof Error ? err.message : 'Failed to load transactions'
      );
    } finally {
      setIsTxLoading(false);
    }
  }, []);

  // Initial Load
  useEffect(() => {
    loadStats();
  }, [loadStats]);

  useEffect(() => {
    loadTransactions(filters);
  }, [loadTransactions, filters]);

  // Combined Refresh
  const handleRefreshAll = () => {
    loadStats();
    loadTransactions(filters);
  };

  // Filter Updates
  const handleFilterChange = (newFilters: Partial<TransactionFilterParams>) => {
    setFilters((prev) => ({
      ...prev,
      ...newFilters,
    }));
  };

  // KPI Card Selection Filter
  const handleFilterSelect = (cardFilter: { risk_level?: string; status?: string }) => {
    setFilters((prev) => ({
      ...prev,
      risk_level: cardFilter.risk_level,
      status: cardFilter.status,
      page: 1,
    }));
  };

  // Quick Review Status Update from Row Action
  const handleStatusChange = async (id: string, newStatus: string) => {
    await updateTransactionStatus(id, newStatus);
    // Refresh both table and dashboard statistics without full reload
    loadStats();
    loadTransactions(filters);
  };

  // Row Selection -> Navigate to Detail Page
  const handleSelectTransaction = (transaction: Transaction) => {
    navigate(`/transactions/${encodeURIComponent(transaction.id)}`);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs font-semibold mb-2">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>FraudShield Operational Center</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Reviewer Console
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Real-time fraud surveillance, explainable risk scoring triage, and reviewer queues.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRefreshAll}
            type="button"
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-medium text-slate-200 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isStatsLoading || isTxLoading ? 'animate-spin text-blue-400' : ''}`} />
            <span>Refresh All</span>
          </button>
        </div>
      </div>

      {/* 1. Summary Statistics KPIs */}
      <section aria-labelledby="kpis-heading">
        <h2 id="kpis-heading" className="sr-only">Summary Statistics</h2>
        <Dashboard
          stats={stats}
          isLoading={isStatsLoading}
          error={statsError}
          onRetry={loadStats}
          onFilterSelect={handleFilterSelect}
          activeFilter={{ risk_level: filters.risk_level, status: filters.status }}
        />
      </section>

      {/* 2. Main Transactions Table */}
      <section aria-labelledby="transactions-table-heading">
        <h2 id="transactions-table-heading" className="sr-only">Transactions Review Queue</h2>
        <TransactionTable
          data={transactionsData}
          isLoading={isTxLoading}
          error={txError}
          filters={filters}
          onFilterChange={handleFilterChange}
          onRefresh={() => loadTransactions(filters)}
          onSelectTransaction={handleSelectTransaction}
          onStatusChange={handleStatusChange}
        />
      </section>
    </div>
  );
};
