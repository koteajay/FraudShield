import React from 'react';
import type { RiskLevel, TransactionStatus } from '../../types/transaction';
import { Search, X, Filter } from 'lucide-react';

export interface FilterState {
  search: string;
  riskLevel: RiskLevel | 'ALL';
  status: TransactionStatus | 'ALL';
}

export interface TransactionFiltersProps {
  filters: FilterState;
  onChange: (updated: FilterState) => void;
  onClear: () => void;
  totalCount: number;
  filteredCount: number;
}

export const TransactionFilters: React.FC<TransactionFiltersProps> = ({
  filters,
  onChange,
  onClear,
  totalCount,
  filteredCount,
}) => {
  const isFiltered =
    filters.search !== '' ||
    filters.riskLevel !== 'ALL' ||
    filters.status !== 'ALL';

  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 bg-slate-900/60 border border-slate-800 rounded-2xl">
      <div className="flex flex-wrap items-center gap-3 flex-1">
        {/* Search Input */}
        <div className="relative min-w-[220px] flex-1 max-w-sm">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search transaction or user ID..."
            value={filters.search}
            onChange={(e) => onChange({ ...filters, search: e.target.value })}
            className="w-full bg-slate-950/80 border border-slate-800 rounded-xl pl-9 pr-8 py-2 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-blue-500/80 focus:ring-1 focus:ring-blue-500/50"
            aria-label="Search transactions"
          />
          {filters.search && (
            <button
              type="button"
              onClick={() => onChange({ ...filters, search: '' })}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 cursor-pointer"
              aria-label="Clear search"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Risk Level Filter */}
        <div className="flex items-center gap-1.5">
          <Filter className="w-3.5 h-3.5 text-slate-500" />
          <select
            value={filters.riskLevel}
            onChange={(e) =>
              onChange({
                ...filters,
                riskLevel: e.target.value as RiskLevel | 'ALL',
              })
            }
            className="bg-slate-950/80 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500/80 cursor-pointer"
            aria-label="Filter by Risk Level"
          >
            <option value="ALL">All Risk Levels</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>
        </div>

        {/* Status Filter */}
        <select
          value={filters.status}
          onChange={(e) =>
            onChange({
              ...filters,
              status: e.target.value as TransactionStatus | 'ALL',
            })
          }
          className="bg-slate-950/80 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500/80 cursor-pointer"
          aria-label="Filter by Status"
        >
          <option value="ALL">All Statuses</option>
          <option value="PENDING">PENDING</option>
          <option value="REVIEWED">REVIEWED</option>
          <option value="CLEARED">CLEARED</option>
        </select>

        {/* Clear Filters Action */}
        {isFiltered && (
          <button
            type="button"
            onClick={onClear}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 rounded-xl transition-colors cursor-pointer"
          >
            <X className="w-3.5 h-3.5" />
            <span>Clear Filters</span>
          </button>
        )}
      </div>

      {/* Counter indicator */}
      <div className="text-xs text-slate-500 font-mono self-end md:self-center">
        Showing <span className="text-slate-200 font-semibold">{filteredCount}</span> of{' '}
        <span>{totalCount}</span>
      </div>
    </div>
  );
};

export default TransactionFilters;
