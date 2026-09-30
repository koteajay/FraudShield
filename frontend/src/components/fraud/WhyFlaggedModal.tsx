import React, { useEffect } from 'react';
import type { Transaction } from '../../types/transaction';
import type { FraudAssessment } from '../../types/fraud';
import { RiskBadge } from '../risk/RiskBadge';
import { RiskScore } from '../risk/RiskScore';
import { FraudFlagBadge } from '../risk/FraudFlagBadge';
import {
  X,
  ShieldAlert,
  Sparkles,
  Info,
  CheckCircle2,
  FileText,
  BarChart3,
} from 'lucide-react';

export interface WhyFlaggedModalProps {
  isOpen: boolean;
  onClose: () => void;
  transaction: Transaction;
  assessment?: FraudAssessment | null;
}

export const WhyFlaggedModal: React.FC<WhyFlaggedModalProps> = ({
  isOpen,
  onClose,
  transaction,
  assessment,
}) => {
  // Close on Escape key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'auto';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  // Derive triggered rules and contributions
  const triggeredRules =
    assessment?.rules?.filter((r) => r.isTriggered) || [];

  // Fallback: If assessment has flags instead of rule results, map flags
  const effectiveFlags =
    triggeredRules.length > 0
      ? triggeredRules
      : (assessment?.flags || []).map((f) => ({
          ruleName: f.ruleName,
          isTriggered: true,
          reason: f.description,
          evidence: (f.metadata?.evidence as string | Record<string, unknown>) || null,
          scoreContribution: f.scoreImpact,
        }));

  const totalContribution = effectiveFlags.reduce(
    (sum, r) => sum + (r.scoreContribution || 0),
    0
  );

  const displayScore =
    assessment?.riskScore !== undefined ? assessment.riskScore : transaction.riskScore;
  const displayLevel =
    assessment?.riskLevel !== undefined ? assessment.riskLevel : transaction.riskLevel;

  // Construct deterministic summary if no natural language explanation exists from backend
  const explanationText =
    assessment?.explanation ||
    assessment?.summary ||
    (effectiveFlags.length > 0
      ? `This transaction was flagged due to ${effectiveFlags.length} triggered fraud detection rule${
          effectiveFlags.length > 1 ? 's' : ''
        } contributing a cumulative +${totalContribution} risk score.`
      : 'No automated fraud rules were triggered for this transaction.');

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="why-flagged-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto"
    >
      {/* Backdrop */}
      <div
        onClick={onClose}
        className="fixed inset-0 bg-slate-950/80 backdrop-blur-md transition-opacity"
      />

      {/* Modal Dialog Content */}
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden z-10 my-8 flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-rose-500/15 text-rose-400 border border-rose-500/30 shadow-lg shadow-rose-950/50">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <h2
                id="why-flagged-title"
                className="text-lg font-bold text-white tracking-tight flex items-center gap-2"
              >
                Why Was This Transaction Flagged?
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                Transaction ID: {transaction.id}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 transition-colors cursor-pointer"
            aria-label="Close dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* 1. Risk Score & Level Hero Banner */}
          <div className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <span className="text-xs uppercase tracking-wider font-semibold text-slate-400 block mb-1">
                Evaluated Risk Severity
              </span>
              <div className="flex items-center gap-3">
                <RiskBadge level={displayLevel} size="lg" />
                <span className="text-xs text-slate-500 font-mono">
                  User: {transaction.userId}
                </span>
              </div>
            </div>

            <div className="sm:text-right">
              <span className="text-xs uppercase tracking-wider font-semibold text-slate-400 block mb-1">
                Risk Score
              </span>
              <RiskScore
                score={displayScore}
                riskLevel={displayLevel}
                size="lg"
                showBar={true}
              />
            </div>
          </div>

          {/* 2. Overall Explanation */}
          <div className="p-4 rounded-xl bg-blue-950/20 border border-blue-900/40 text-blue-200 text-xs leading-relaxed flex items-start gap-3">
            <Sparkles className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-blue-300 block mb-0.5">
                Evaluation Summary
              </span>
              <p className="text-slate-300">{explanationText}</p>
            </div>
          </div>

          {/* 3. Triggered Rules & Score Contribution Breakdown */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-purple-400" />
                Score Contribution Breakdown
              </h3>
              <span className="text-xs font-mono text-rose-400 font-semibold">
                Total Contribution: +{totalContribution}
              </span>
            </div>

            {effectiveFlags.length === 0 ? (
              <div className="p-6 text-center rounded-xl bg-slate-950/40 border border-slate-800 text-xs text-slate-500">
                No individual rule contributions recorded.
              </div>
            ) : (
              <div className="space-y-2.5">
                {effectiveFlags.map((rule, idx) => {
                  const contribution = rule.scoreContribution || 0;
                  const ratio =
                    totalContribution > 0
                      ? Math.round((contribution / totalContribution) * 100)
                      : 0;

                  return (
                    <div
                      key={idx}
                      className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-slate-700 transition"
                    >
                      <div className="flex items-center justify-between gap-3 mb-2">
                        <div className="flex items-center gap-2">
                          <CheckCircle2 className="w-4 h-4 text-rose-400 shrink-0" />
                          <FraudFlagBadge rule={rule.ruleName} size="sm" />
                        </div>
                        <span className="font-mono text-xs font-bold text-rose-400">
                          +{contribution}
                        </span>
                      </div>

                      {/* Visual Contribution Bar */}
                      <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden mb-2">
                        <div
                          className="h-full bg-rose-500 rounded-full"
                          style={{ width: `${ratio}%` }}
                        />
                      </div>

                      {rule.reason && (
                        <p className="text-[11px] text-slate-400 leading-normal mb-1">
                          {rule.reason}
                        </p>
                      )}

                      {/* Evidence */}
                      {rule.evidence && (
                        <div className="mt-2 pt-2 border-t border-slate-900 flex items-start gap-1.5 text-[11px] text-slate-400 font-mono">
                          <FileText className="w-3 h-3 text-slate-500 shrink-0 mt-0.5" />
                          <span>
                            Evidence:{' '}
                            {typeof rule.evidence === 'object'
                              ? JSON.stringify(rule.evidence)
                              : String(rule.evidence)}
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* 4. Transaction Context Snapshot */}
          <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800/80">
            <span className="text-[11px] uppercase tracking-wider font-semibold text-slate-400 block mb-2">
              Context Details
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div>
                <span className="text-slate-500 block text-[10px]">AMOUNT</span>
                <span className="text-white font-semibold">
                  {transaction.amount} {transaction.currency}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">LOCATION</span>
                <span className="text-slate-300">
                  {transaction.location || 'Unknown'}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">STATUS</span>
                <span className="text-slate-300">{transaction.status}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">TIMESTAMP</span>
                <span className="text-slate-400 truncate block">
                  {new Date(transaction.timestamp).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-blue-400" />
            <span>Explainable AI Risk Scoring Engine</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium transition-colors cursor-pointer"
          >
            Close Investigation
          </button>
        </div>
      </div>
    </div>
  );
};

export default WhyFlaggedModal;
