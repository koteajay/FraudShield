import React from 'react';
import type { FraudRuleResult as FraudRuleResultType } from '../../types/fraud';
import { FraudFlagBadge } from '../risk/FraudFlagBadge';
import { CheckCircle2, MinusCircle, FileText } from 'lucide-react';

export interface FraudRuleResultProps {
  rule: FraudRuleResultType;
}

/**
 * Helper to render evidence whether string, array, or key-value object.
 */
function renderEvidence(evidence: FraudRuleResultType['evidence']): React.ReactNode {
  if (!evidence) {
    return <span className="text-slate-500 italic">Evidence unavailable</span>;
  }

  if (typeof evidence === 'string') {
    return <p className="text-xs text-slate-300 font-mono leading-relaxed">{evidence}</p>;
  }

  if (typeof evidence === 'object') {
    return (
      <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-2.5 font-mono text-xs text-slate-300 space-y-1">
        {Object.entries(evidence).map(([key, val]) => (
          <div key={key} className="flex flex-wrap items-baseline gap-2">
            <span className="text-slate-500">{key}:</span>
            <span className="text-slate-200 font-medium">
              {typeof val === 'object' ? JSON.stringify(val) : String(val)}
            </span>
          </div>
        ))}
      </div>
    );
  }

  return <span className="text-slate-300 text-xs">{String(evidence)}</span>;
}

export const FraudRuleResult: React.FC<FraudRuleResultProps> = ({ rule }) => {
  const { ruleName, isTriggered, reason, evidence, scoreContribution } = rule;

  return (
    <div
      className={`rounded-2xl p-5 border transition-all duration-200 ${
        isTriggered
          ? 'bg-rose-950/20 border-rose-900/50 shadow-lg shadow-rose-950/30'
          : 'bg-slate-900/50 border-slate-800/70 opacity-75'
      }`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800/80">
        <div className="flex items-center gap-3">
          <FraudFlagBadge rule={ruleName} size="md" />

          {/* Triggered badge */}
          {isTriggered ? (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/40">
              <CheckCircle2 className="w-3.5 h-3.5 text-rose-400" />
              TRIGGERED
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-800 text-slate-400 border border-slate-700">
              <MinusCircle className="w-3 h-3 text-slate-500" />
              Not Triggered
            </span>
          )}
        </div>

        {/* Score contribution */}
        {isTriggered && scoreContribution !== undefined && (
          <div className="inline-flex items-baseline gap-1 font-mono">
            <span className="text-xs text-slate-400 font-medium">Score Impact:</span>
            <span className="text-sm font-bold text-rose-400">
              +{scoreContribution}
            </span>
          </div>
        )}
      </div>

      <div className="mt-3.5 space-y-3">
        {/* Reason */}
        {reason && (
          <div>
            <span className="text-[11px] uppercase tracking-wider font-semibold text-slate-400 block mb-1">
              Reason
            </span>
            <p className="text-xs text-slate-200 leading-relaxed">{reason}</p>
          </div>
        )}

        {/* Evidence */}
        <div>
          <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider font-semibold text-slate-400 mb-1.5">
            <FileText className="w-3.5 h-3.5 text-blue-400" />
            <span>Evidence</span>
          </div>
          {renderEvidence(evidence)}
        </div>
      </div>
    </div>
  );
};

export default FraudRuleResult;
