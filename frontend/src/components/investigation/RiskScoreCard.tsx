import React from 'react';
import { ShieldAlert, ShieldCheck } from 'lucide-react';
import { RiskBadge } from '../transactions/RiskBadge';
import type { RiskLevel } from '../../types/transaction';

interface RiskScoreCardProps {
  score: number;
  level: RiskLevel | string;
  explanation?: string;
  ruleCount?: number;
}

export const RiskScoreCard: React.FC<RiskScoreCardProps> = ({
  score,
  level,
  explanation,
  ruleCount = 0,
}) => {
  const normalizedLevel = (level || 'LOW').toUpperCase();
  const clampedScore = Math.min(100, Math.max(0, Math.round(score)));

  // Color theme mapping for the score visualizer
  const getTheme = () => {
    switch (normalizedLevel) {
      case 'CRITICAL':
        return {
          textColor: 'text-rose-400',
          borderColor: 'border-rose-500/40',
          bgGradient: 'from-rose-950/40 via-slate-900/60 to-slate-900/40',
          progressColor: 'bg-rose-500',
          glowColor: 'shadow-rose-900/30',
        };
      case 'HIGH':
        return {
          textColor: 'text-orange-400',
          borderColor: 'border-orange-500/40',
          bgGradient: 'from-orange-950/30 via-slate-900/60 to-slate-900/40',
          progressColor: 'bg-orange-500',
          glowColor: 'shadow-orange-900/20',
        };
      case 'MEDIUM':
        return {
          textColor: 'text-amber-400',
          borderColor: 'border-amber-500/40',
          bgGradient: 'from-amber-950/20 via-slate-900/60 to-slate-900/40',
          progressColor: 'bg-amber-500',
          glowColor: 'shadow-amber-900/20',
        };
      case 'LOW':
      default:
        return {
          textColor: 'text-emerald-400',
          borderColor: 'border-emerald-500/30',
          bgGradient: 'from-emerald-950/20 via-slate-900/60 to-slate-900/40',
          progressColor: 'bg-emerald-500',
          glowColor: 'shadow-emerald-900/20',
        };
    }
  };

  const theme = getTheme();

  return (
    <div
      className={`rounded-2xl border ${theme.borderColor} bg-gradient-to-br ${theme.bgGradient} p-6 shadow-xl ${theme.glowColor} backdrop-blur-md flex flex-col justify-between`}
    >
      <div>
        <div className="flex items-center justify-between gap-3 mb-4">
          <div className="flex items-center gap-2">
            {clampedScore >= 70 ? (
              <ShieldAlert className={`w-5 h-5 ${theme.textColor}`} />
            ) : (
              <ShieldCheck className={`w-5 h-5 ${theme.textColor}`} />
            )}
            <span className="text-xs font-semibold tracking-wider uppercase text-slate-300">
              Risk Evaluation
            </span>
          </div>
          <RiskBadge level={level} className="scale-105" />
        </div>

        {/* Score & Gauge */}
        <div className="flex items-baseline gap-2 mb-2">
          <span className={`text-6xl font-black font-mono tracking-tight ${theme.textColor}`}>
            {clampedScore}
          </span>
          <span className="text-lg font-mono text-slate-500 font-semibold">/ 100</span>
        </div>

        {/* Progress Bar Gauge */}
        <div className="w-full bg-slate-950 rounded-full h-3.5 p-0.5 border border-slate-800 overflow-hidden mb-4">
          <div
            className={`h-full rounded-full transition-all duration-700 ease-out ${theme.progressColor}`}
            style={{ width: `${clampedScore}%` }}
            role="progressbar"
            aria-valuenow={clampedScore}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>

        {/* Explanation string from backend */}
        {explanation && (
          <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 text-xs text-slate-300 leading-relaxed">
            <span className="font-semibold text-slate-200 block mb-1">
              Assessment Summary:
            </span>
            {explanation}
          </div>
        )}
      </div>

      <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
        <span>Triggered Fraud Rules</span>
        <span className="font-mono font-bold text-white bg-slate-800 px-2 py-0.5 rounded">
          {ruleCount}
        </span>
      </div>
    </div>
  );
};
