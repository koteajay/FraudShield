import React from 'react';
import type { RiskLevel } from '../../types/transaction';
import { ShieldAlert, AlertTriangle, AlertCircle, ShieldCheck, HelpCircle } from 'lucide-react';

export interface RiskBadgeProps {
  level?: RiskLevel | string | null;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  className?: string;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({
  level,
  size = 'md',
  showIcon = true,
  className = '',
}) => {
  const normalizedLevel = (level?.toUpperCase() || 'UNKNOWN') as RiskLevel | 'UNKNOWN';

  const configMap: Record<
    RiskLevel | 'UNKNOWN',
    {
      label: string;
      icon: React.ReactNode;
      containerClass: string;
      textClass: string;
    }
  > = {
    CRITICAL: {
      label: 'CRITICAL',
      icon: <ShieldAlert className="shrink-0" />,
      containerClass: 'bg-rose-500/15 text-rose-300 border-rose-500/40 shadow-sm shadow-rose-950/40',
      textClass: 'font-bold tracking-wider',
    },
    HIGH: {
      label: 'HIGH',
      icon: <AlertTriangle className="shrink-0" />,
      containerClass: 'bg-amber-500/15 text-amber-300 border-amber-500/40 shadow-sm shadow-amber-950/40',
      textClass: 'font-semibold tracking-wide',
    },
    MEDIUM: {
      label: 'MEDIUM',
      icon: <AlertCircle className="shrink-0" />,
      containerClass: 'bg-yellow-500/15 text-yellow-300 border-yellow-500/30',
      textClass: 'font-medium',
    },
    LOW: {
      label: 'LOW',
      icon: <ShieldCheck className="shrink-0" />,
      containerClass: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
      textClass: 'font-medium',
    },
    UNKNOWN: {
      label: 'UNKNOWN',
      icon: <HelpCircle className="shrink-0" />,
      containerClass: 'bg-slate-800/60 text-slate-400 border-slate-700/60',
      textClass: 'font-normal',
    },
  };

  const current = configMap[normalizedLevel] || configMap.UNKNOWN;

  const sizeClasses = {
    sm: 'text-[10px] px-2 py-0.5 gap-1 [&>svg]:w-3 [&>svg]:h-3',
    md: 'text-xs px-2.5 py-1 gap-1.5 [&>svg]:w-3.5 [&>svg]:h-3.5',
    lg: 'text-sm px-3.5 py-1.5 gap-2 [&>svg]:w-4 [&>svg]:h-4',
  }[size];

  return (
    <span
      className={`inline-flex items-center rounded-md border font-mono select-none ${current.containerClass} ${sizeClasses} ${className}`}
      aria-label={`Risk Level: ${current.label}`}
    >
      {showIcon && current.icon}
      <span className={current.textClass}>{current.label}</span>
    </span>
  );
};

export default RiskBadge;
