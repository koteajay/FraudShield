import React from 'react';
import { Link } from 'react-router-dom';
import type { Transaction } from '../../types/transaction';
import { RiskBadge } from '../risk/RiskBadge';
import { RiskScore } from '../risk/RiskScore';
import { StatusBadge } from '../risk/StatusBadge';
import { ExternalLink, User, MapPin } from 'lucide-react';

export interface TransactionTableProps {
  transactions: Transaction[];
  isLoading?: boolean;
}

/**
 * Format currency amount dynamically based on the transaction currency code.
 */
function formatCurrency(amount: number, currencyCode: string = 'USD'): string {
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: currencyCode.toUpperCase(),
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    // Fallback if currencyCode is not a valid ISO code
    return `${currencyCode.toUpperCase()} ${amount.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  }
}

/**
 * Formats ISO timestamp to human-friendly reviewer format: "Sep 30, 2026, 10:42 AM"
 */
function formatTimestamp(timestamp: string): { formatted: string; relative: string } {
  try {
    const date = new Date(timestamp);
    if (isNaN(date.getTime())) {
      return { formatted: timestamp, relative: '' };
    }

    const formatted = new Intl.DateTimeFormat(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: 'numeric',
      hour12: true,
    }).format(date);

    return { formatted, relative: date.toISOString() };
  } catch {
    return { formatted: timestamp, relative: '' };
  }
}

export const TransactionTable: React.FC<TransactionTableProps> = ({
  transactions,
  isLoading = false,
}) => {
  if (isLoading) {
    return (
      <div className="w-full bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-xl animate-pulse">
        <div className="p-4 border-b border-slate-800 bg-slate-900/80">
          <div className="h-5 w-48 bg-slate-800 rounded" />
        </div>
        <div className="divide-y divide-slate-800/60 p-6 space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-12 bg-slate-800/40 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="w-full bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl backdrop-blur-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse min-w-[900px]">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-950/70 text-[11px] font-mono font-semibold uppercase tracking-wider text-slate-400 select-none">
              <th scope="col" className="py-3.5 px-4">Transaction ID</th>
              <th scope="col" className="py-3.5 px-4">User</th>
              <th scope="col" className="py-3.5 px-4">Amount</th>
              <th scope="col" className="py-3.5 px-4">Location</th>
              <th scope="col" className="py-3.5 px-4">Risk Score</th>
              <th scope="col" className="py-3.5 px-4">Risk Level</th>
              <th scope="col" className="py-3.5 px-4">Status</th>
              <th scope="col" className="py-3.5 px-4">Timestamp</th>
              <th scope="col" className="py-3.5 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-sm">
            {transactions.map((txn) => {
              const { formatted, relative } = formatTimestamp(txn.timestamp);

              return (
                <tr
                  key={txn.id}
                  className="hover:bg-slate-800/40 transition-colors duration-150 group"
                >
                  {/* Transaction ID */}
                  <td className="py-3.5 px-4 font-mono font-medium text-slate-200">
                    <Link
                      to={`/transactions/${txn.id}`}
                      className="hover:text-blue-400 hover:underline transition-colors inline-flex items-center gap-1.5"
                    >
                      <span>{txn.id}</span>
                    </Link>
                  </td>

                  {/* User */}
                  <td className="py-3.5 px-4 text-slate-300">
                    <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-slate-950/50 border border-slate-800/80 font-mono text-xs text-indigo-300">
                      <User className="w-3 h-3 text-indigo-400" />
                      <span>{txn.userId}</span>
                    </div>
                  </td>

                  {/* Amount */}
                  <td className="py-3.5 px-4 font-mono font-semibold text-white">
                    {formatCurrency(txn.amount, txn.currency)}
                  </td>

                  {/* Location */}
                  <td className="py-3.5 px-4 text-slate-400 text-xs">
                    {txn.location ? (
                      <div className="flex items-center gap-1">
                        <MapPin className="w-3 h-3 text-slate-500 shrink-0" />
                        <span className="truncate max-w-[130px]">{txn.location}</span>
                      </div>
                    ) : (
                      <span className="text-slate-600 italic">Unknown</span>
                    )}
                  </td>

                  {/* Risk Score */}
                  <td className="py-3.5 px-4">
                    <RiskScore
                      score={txn.riskScore}
                      riskLevel={txn.riskLevel}
                      size="sm"
                      showBar={true}
                    />
                  </td>

                  {/* Risk Level */}
                  <td className="py-3.5 px-4">
                    <RiskBadge level={txn.riskLevel} size="sm" />
                  </td>

                  {/* Status */}
                  <td className="py-3.5 px-4">
                    <StatusBadge status={txn.status} size="sm" />
                  </td>

                  {/* Timestamp */}
                  <td className="py-3.5 px-4 text-xs text-slate-400 whitespace-nowrap" title={relative}>
                    {formatted}
                  </td>

                  {/* Action */}
                  <td className="py-3.5 px-4 text-right">
                    <Link
                      to={`/transactions/${txn.id}`}
                      className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg bg-blue-600/15 text-blue-400 hover:bg-blue-600 hover:text-white border border-blue-500/20 hover:border-blue-500 transition-all duration-150 cursor-pointer shadow-sm"
                      aria-label={`Investigate transaction ${txn.id}`}
                    >
                      <span>Investigate</span>
                      <ExternalLink className="w-3 h-3" />
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TransactionTable;
