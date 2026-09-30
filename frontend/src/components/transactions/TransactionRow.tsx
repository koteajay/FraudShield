import React, { useState } from 'react';
import { ChevronRight, Loader2 } from 'lucide-react';
import { RiskBadge } from './RiskBadge';
import { StatusBadge } from './StatusBadge';
import { formatCurrency, formatTimestamp } from '../../utils/formatters';
import type { Transaction } from '../../types/transaction';

interface TransactionRowProps {
  transaction: Transaction;
  onSelect: (transaction: Transaction) => void;
  onStatusChange?: (id: string, newStatus: string) => Promise<void>;
}

export const TransactionRow: React.FC<TransactionRowProps> = ({
  transaction,
  onSelect,
  onStatusChange,
}) => {
  const [isUpdating, setIsUpdating] = useState<boolean>(false);
  const [updateError, setUpdateError] = useState<string | null>(null);

  const handleStatusSelect = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    e.stopPropagation();
    const newStatus = e.target.value;
    if (!newStatus || newStatus === transaction.review_status) return;

    setIsUpdating(true);
    setUpdateError(null);
    try {
      if (onStatusChange) {
        await onStatusChange(transaction.id, newStatus);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Status update failed';
      setUpdateError(msg);
      // Reset select input back to original status
      e.target.value = String(transaction.review_status);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleRowClick = () => {
    onSelect(transaction);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onSelect(transaction);
    }
  };

  return (
    <tr
      tabIndex={0}
      role="row"
      onClick={handleRowClick}
      onKeyDown={handleKeyDown}
      className="group hover:bg-slate-800/40 transition-colors cursor-pointer border-b border-slate-800/80 focus:outline-none focus:bg-slate-800/60"
    >
      {/* 1. Transaction ID */}
      <td className="px-5 py-3.5 whitespace-nowrap">
        <div className="flex items-center gap-1.5 font-mono text-xs text-blue-400 group-hover:text-blue-300 font-medium">
          <span className="truncate max-w-[130px]" title={transaction.transaction_reference || transaction.id}>
            {transaction.transaction_reference || transaction.id.slice(0, 12)}
          </span>
          <ChevronRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity text-slate-500" />
        </div>
      </td>

      {/* 2. User */}
      <td className="px-5 py-3.5 whitespace-nowrap">
        <div className="text-xs font-medium text-slate-300 truncate max-w-[110px]" title={transaction.user_id}>
          {transaction.user_id}
        </div>
      </td>

      {/* 3. Amount */}
      <td className="px-5 py-3.5 whitespace-nowrap text-right">
        <span className="text-xs font-semibold font-mono text-white">
          {formatCurrency(transaction.amount, transaction.currency)}
        </span>
      </td>

      {/* 4. Location */}
      <td className="px-5 py-3.5 whitespace-nowrap">
        <span
          className="text-xs text-slate-400 truncate max-w-[130px] block"
          title={transaction.location || transaction.city || 'Unknown'}
        >
          {transaction.location || transaction.city || '—'}
        </span>
      </td>

      {/* 5. Risk Score */}
      <td className="px-5 py-3.5 whitespace-nowrap text-right">
        <span
          className={`font-mono text-xs font-bold ${
            transaction.risk_score >= 80
              ? 'text-rose-400'
              : transaction.risk_score >= 60
              ? 'text-orange-400'
              : transaction.risk_score >= 30
              ? 'text-amber-400'
              : 'text-emerald-400'
          }`}
        >
          {transaction.risk_score.toFixed(0)}
        </span>
      </td>

      {/* 6. Risk Level */}
      <td className="px-5 py-3.5 whitespace-nowrap">
        <RiskBadge level={transaction.risk_level} />
      </td>

      {/* 7. Status & Quick Action */}
      <td className="px-5 py-3.5 whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-2">
          <StatusBadge status={transaction.review_status || transaction.status} />

          {onStatusChange && (
            <div className="relative inline-block text-left">
              {isUpdating ? (
                <Loader2 className="w-3.5 h-3.5 text-blue-400 animate-spin" aria-label="Updating status" />
              ) : (
                <select
                  aria-label={`Change status for transaction ${transaction.id}`}
                  defaultValue={String(transaction.review_status)}
                  onChange={handleStatusSelect}
                  className="text-[11px] bg-slate-900 border border-slate-700 hover:border-slate-600 rounded px-1.5 py-0.5 text-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
                >
                  <option value="PENDING_REVIEW">Pending Review</option>
                  <option value="REVIEWED">Reviewed</option>
                  <option value="CLEARED">Cleared</option>
                  <option value="ESCALATED">Escalated</option>
                </select>
              )}
              {updateError && (
                <span className="text-[10px] text-rose-400 block max-w-[120px] truncate" title={updateError}>
                  {updateError}
                </span>
              )}
            </div>
          )}
        </div>
      </td>

      {/* 8. Time */}
      <td className="px-5 py-3.5 whitespace-nowrap text-xs text-slate-400 font-mono">
        {formatTimestamp(transaction.timestamp)}
      </td>
    </tr>
  );
};
