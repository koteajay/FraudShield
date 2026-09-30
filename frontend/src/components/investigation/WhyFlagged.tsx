import React from 'react';
import { HelpCircle } from 'lucide-react';
import { RiskScoreCard } from './RiskScoreCard';
import { TriggeredRules } from './TriggeredRules';
import type { TransactionDetail } from '../../types/transaction';

interface WhyFlaggedProps {
  transaction: TransactionDetail;
}

export const WhyFlagged: React.FC<WhyFlaggedProps> = ({ transaction }) => {
  const triggeredRules = (transaction.rule_results || []).filter((r) => r.is_triggered);
  const riskScore = transaction.risk?.score ?? transaction.risk_score ?? 0;
  const riskLevel = transaction.risk?.level ?? transaction.risk_level ?? 'LOW';
  const explanation =
    transaction.risk?.explanation ||
    (triggeredRules.length > 0
      ? 'Suspicious activity flagged by automated detection rules.'
      : 'No suspicious indicators detected; transaction appears consistent with normal usage.');

  return (
    <section aria-labelledby="why-flagged-heading" className="space-y-4">
      <div className="flex items-center gap-2">
        <HelpCircle className="w-5 h-5 text-blue-400" />
        <h2 id="why-flagged-heading" className="text-xl font-bold text-white tracking-tight">
          Why Flagged?
        </h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Risk Score & Overall Assessment Summary */}
        <div className="lg:col-span-4">
          <RiskScoreCard
            score={riskScore}
            level={riskLevel}
            explanation={explanation}
            ruleCount={triggeredRules.length}
          />
        </div>

        {/* Right Column: Triggered Rules & Evidence Breakdown */}
        <div className="lg:col-span-8 bg-slate-900/60 border border-slate-800 rounded-2xl p-5 backdrop-blur-md">
          <TriggeredRules rules={transaction.rule_results || []} />
        </div>
      </div>
    </section>
  );
};
