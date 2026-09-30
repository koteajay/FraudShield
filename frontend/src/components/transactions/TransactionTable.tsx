import React from 'react';
import {
  Filter,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  Search,
} from 'lucide-react';
import { TransactionRow } from './TransactionRow';
import { TransactionTableSkeleton } from './TransactionTableSkeleton';
import { EmptyState } from '../common/EmptyState';
import { ErrorState } from '../common/ErrorState';
import type {
  Transaction,
  TransactionFilterParams,
  PaginatedTransactionsResponse,
} from '../../types/transaction';

interface TransactionTableProps {
  data: PaginatedTransactionsResponse | null;
  isLoading: boolean;
  error: string | null;
  filters: TransactionFilterParams;
  onFilterChange: (newFilters: Partial<TransactionFilterParams>) => void;
  onRefresh: () => void;
  onSelectTransaction: (transaction: Transaction) => void;
  onStatusChange?: (id: string, newStatus: string) => Promise<void>;
}

export const TransactionTable: React.FC<TransactionTableProps> = ({
  data,
  isLoading,
  error,
  filters,
  onFilterChange,
  onRefresh,
  onSelectTransaction,
  onStatusChange,
}) => {
  const currentPage = data?.page || filters.page || 1;
  const totalPages = data?.total_pages || 1;
  const totalItems = data?.total || 0;
  const pageSize = data?.page_size || filters.page_size || 20;

  const startItem = totalItems === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  const handlePrevPage = () => {
    if (currentPage > 1) {
      onFilterChange({ page: currentPage - 1 });
    }
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      onFilterChange({ page: currentPage + 1 });
    }
  };

  const handleRiskFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    onFilterChange({ risk_level: val === 'ALL' ? undefined : val, page: 1 });
  };

  const handleStatusFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    onFilterChange({ status: val === 'ALL' ? undefined : val, page: 1 });
  };

  const handleSearchSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const userSearch = formData.get('user_id')?.toString().trim();
    onFilterChange({ user_id: userSearch || undefined, page: 1 });
  };

  const hasActiveFilters = Boolean(
    filters.risk_level || filters.status || filters.user_id
  );

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 shadow-xl backdrop-blur-sm overflow-hidden flex flex-col">
      {/* 1. Header Toolbar */}
      <div className="p-4 sm:p-5 border-b border-slate-800/80 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
            <span>Transactions</span>
            <span className="text-xs px-2 py-0.5 rounded-full font-mono bg-slate-800 text-slate-300 border border-slate-700">
              {totalItems.toLocaleString()} total
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Operational review queue sorted newest first. Click any row for transaction investigation.
          </p>
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* User ID Search Form */}
          <form onSubmit={handleSearchSubmit} className="relative">
            <input
              type="text"
              name="user_id"
              defaultValue={filters.user_id || ''}
              placeholder="Search User ID..."
              aria-label="Search by User ID"
              className="text-xs bg-slate-950 border border-slate-800 focus:border-blue-500 rounded-lg pl-8 pr-3 py-1.5 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500 w-36 sm:w-44"
            />
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" aria-hidden="true" />
          </form>

          {/* Risk Level Filter */}
          <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1">
            <Filter className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
            <select
              aria-label="Filter by Risk Level"
              value={filters.risk_level || 'ALL'}
              onChange={handleRiskFilterChange}
              className="text-xs bg-transparent text-slate-300 focus:outline-none cursor-pointer"
            >
              <option value="ALL">All Risk Levels</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1">
            <select
              aria-label="Filter by Status"
              value={filters.status || 'ALL'}
              onChange={handleStatusFilterChange}
              className="text-xs bg-transparent text-slate-300 focus:outline-none cursor-pointer"
            >
              <option value="ALL">All Statuses</option>
              <option value="PENDING_REVIEW">Pending Review</option>
              <option value="FLAGGED">Flagged</option>
              <option value="REVIEWED">Reviewed</option>
              <option value="CLEARED">Cleared</option>
              <option value="ESCALATED">Escalated</option>
            </select>
          </div>

          {/* Reset Filters */}
          {hasActiveFilters && (
            <button
              onClick={() => onFilterChange({ risk_level: undefined, status: undefined, user_id: undefined, page: 1 })}
              type="button"
              className="text-xs text-blue-400 hover:text-blue-300 underline px-1 py-1"
            >
              Reset
            </button>
          )}

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            disabled={isLoading}
            type="button"
            aria-label="Refresh transaction data"
            title="Refresh transactions"
            className="p-1.5 rounded-lg border border-slate-800 bg-slate-950 hover:bg-slate-800 text-slate-300 hover:text-white transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-blue-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* 2. Table or State Display */}
      {error && !data ? (
        <div className="p-8">
          <ErrorState
            title="Unable to load transactions"
            message={error}
            onRetry={onRefresh}
          />
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse" aria-label="Transactions Review Table">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                <th scope="col" className="px-5 py-3">Transaction ID</th>
                <th scope="col" className="px-5 py-3">User</th>
                <th scope="col" className="px-5 py-3 text-right">Amount</th>
                <th scope="col" className="px-5 py-3">Location</th>
                <th scope="col" className="px-5 py-3 text-right">
                  <span className="inline-flex items-center gap-1 justify-end">
                    <span>Score</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-500" aria-hidden="true" />
                  </span>
                </th>
                <th scope="col" className="px-5 py-3">Risk Level</th>
                <th scope="col" className="px-5 py-3">Status</th>
                <th scope="col" className="px-5 py-3">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {isLoading && !data ? (
                <tr>
                  <td colSpan={8} className="p-0">
                    <TransactionTableSkeleton rows={pageSize > 10 ? 10 : pageSize} />
                  </td>
                </tr>
              ) : data && data.items.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12">
                    <EmptyState
                      title={hasActiveFilters ? 'No transactions match filters' : 'No transactions found'}
                      message={
                        hasActiveFilters
                          ? 'Try adjusting or clearing your search and filter parameters.'
                          : 'Transactions ingested through the API will appear here.'
                      }
                      actionLabel={hasActiveFilters ? 'Clear Filters' : undefined}
                      onAction={
                        hasActiveFilters
                          ? () => onFilterChange({ risk_level: undefined, status: undefined, user_id: undefined, page: 1 })
                          : undefined
                      }
                    />
                  </td>
                </tr>
              ) : (
                data?.items.map((tx) => (
                  <TransactionRow
                    key={tx.id}
                    transaction={tx}
                    onSelect={onSelectTransaction}
                    onStatusChange={onStatusChange}
                  />
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* 3. Pagination Footer */}
      {data && data.items.length > 0 && (
        <div className="px-5 py-3.5 border-t border-slate-800 bg-slate-950/40 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400">
          <div>
            Showing <span className="font-medium text-slate-200">{startItem}</span> to{' '}
            <span className="font-medium text-slate-200">{endItem}</span> of{' '}
            <span className="font-medium text-slate-200">{totalItems.toLocaleString()}</span> entries
          </div>

          <div className="flex items-center gap-1.5">
            {/* Previous Button */}
            <button
              onClick={handlePrevPage}
              disabled={currentPage <= 1 || isLoading}
              type="button"
              className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 disabled:hover:bg-slate-900 text-slate-300 disabled:cursor-not-allowed transition-colors"
              aria-label="Previous page"
            >
              <ChevronLeft className="w-3.5 h-3.5" aria-hidden="true" />
              <span>Previous</span>
            </button>

            {/* Page Indicator */}
            <div className="px-3 py-1 font-mono text-slate-300 bg-slate-950 border border-slate-800/80 rounded-lg">
              Page <span className="font-bold text-white">{currentPage}</span> of{' '}
              <span>{totalPages}</span>
            </div>

            {/* Next Button */}
            <button
              onClick={handleNextPage}
              disabled={currentPage >= totalPages || isLoading}
              type="button"
              className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 disabled:hover:bg-slate-900 text-slate-300 disabled:cursor-not-allowed transition-colors"
              aria-label="Next page"
            >
              <span>Next</span>
              <ChevronRight className="w-3.5 h-3.5" aria-hidden="true" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
