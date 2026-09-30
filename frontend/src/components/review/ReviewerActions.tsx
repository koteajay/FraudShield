import React, { useState } from 'react';
import { ShieldCheck, Check, AlertTriangle, CheckCircle2, Lock, Loader2 } from 'lucide-react';
import { StatusBadge } from '../transactions/StatusBadge';
import { ReviewNoteInput } from './ReviewNoteInput';
import { ClearConfirmationModal } from './ClearConfirmationModal';
import { updateTransactionStatus } from '../../services/reviewService';
import type { ReviewStatus, ReviewStatusUpdateResponse } from '../../types/review';

interface ReviewerActionsProps {
  transactionId: string;
  currentStatus: ReviewStatus;
  onStatusUpdated: (response: ReviewStatusUpdateResponse) => void;
  onRefreshNeeded?: () => void;
}

export const ReviewerActions: React.FC<ReviewerActionsProps> = ({
  transactionId,
  currentStatus,
  onStatusUpdated,
  onRefreshNeeded,
}) => {
  const [note, setNote] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [feedbackSuccess, setFeedbackSuccess] = useState<string | null>(null);
  const [feedbackError, setFeedbackError] = useState<string | null>(null);
  const [isClearModalOpen, setIsClearModalOpen] = useState<boolean>(false);

  const normalizedStatus = String(currentStatus).toUpperCase();
  const isCleared = normalizedStatus === 'CLEARED';
  const isReviewed = normalizedStatus === 'REVIEWED';

  const executeStatusChange = async (targetStatus: string) => {
    setIsSubmitting(true);
    setFeedbackError(null);
    setFeedbackSuccess(null);

    try {
      const response = await updateTransactionStatus(transactionId, targetStatus, note);
      setNote(''); // Clear note after success
      setFeedbackSuccess(
        targetStatus === 'CLEARED'
          ? 'Transaction marked as Cleared.'
          : 'Transaction marked as Reviewed.'
      );
      onStatusUpdated(response);
    } catch (err: unknown) {
      const rawMsg = err instanceof Error ? err.message : '';
      if (rawMsg.includes('400') || rawMsg.includes('Invalid review status transition') || rawMsg.includes('already')) {
        setFeedbackError(
          'Unable to update transaction status. The transaction status may have changed since this page was opened. Please refresh and try again.'
        );
        if (onRefreshNeeded) onRefreshNeeded();
      } else {
        setFeedbackError(rawMsg || 'Unable to update transaction status.');
      }
    } finally {
      setIsSubmitting(false);
      setIsClearModalOpen(false);
    }
  };

  const handleMarkReviewed = async () => {
    await executeStatusChange('REVIEWED');
  };

  const handleConfirmClear = async () => {
    await executeStatusChange('CLEARED');
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 backdrop-blur-md shadow-xl space-y-5">
      {/* Header with Current Status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <ShieldCheck className="w-5 h-5 text-blue-400" />
          <h3 className="text-base font-bold text-white tracking-tight">
            Reviewer Actions
          </h3>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Current Status:</span>
          <StatusBadge status={currentStatus} />
        </div>
      </div>

      {/* Success Notification */}
      {feedbackSuccess && (
        <div
          role="status"
          className="p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-xs font-semibold text-emerald-300 flex items-center gap-2 animate-in fade-in"
        >
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{feedbackSuccess}</span>
        </div>
      )}

      {/* Error Notification */}
      {feedbackError && (
        <div
          role="alert"
          className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/30 text-xs text-rose-300 flex items-start gap-2 animate-in fade-in"
        >
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-semibold block">{feedbackError}</span>
          </div>
        </div>
      )}

      {/* When Cleared: Terminal state notice */}
      {isCleared ? (
        <div className="p-4 rounded-xl bg-slate-950/60 border border-emerald-500/20 text-xs text-slate-300 flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center shrink-0">
            <Lock className="w-4 h-4" />
          </div>
          <div>
            <h4 className="font-bold text-white">Review Workflow Finalized</h4>
            <p className="text-slate-400 text-[11px] mt-0.5">
              This transaction has been verified and marked as CLEARED. No further workflow transitions are required.
            </p>
          </div>
        </div>
      ) : (
        /* Active Workflow Controls */
        <div className="space-y-4">
          <ReviewNoteInput
            value={note}
            onChange={setNote}
            disabled={isSubmitting}
            maxLength={2000}
          />

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-3 pt-1">
            {!isReviewed && (
              <button
                type="button"
                onClick={handleMarkReviewed}
                disabled={isSubmitting}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-xs font-bold text-white shadow-lg shadow-blue-900/30 transition-all disabled:opacity-50 cursor-pointer active:scale-95"
              >
                {isSubmitting ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Check className="w-3.5 h-3.5" />
                )}
                <span>Mark Reviewed</span>
              </button>
            )}

            <button
              type="button"
              onClick={() => setIsClearModalOpen(true)}
              disabled={isSubmitting}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-xs font-bold text-white shadow-lg shadow-emerald-950/40 transition-all disabled:opacity-50 cursor-pointer active:scale-95"
            >
              {isSubmitting ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <ShieldCheck className="w-3.5 h-3.5" />
              )}
              <span>Mark Cleared</span>
            </button>
          </div>
        </div>
      )}

      {/* Confirmation Modal for Clearing */}
      <ClearConfirmationModal
        isOpen={isClearModalOpen}
        onClose={() => setIsClearModalOpen(false)}
        onConfirm={handleConfirmClear}
        note={note}
        isSubmitting={isSubmitting}
      />
    </div>
  );
};
