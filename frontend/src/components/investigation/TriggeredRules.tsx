import React, { useState } from 'react';
import { ChevronDown, ChevronUp, AlertCircle, CheckCircle2 } from 'lucide-react';
import { RuleEvidence } from './RuleEvidence';
import type { RuleResultDetail } from '../../types/transaction';

interface TriggeredRulesProps {
  rules?: RuleResultDetail[];
}

export const TriggeredRules: React.FC<TriggeredRulesProps> = ({ rules = [] }) => {
  // Filter for triggered rules if the list contains both triggered and non-triggered
  const triggeredRules = rules.filter((r) => r.is_triggered);

  // Keep track of which rule cards are expanded. Default first one or all open if small list
  const [expandedMap, setExpandedMap] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {};
    triggeredRules.forEach((rule, idx) => {
      // expand all if <= 3 rules, otherwise expand first 2
      initial[rule.rule_id || String(idx)] = idx < 3;
    });
    return initial;
  });

  const toggleExpand = (id: string) => {
    setExpandedMap((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const expandAll = () => {
    const next: Record<string, boolean> = {};
    triggeredRules.forEach((rule, idx) => {
      next[rule.rule_id || String(idx)] = true;
    });
    setExpandedMap(next);
  };

  const collapseAll = () => {
    setExpandedMap({});
  };

  if (triggeredRules.length === 0) {
    return (
      <div className="rounded-2xl border border-emerald-500/20 bg-emerald-950/10 p-6 text-center">
        <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
        <h4 className="text-sm font-semibold text-emerald-200">No Triggered Fraud Rules</h4>
        <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
          All automated rule evaluations returned negative for anomalous or malicious patterns.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Controls header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400" />
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Triggered Rules ({triggeredRules.length})
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={expandAll}
            className="text-[11px] text-slate-400 hover:text-white transition-colors"
          >
            Expand all
          </button>
          <span className="text-slate-700">|</span>
          <button
            type="button"
            onClick={collapseAll}
            className="text-[11px] text-slate-400 hover:text-white transition-colors"
          >
            Collapse all
          </button>
        </div>
      </div>

      {/* Rules Accordion List */}
      <div className="space-y-2.5">
        {triggeredRules.map((rule, idx) => {
          const ruleKey = rule.rule_id || String(idx);
          const isExpanded = !!expandedMap[ruleKey];
          const reason = rule.reason || rule.details?.reason || 'Rule condition matched transaction anomaly.';
          const evidence = rule.evidence || rule.details?.evidence;
          const scoreContrib =
            rule.score_contribution != null
              ? rule.score_contribution
              : rule.details?.score_contribution;

          return (
            <div
              key={ruleKey}
              className={`rounded-xl border transition-all duration-200 overflow-hidden ${
                isExpanded
                  ? 'border-slate-700 bg-slate-900/90 shadow-lg'
                  : 'border-slate-800 bg-slate-900/50 hover:border-slate-700/80 hover:bg-slate-900/70'
              }`}
            >
              {/* Card Header / Summary Clickable Row */}
              <button
                type="button"
                onClick={() => toggleExpand(ruleKey)}
                aria-expanded={isExpanded}
                className="w-full p-4 flex items-center justify-between gap-4 text-left cursor-pointer"
              >
                <div className="flex items-start gap-3 min-w-0">
                  <div className="mt-0.5 w-5 h-5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/40 flex items-center justify-center shrink-0">
                    <span className="text-xs font-bold">✓</span>
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="text-sm font-bold text-white tracking-tight">
                        {rule.rule_name || rule.rule_id}
                      </h4>
                      {rule.severity && (
                        <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                          {rule.severity}
                        </span>
                      )}
                    </div>
                    {!isExpanded && (
                      <p className="text-xs text-slate-400 mt-1 truncate max-w-xl">
                        {reason}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  {scoreContrib != null && (
                    <span className="font-mono text-sm font-extrabold text-rose-400 bg-rose-950/40 border border-rose-500/30 px-2 py-0.5 rounded-md">
                      +{scoreContrib}
                    </span>
                  )}
                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4 text-slate-400" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-slate-400" />
                  )}
                </div>
              </button>

              {/* Expanded Details Body */}
              {isExpanded && (
                <div className="px-4 pb-4 pt-1 border-t border-slate-800/80 space-y-3">
                  <div>
                    <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                      Reason:
                    </span>
                    <p className="text-xs text-slate-200 leading-relaxed bg-slate-950/50 p-2.5 rounded-lg border border-slate-800">
                      {reason}
                    </p>
                  </div>

                  <div>
                    <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1.5">
                      Captured Evidence:
                    </span>
                    <RuleEvidence evidence={evidence} />
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
