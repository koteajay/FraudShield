import React from 'react';
import type { LucideIcon } from 'lucide-react';

export type StatVariant = 'default' | 'warning' | 'danger' | 'critical' | 'success' | 'info' | 'purple';

export interface StatCardProps {
  title: string;
  value: number | string;
  description?: string;
  icon: LucideIcon;
  variant?: StatVariant;
  badgeText?: string;
  onClick?: () => void;
  className?: string;
}

const variantStyles: Record<
  StatVariant,
  { card: string; iconBg: string; iconText: string; valueText: string }
> = {
  default: {
    card: 'border-slate-800 bg-slate-900/60 hover:border-slate-700',
    iconBg: 'bg-slate-800/80 text-slate-300 border-slate-700/50',
    iconText: 'text-slate-300',
    valueText: 'text-white',
  },
  info: {
    card: 'border-blue-900/40 bg-blue-950/20 hover:border-blue-800/60',
    iconBg: 'bg-blue-600/20 text-blue-400 border-blue-500/30',
    iconText: 'text-blue-400',
    valueText: 'text-blue-100',
  },
  warning: {
    card: 'border-amber-900/40 bg-amber-950/20 hover:border-amber-800/60',
    iconBg: 'bg-amber-600/20 text-amber-400 border-amber-500/30',
    iconText: 'text-amber-400',
    valueText: 'text-amber-200',
  },
  danger: {
    card: 'border-orange-900/40 bg-orange-950/20 hover:border-orange-800/60',
    iconBg: 'bg-orange-600/20 text-orange-400 border-orange-500/30',
    iconText: 'text-orange-400',
    valueText: 'text-orange-200',
  },
  critical: {
    card: 'border-rose-900/50 bg-rose-950/30 hover:border-rose-800/70 shadow-lg shadow-rose-950/20',
    iconBg: 'bg-rose-600/25 text-rose-400 border-rose-500/40',
    iconText: 'text-rose-400',
    valueText: 'text-rose-200',
  },
  success: {
    card: 'border-emerald-900/40 bg-emerald-950/20 hover:border-emerald-800/60',
    iconBg: 'bg-emerald-600/20 text-emerald-400 border-emerald-500/30',
    iconText: 'text-emerald-400',
    valueText: 'text-emerald-200',
  },
  purple: {
    card: 'border-purple-900/40 bg-purple-950/20 hover:border-purple-800/60',
    iconBg: 'bg-purple-600/20 text-purple-400 border-purple-500/30',
    iconText: 'text-purple-400',
    valueText: 'text-purple-200',
  },
};

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  description,
  icon: Icon,
  variant = 'default',
  badgeText,
  onClick,
  className = '',
}) => {
  const styles = variantStyles[variant] || variantStyles.default;
  const isInteractive = Boolean(onClick);

  return (
    <div
      onClick={onClick}
      role={isInteractive ? 'button' : undefined}
      tabIndex={isInteractive ? 0 : undefined}
      onKeyDown={
        isInteractive
          ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onClick?.();
              }
            }
          : undefined
      }
      className={`rounded-xl border p-4.5 transition-all duration-200 backdrop-blur-sm ${styles.card} ${
        isInteractive ? 'cursor-pointer hover:scale-[1.01]' : ''
      } ${className}`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
          {title}
        </span>
        <div
          className={`p-2 rounded-lg border ${styles.iconBg} flex items-center justify-center`}
          aria-hidden="true"
        >
          <Icon className={`w-4 h-4 ${styles.iconText}`} />
        </div>
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        <span className={`text-2xl sm:text-3xl font-bold tracking-tight ${styles.valueText}`}>
          {typeof value === 'number' ? value.toLocaleString() : value}
        </span>
        {badgeText && (
          <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-slate-800 text-slate-300 border border-slate-700">
            {badgeText}
          </span>
        )}
      </div>

      {description && (
        <p className="mt-1 text-xs text-slate-400 truncate">{description}</p>
      )}
    </div>
  );
};
