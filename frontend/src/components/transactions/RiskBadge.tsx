import React from 'react';
import { ShieldCheck, AlertCircle, AlertTriangle, Flame, HelpCircle } from 'lucide-react';
import type { RiskLevel } from '../../types/transaction';

interface RiskBadgeProps {
  level: RiskLevel | string;
  score?: number;
  showScore?: boolean;
  className?: string;
}

interface RiskStyle {
  label: string;
  badge: string;
  dot: string;
  icon: React.ComponentType<{ className?: string }>;
}

const riskStyles: Record<string, RiskStyle> = {
  LOW: {
    label: 'LOW',
    badge: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/25',
    dot: 'bg-emerald-400',
    icon: ShieldCheck,
  },
  MEDIUM: {
    label: 'MEDIUM',
    badge: 'bg-amber-500/10 text-amber-300 border-amber-500/30',
    dot: 'bg-amber-400',
    icon: AlertCircle,
  },
  HIGH: {
    label: 'HIGH',
    badge: 'bg-orange-500/15 text-orange-200 border-orange-500/40',
    dot: 'bg-orange-400',
    icon: AlertTriangle,
  },
  CRITICAL: {
    label: 'CRITICAL',
    badge: 'bg-rose-500/20 text-rose-200 border-rose-500/50 shadow-sm shadow-rose-950/50',
    dot: 'bg-rose-500 animate-pulse',
    icon: Flame,
  },
};

const defaultStyle: RiskStyle = {
  label: 'UNKNOWN',
  badge: 'bg-slate-800 text-slate-300 border-slate-700',
  dot: 'bg-slate-400',
  icon: HelpCircle,
};

export const RiskBadge: React.FC<RiskBadgeProps> = ({
  level,
  score,
  showScore = false,
  className = '',
}) => {
  const normalizedLevel = (level || '').toUpperCase().trim();
  const style = riskStyles[normalizedLevel] || {
    ...defaultStyle,
    label: normalizedLevel || 'UNKNOWN',
  };
  const IconComponent = style.icon;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide border ${style.badge} ${className}`}
      title={`Risk Level: ${style.label}${score != null ? ` (${score.toFixed(0)}/100)` : ''}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${style.dot}`} aria-hidden="true" />
      <IconComponent className="w-3.5 h-3.5" aria-hidden="true" />
      <span>{style.label}</span>
      {showScore && score != null && (
        <span className="font-mono text-[10px] opacity-80 pl-0.5">
          {score.toFixed(0)}
        </span>
      )}
    </span>
  );
};
