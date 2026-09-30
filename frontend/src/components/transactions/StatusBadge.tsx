import React from 'react';
import {
  Clock,
  CheckCircle2,
  ShieldCheck,
  AlertOctagon,
  Flag,
  HelpCircle,
} from 'lucide-react';
import type { ReviewStatus, TransactionStatus } from '../../types/transaction';

interface StatusBadgeProps {
  status: ReviewStatus | TransactionStatus | string;
  className?: string;
}

interface StatusStyle {
  label: string;
  badge: string;
  icon: React.ComponentType<{ className?: string }>;
}

const statusMap: Record<string, StatusStyle> = {
  PENDING_REVIEW: {
    label: 'Pending Review',
    badge: 'bg-blue-500/10 text-blue-300 border-blue-500/30',
    icon: Clock,
  },
  IN_REVIEW: {
    label: 'In Review',
    badge: 'bg-blue-500/15 text-blue-200 border-blue-500/40',
    icon: Clock,
  },
  UNDER_REVIEW: {
    label: 'Under Review',
    badge: 'bg-blue-500/15 text-blue-200 border-blue-500/40',
    icon: Clock,
  },
  REVIEWED: {
    label: 'Reviewed',
    badge: 'bg-purple-500/10 text-purple-300 border-purple-500/30',
    icon: CheckCircle2,
  },
  CLEARED: {
    label: 'Cleared',
    badge: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
    icon: ShieldCheck,
  },
  RESOLVED_LEGITIMATE: {
    label: 'Legitimate',
    badge: 'bg-emerald-500/15 text-emerald-200 border-emerald-500/35',
    icon: ShieldCheck,
  },
  RESOLVED_FRAUD: {
    label: 'Confirmed Fraud',
    badge: 'bg-rose-500/20 text-rose-200 border-rose-500/50',
    icon: AlertOctagon,
  },
  ESCALATED: {
    label: 'Escalated',
    badge: 'bg-orange-500/15 text-orange-200 border-orange-500/40',
    icon: AlertOctagon,
  },
  FLAGGED: {
    label: 'Flagged',
    badge: 'bg-amber-500/15 text-amber-200 border-amber-500/40',
    icon: Flag,
  },
  APPROVED: {
    label: 'Approved',
    badge: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/25',
    icon: ShieldCheck,
  },
  DECLINED: {
    label: 'Declined',
    badge: 'bg-rose-500/15 text-rose-300 border-rose-500/35',
    icon: AlertOctagon,
  },
  PENDING: {
    label: 'Pending',
    badge: 'bg-slate-800 text-slate-300 border-slate-700',
    icon: Clock,
  },
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const normalized = (status || '').toUpperCase().trim();
  const config = statusMap[normalized] || {
    label: normalized.replace(/_/g, ' ') || 'Unknown',
    badge: 'bg-slate-800 text-slate-300 border-slate-700',
    icon: HelpCircle,
  };
  const IconComponent = config.icon;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${config.badge} ${className}`}
    >
      <IconComponent className="w-3.5 h-3.5" aria-hidden="true" />
      <span>{config.label}</span>
    </span>
  );
};
