import React, { useState } from 'react';
import { ArrowLeft, User, MapPin, Calendar, DollarSign, Store, Loader2 } from 'lucide-react';
import { StatusBadge } from '../transactions/StatusBadge';
import { formatCurrency, formatTimestamp } from '../../utils/formatters';
import type { TransactionDetail } from '../../types/transaction';

interface InvestigationHeaderProps {
  transaction: TransactionDetail;
  onBack: () => void;
  onStatusChange?: (id: string, newStatus: string) => Promise<void>;
}

export const InvestigationHeader: React.FC<InvestigationHeaderProps> = ({
  transaction,
  onBack,
  onStatusChange,
}) => {
  const [isUpdating, setIsUpdating] = useState<boolean>(false);
  const [updateError, setUpdateError] = useState<string | null>(null);

  const handleStatusSelect = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newStatus = e.target.value;
    if (!newStatus || newStatus === transaction.review_status) return;

    setIsUpdating(true);
    setUpdateError(null);
    try {
      if (onStatusChange) {
        await onStatusChange(transaction.id, newStatus);
      }
    } catch (err: unknown) {
      setUpdateError(err instanceof Error ? err.message : 'Status update failed');
      e.target.value = String(transaction.review_status);
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Top Navigation Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <button
          onClick={onBack}
          type="button"
          className="inline-flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-white transition-colors group w-fit"
        >
          <ArrowLeft className="w-4 h-4 text-slate-400 group-hover:-translate-x-0.5 transition-transform" />
          <span>Back to Transactions</span>
        </button>

        {/* Quick Review Status Action */}
        <div className="flex items-center gap-2.5 bg-slate-900/80 border border-slate-800 px-3 py-1.5 rounded-lg w-fit">
          <span className="text-xs text-slate-400">Review Status:</span>
          {isUpdating ? (
            <div className="flex items-center gap-1.5 text-xs text-blue-400">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Updating...</span>
            </div>
          ) : (
            <select
              aria-label="Update review status"
              value={String(transaction.review_status)}
              onChange={handleStatusSelect}
              className="text-xs bg-slate-950 border border-slate-700 hover:border-slate-600 rounded px-2 py-1 text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
            >
              <option value="PENDING_REVIEW">Pending Review</option>
              <option value="REVIEWED">Reviewed</option>
              <option value="CLEARED">Cleared</option>
              <option value="ESCALATED">Escalated</option>
            </select>
          )}
        </div>
      </div>

      {updateError && (
        <div className="p-2.5 rounded-lg bg-rose-950/40 border border-rose-500/30 text-xs text-rose-300">
          {updateError}
        </div>
      )}

      {/* Main Header Banner */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 sm:p-6 backdrop-blur-md shadow-xl flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="font-mono text-xs font-semibold px-2.5 py-1 rounded-md bg-blue-500/10 text-blue-300 border border-blue-500/20">
              {transaction.transaction_reference || transaction.id}
            </span>
            <StatusBadge status={transaction.review_status || transaction.status} />
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Transaction Investigation
          </h1>

          <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-slate-400">
            <span className="flex items-center gap-1.5 text-slate-300">
              <User className="w-3.5 h-3.5 text-blue-400" />
              <strong className="font-mono text-white">{transaction.user_id}</strong>
            </span>
            <span className="flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-slate-500" />
              <span>{transaction.location || transaction.city || 'Unknown location'}</span>
            </span>
            {transaction.merchant_name && (
              <span className="flex items-center gap-1.5">
                <Store className="w-3.5 h-3.5 text-slate-500" />
                <span>{transaction.merchant_name}</span>
              </span>
            )}
            <span className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-slate-500" />
              <span className="font-mono">{formatTimestamp(transaction.timestamp)}</span>
            </span>
          </div>
        </div>

        {/* Amount Badge */}
        <div className="lg:text-right border-t lg:border-t-0 pt-4 lg:pt-0 border-slate-800">
          <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block">
            Transaction Amount
          </span>
          <div className="text-2xl sm:text-3xl font-mono font-extrabold text-white tracking-tight flex items-center lg:justify-end gap-1 mt-0.5">
            <DollarSign className="w-5 h-5 text-emerald-400 inline lg:hidden" />
            <span>{formatCurrency(transaction.amount, transaction.currency)}</span>
          </div>
          <span className="text-[11px] font-mono text-slate-400">
            Currency: <strong className="text-slate-300">{transaction.currency}</strong>
          </span>
        </div>
      </div>
    </div>
  );
};
