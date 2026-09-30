import React from 'react';
import type { RiskLevel } from '../../types/transaction';
import { RiskBadge } from './RiskBadge';

export interface RiskScoreProps {
  score?: number | null;
  riskLevel?: RiskLevel;
  size?: 'sm' | 'md' | 'lg';
  showBar?: boolean;
  showBadge?: boolean;
  className?: string;
}

export const RiskScore: React.FC<RiskScoreProps> = ({
  score,
  riskLevel,
  size = 'md',
  showBar = true,
  showBadge = false,
  className = '',
}) => {
  const isAvailable = score !== undefined && score !== null && !isNaN(score);
  const clampedScore = isAvailable ? Math.min(100, Math.max(0, Math.round(score))) : 0;

  // Determine derived risk level if not explicitly provided
  const derivedLevel: RiskLevel =
    riskLevel ||
    (clampedScore >= 80
      ? 'CRITICAL'
      : clampedScore >= 60
      ? 'HIGH'
      : clampedScore >= 30
      ? 'MEDIUM'
      : 'LOW');

  const barColorMap: Record<RiskLevel, string> = {
    CRITICAL: 'bg-rose-500 shadow-rose-500/50',
    HIGH: 'bg-amber-500 shadow-amber-500/50',
    MEDIUM: 'bg-yellow-400 shadow-yellow-400/50',
    LOW: 'bg-emerald-500 shadow-emerald-500/50',
  };

  const textColorMap: Record<RiskLevel, string> = {
    CRITICAL: 'text-rose-400',
    HIGH: 'text-amber-400',
    MEDIUM: 'text-yellow-400',
    LOW: 'text-emerald-400',
  };

  const textSizes = {
    sm: 'text-xs',
    md: 'text-sm font-semibold',
    lg: 'text-xl font-bold',
  }[size];

  const barHeights = {
    sm: 'h-1.5 w-16',
    md: 'h-2 w-24',
    lg: 'h-2.5 w-36',
  }[size];

  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      <div className="flex items-center gap-2">
        <div className="flex items-baseline gap-1 font-mono">
          <span className={`${textSizes} ${textColorMap[derivedLevel]}`}>
            {isAvailable ? clampedScore : '--'}
          </span>
          <span className="text-[11px] text-slate-400 font-normal">/ 100</span>
        </div>

        {showBadge && <RiskBadge level={derivedLevel} size="sm" />}
      </div>

      {showBar && (
        <div
          className={`${barHeights} bg-slate-800 rounded-full overflow-hidden border border-slate-700/50`}
          title={`Risk Score: ${isAvailable ? clampedScore : 0}%`}
        >
          <div
            className={`h-full rounded-full transition-all duration-300 ${barColorMap[derivedLevel]}`}
            style={{ width: `${isAvailable ? clampedScore : 0}%` }}
          />
        </div>
      )}
    </div>
  );
};

export default RiskScore;
