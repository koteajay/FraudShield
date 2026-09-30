import React from 'react';
import { History, UserCheck, ArrowRight, MessageSquare, Clock, RotateCw } from 'lucide-react';
import { formatTimestamp } from '../../utils/formatters';
import type { ReviewRecord } from '../../types/review';

interface ReviewHistoryProps {
  reviews: ReviewRecord[];
  isLoading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

export const ReviewHistory: React.FC<ReviewHistoryProps> = ({
  reviews = [],
  isLoading = false,
  error = null,
  onRetry,
}) => {
  if (isLoading) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-3 animate-pulse">
        <div className="h-5 w-40 bg-slate-800 rounded mb-4" />
        <div className="h-16 bg-slate-800/60 rounded-xl" />
        <div className="h-16 bg-slate-800/60 rounded-xl" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-300">Review History</h3>
          <p className="text-xs text-rose-300 mt-1">{error}</p>
        </div>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 transition-colors w-fit"
          >
            <RotateCw className="w-3.5 h-3.5" />
            <span>Retry History</span>
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 backdrop-blur-md shadow-xl space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <History className="w-5 h-5 text-blue-400" />
          <h3 className="text-base font-bold text-white tracking-tight">
            Review History &amp; Audit Trail
          </h3>
        </div>
        <span className="text-xs font-mono text-slate-400">
          {reviews.length} {reviews.length === 1 ? 'record' : 'records'}
        </span>
      </div>

      {reviews.length === 0 ? (
        <div className="p-6 text-center rounded-xl bg-slate-950/40 border border-slate-800/80">
          <History className="w-6 h-6 text-slate-600 mx-auto mb-2" />
          <p className="text-xs text-slate-400 font-medium">No review actions recorded yet.</p>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Initial review status changes will establish the forensic audit log.
          </p>
        </div>
      ) : (
        <div className="relative pl-6 space-y-5 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
          {reviews.map((rev) => (
            <div key={rev.id} className="relative group">
              {/* Timeline marker node */}
              <div className="absolute -left-[27px] top-1.5 w-3 h-3 rounded-full bg-blue-500 border-2 border-slate-900 shadow-sm" />

              <div className="rounded-xl border border-slate-800/90 bg-slate-950/60 p-4 space-y-2.5 hover:border-slate-700 transition-colors">
                {/* Meta row: Reviewer + Timestamp */}
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                  <span className="flex items-center gap-1.5 font-semibold text-slate-200">
                    <UserCheck className="w-3.5 h-3.5 text-blue-400" />
                    <span className="font-mono text-blue-300">{rev.reviewer_id}</span>
                  </span>
                  <span className="flex items-center gap-1 text-[11px] text-slate-400 font-mono">
                    <Clock className="w-3 h-3 text-slate-500" />
                    <span>{formatTimestamp(rev.created_at)}</span>
                  </span>
                </div>

                {/* Status Transition Badges */}
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                    {rev.previous_status}
                  </span>
                  <ArrowRight className="w-3 h-3 text-slate-500" />
                  <span
                    className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold border ${
                      rev.new_status === 'CLEARED'
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                        : rev.new_status === 'REVIEWED'
                        ? 'bg-blue-500/20 text-blue-300 border-blue-500/40'
                        : 'bg-slate-800 text-slate-200 border-slate-700'
                    }`}
                  >
                    {rev.new_status}
                  </span>
                </div>

                {/* Reviewer Note */}
                {rev.note && (
                  <div className="pt-1 flex items-start gap-2 text-xs text-slate-300 leading-relaxed bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/60 font-mono">
                    <MessageSquare className="w-3.5 h-3.5 text-slate-500 shrink-0 mt-0.5" />
                    <span className="break-words">“{rev.note}”</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
