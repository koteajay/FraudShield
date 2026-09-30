import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { getDashboardStats } from '../services/api/dashboard';
import { getTransactions } from '../services/api/transactions';
import type { DashboardStats } from '../types/dashboard';
import type { Transaction } from '../types/transaction';
import { DashboardStatsGrid } from '../components/dashboard/DashboardStatsGrid';
import { TransactionTable } from '../components/transactions/TransactionTable';
import {
  TransactionFilters,
  type FilterState,
} from '../components/transactions/TransactionFilters';
import { ErrorState } from '../components/common/ErrorState';
import { EmptyState } from '../components/common/EmptyState';
import { SAMPLE_DASHBOARD_STATS, SAMPLE_TRANSACTIONS } from '../utils/sampleData';
import {
  LayoutDashboard,
  RefreshCw,
  AlertCircle,
  Eye,
  SlidersHorizontal,
} from 'lucide-react';

const INITIAL_FILTERS: FilterState = {
  search: '',
  riskLevel: 'ALL',
  status: 'ALL',
};

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterState>(INITIAL_FILTERS);
  const [isInspectionMode, setIsInspectionMode] = useState<boolean>(false);

  const fetchDashboardData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Execute live API service calls concurrently
      const [statsResult, transactionsResult] = await Promise.all([
        getDashboardStats(),
        getTransactions(),
      ]);

      setStats(statsResult);
      setTransactions(transactionsResult);
      setIsInspectionMode(false);
    } catch (err: unknown) {
      if (
        err &&
        typeof err === 'object' &&
        'message' in err &&
        typeof (err as { message: unknown }).message === 'string'
      ) {
        setError((err as { message: string }).message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Unable to load dashboard data from backend service.');
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Activate development inspection sample when backend endpoint is not yet connected
  const enableInspectionPreview = () => {
    setStats(SAMPLE_DASHBOARD_STATS);
    setTransactions(SAMPLE_TRANSACTIONS);
    setIsInspectionMode(true);
    setError(null);
  };

  // Client-side filtering logic
  const filteredTransactions = useMemo(() => {
    return transactions.filter((txn) => {
      // 1. Search filter (Transaction ID, User ID, Location)
      if (filters.search) {
        const query = filters.search.toLowerCase().trim();
        const matchesId = txn.id.toLowerCase().includes(query);
        const matchesUser = txn.userId.toLowerCase().includes(query);
        const matchesLocation = txn.location
          ? txn.location.toLowerCase().includes(query)
          : false;
        const matchesMerchant = txn.merchant
          ? txn.merchant.toLowerCase().includes(query)
          : false;

        if (!matchesId && !matchesUser && !matchesLocation && !matchesMerchant) {
          return false;
        }
      }

      // 2. Risk Level filter
      if (filters.riskLevel !== 'ALL' && txn.riskLevel !== filters.riskLevel) {
        return false;
      }

      // 3. Status filter
      if (filters.status !== 'ALL' && txn.status !== filters.status) {
        return false;
      }

      return true;
    });
  }, [transactions, filters]);

  const handleClearFilters = () => {
    setFilters(INITIAL_FILTERS);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      {/* Inspection Mode Alert Banner */}
      {isInspectionMode && (
        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-lg shadow-amber-950/20">
          <div className="flex items-center gap-2.5">
            <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
            <div>
              <span className="font-semibold text-white">
                Development Inspection Preview Active:
              </span>{' '}
              Displaying sample reviewer dataset because live backend endpoint is offline or returned 404. Real API service layer remains active.
            </div>
          </div>
          <button
            type="button"
            onClick={fetchDashboardData}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 border border-amber-500/40 font-medium transition cursor-pointer self-start sm:self-auto shrink-0"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Switch to Live API</span>
          </button>
        </div>
      )}

      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <LayoutDashboard className="w-5 h-5" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Reviewer Dashboard
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1 font-medium">
            Monitor transaction risk scores, analyze rule flags, and prioritize high-risk investigations.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={fetchDashboardData}
            disabled={isLoading}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition disabled:opacity-50 cursor-pointer shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh Feed</span>
          </button>
        </div>
      </div>

      {/* Statistics Cards Grid */}
      <section aria-labelledby="stats-heading">
        <h2 id="stats-heading" className="sr-only">
          Dashboard Summary Statistics
        </h2>
        <DashboardStatsGrid
          stats={
            stats || {
              totalTransactions: 0,
              flaggedTransactions: 0,
              highRisk: 0,
              critical: 0,
              pendingReview: 0,
              cleared: 0,
            }
          }
          isLoading={isLoading && !stats}
        />
      </section>

      {/* Filters and Transactions Feed */}
      <section className="space-y-4" aria-labelledby="transactions-heading">
        <div className="flex items-center justify-between">
          <h2
            id="transactions-heading"
            className="text-base font-semibold text-white flex items-center gap-2"
          >
            <span>Live Transaction Stream</span>
            <span className="text-xs font-mono font-normal text-slate-500">
              ({filteredTransactions.length} items)
            </span>
          </h2>
        </div>

        {/* Filter Bar */}
        <TransactionFilters
          filters={filters}
          onChange={setFilters}
          onClear={handleClearFilters}
          totalCount={transactions.length}
          filteredCount={filteredTransactions.length}
        />

        {/* Loading State */}
        {isLoading && transactions.length === 0 && (
          <TransactionTable transactions={[]} isLoading={true} />
        )}

        {/* Error State with option to preview inspection data */}
        {!isLoading && error && transactions.length === 0 && (
          <div className="space-y-4">
            <ErrorState
              title="Unable to load dashboard transactions"
              message={error}
              onRetry={fetchDashboardData}
              retryLabel="Retry API Request"
            />
            <div className="text-center">
              <button
                type="button"
                onClick={enableInspectionPreview}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition shadow-md cursor-pointer"
              >
                <Eye className="w-4 h-4 text-blue-400" />
                <span>Preview Sample Inspection Dataset (Demo Mode)</span>
              </button>
            </div>
          </div>
        )}

        {/* Empty States */}
        {!isLoading && !error && transactions.length === 0 && (
          <EmptyState
            title="No transactions found"
            message="No transactions have been ingested or recorded in the system yet."
            actionLabel="Refresh Transactions"
            onAction={fetchDashboardData}
          />
        )}

        {/* Filtered Empty State */}
        {!isLoading && transactions.length > 0 && filteredTransactions.length === 0 && (
          <EmptyState
            icon={<SlidersHorizontal className="w-6 h-6 text-slate-400" />}
            title="No matching transactions"
            message="No transactions match the selected risk level, status, or search query."
            actionLabel="Clear All Filters"
            onAction={handleClearFilters}
          />
        )}

        {/* Active Transaction Table */}
        {!isLoading && filteredTransactions.length > 0 && (
          <TransactionTable
            transactions={filteredTransactions}
            isLoading={false}
          />
        )}
      </section>
    </div>
  );
};

export default DashboardPage;
