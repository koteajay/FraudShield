import React from 'react';
import type { TransactionStatus } from '../../types/transaction';
import { Clock, CheckCircle2, ShieldAlert, CheckCheck, HelpCircle } from 'lucide-react';

export interface StatusBadgeProps {
  status?: TransactionStatus | string | null;
  size?: 'sm' | 'md';
  showIcon?: boolean;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'md',
  showIcon = true,
  className = '',
}) => {
  const normalized = (status?.toUpperCase() || 'UNKNOWN') as TransactionStatus | 'UNKNOWN';

  const configMap: Record<
    TransactionStatus | 'UNKNOWN',
    {
      label: string;
      icon: React.ReactNode;
      containerClass: string;
    }
  > = {
    PENDING: {
      label: 'PENDING',
      icon: <Clock className="shrink-0" />,
      containerClass: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    },
    REVIEWED: {
      label: 'REVIEWED',
      icon: <CheckCircle2 className="shrink-0" />,
      containerClass: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
    },
    CLEARED: {
      label: 'CLEARED',
      icon: <CheckCheck className="shrink-0" />,
      containerClass: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    },
    FLAGGED: {
      label: 'FLAGGED',
      icon: <ShieldAlert className="shrink-0" />,
      containerClass: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    },
    UNKNOWN: {
      label: 'UNKNOWN',
      icon: <HelpCircle className="shrink-0" />,
      containerClass: 'bg-slate-800 text-slate-400 border-slate-700',
    },
  };

  const current = configMap[normalized] || configMap.UNKNOWN;

  const sizeClasses = {
    sm: 'text-[10px] px-2 py-0.5 gap-1 font-mono [&>svg]:w-3 [&>svg]:h-3',
    md: 'text-xs px-2.5 py-1 gap-1.5 font-medium [&>svg]:w-3.5 [&>svg]:h-3.5',
  }[size];

  return (
    <span
      className={`inline-flex items-center rounded-full border select-none ${current.containerClass} ${sizeClasses} ${className}`}
      aria-label={`Status: ${current.label}`}
    >
      {showIcon && current.icon}
      <span>{current.label}</span>
    </span>
  );
};

export default StatusBadge;
