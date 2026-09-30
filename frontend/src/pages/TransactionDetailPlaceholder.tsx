import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, AlertTriangle, User, DollarSign } from 'lucide-react';
import { getTransaction, updateTransactionStatus } from '../services/transactionService';
import { RiskBadge } from '../components/transactions/RiskBadge';
import { StatusBadge } from '../components/transactions/StatusBadge';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { formatCurrency, formatTimestamp } from '../utils/formatters';
import type { TransactionDetail } from '../types/transaction';

export const TransactionDetailPlaceholder: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [transaction, setTransaction] = useState<TransactionDetail | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isUpdating, setIsUpdating] = useState<boolean>(false);

  const loadTx = useCallback(async () => {
    if (!id) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await getTransaction(id);
      setTransaction(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load transaction');
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadTx();
  }, [loadTx]);

  const handleStatusChange = async (newStatus: string) => {
    if (!id) return;
    setIsUpdating(true);
    try {
      await updateTransactionStatus(id, newStatus);
      await loadTx();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Status update failed');
    } finally {
      setIsUpdating(false);
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-16">
        <LoadingState message="Loading transaction forensic details..." />
      </div>
    );
  }

  if (error || !transaction) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-16 space-y-4">
        <button
          onClick={() => navigate('/dashboard')}
          type="button"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Reviewer Console</span>
        </button>
        <ErrorState
          title="Transaction Not Found"
          message={error || 'Unable to retrieve transaction details.'}
          onRetry={loadTx}
        />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      {/* Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/dashboard')}
          type="button"
          className="inline-flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Reviewer Console</span>
        </button>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Review Status:</span>
          <select
            disabled={isUpdating}
            value={String(transaction.review_status)}
            onChange={(e) => handleStatusChange(e.target.value)}
            className="text-xs bg-slate-900 border border-slate-700 hover:border-slate-600 rounded-lg px-2.5 py-1 text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer disabled:opacity-50"
          >
            <option value="PENDING_REVIEW">Pending Review</option>
            <option value="REVIEWED">Reviewed</option>
            <option value="CLEARED">Cleared</option>
            <option value="ESCALATED">Escalated</option>
          </select>
        </div>
      </div>

      {/* Main Forensic Header */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                {transaction.transaction_reference || transaction.id}
              </span>
              <StatusBadge status={transaction.review_status || transaction.status} />
            </div>
            <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
              Transaction Details &amp; Risk Assessment
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Detailed transaction record shell ready for Phase 11 deep investigation.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-xs text-slate-400 uppercase font-medium">Risk Score</div>
              <div className="text-2xl font-mono font-bold text-white">
                {transaction.risk_score.toFixed(0)}
                <span className="text-xs text-slate-500">/100</span>
              </div>
            </div>
            <RiskBadge level={transaction.risk_level} score={transaction.risk_score} />
          </div>
        </div>

        {/* 2-Column Overview Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="space-y-3 bg-slate-950/60 p-4 rounded-lg border border-slate-800/80">
            <h3 className="font-semibold text-slate-300 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
              <DollarSign className="w-3.5 h-3.5 text-blue-400" />
              <span>Financial Telemetry</span>
            </h3>
            <div className="space-y-2 text-slate-300">
              <div className="flex justify-between py-1 border-b border-slate-800/50">
                <span className="text-slate-400">Amount:</span>
                <span className="font-mono font-bold text-white">
                  {formatCurrency(transaction.amount, transaction.currency)}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/50">
                <span className="text-slate-400">Merchant:</span>
                <span className="font-medium text-slate-200">{transaction.merchant_name || '—'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/50">
                <span className="text-slate-400">Category:</span>
                <span className="font-mono text-slate-300">{transaction.merchant_category || '—'}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Timestamp:</span>
                <span className="font-mono text-slate-300">{formatTimestamp(transaction.timestamp)}</span>
              </div>
            </div>
          </div>

          <div className="space-y-3 bg-slate-950/60 p-4 rounded-lg border border-slate-800/80">
            <h3 className="font-semibold text-slate-300 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-blue-400" />
              <span>Identity &amp; Context</span>
            </h3>
            <div className="space-y-2 text-slate-300">
              <div className="flex justify-between py-1 border-b border-slate-800/50">
                <span className="text-slate-400">User ID:</span>
                <span className="font-mono text-slate-200">{transaction.user_id}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/50">
                <span className="text-slate-400">Location:</span>
                <span className="text-slate-200">{transaction.location || transaction.city || '—'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/50">
                <span className="text-slate-400">Device ID:</span>
                <span className="font-mono text-slate-300">{transaction.device?.device_id || '—'}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Device Status:</span>
                <span className={`font-medium ${transaction.device?.is_new ? 'text-amber-400' : 'text-emerald-400'}`}>
                  {transaction.device?.is_new ? 'New / Unrecognized' : 'Known Device'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Triggered Rules Breakdown */}
        {transaction.rule_results && transaction.rule_results.length > 0 && (
          <div className="space-y-3 pt-2">
            <h3 className="font-semibold text-slate-300 text-xs uppercase tracking-wider flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              <span>Fraud Rule Heuristics Evaluated</span>
            </h3>
            <div className="divide-y divide-slate-800/80 border border-slate-800 rounded-lg overflow-hidden bg-slate-950/40">
              {transaction.rule_results.map((rule) => (
                <div key={rule.rule_id} className="p-3.5 flex items-start justify-between gap-4 text-xs">
                  <div>
                    <div className="flex items-center gap-2 font-medium text-slate-200">
                      <span>{rule.rule_name}</span>
                      <span className="text-[10px] font-mono text-slate-500">{rule.rule_id}</span>
                    </div>
                    {rule.details?.reason && (
                      <p className="mt-1 text-slate-400 text-xs leading-relaxed">{rule.details.reason}</p>
                    )}
                  </div>
                  <div className="text-right whitespace-nowrap">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-[11px] font-medium font-mono ${
                        rule.is_triggered
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          : 'bg-slate-800 text-slate-400 border border-slate-700'
                      }`}
                    >
                      {rule.is_triggered ? 'TRIGGERED' : 'PASS'}
                    </span>
                    {rule.is_triggered && rule.details?.score_contribution != null && (
                      <div className="text-[11px] text-amber-400 font-mono mt-1">
                        +{rule.details.score_contribution} pts
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
