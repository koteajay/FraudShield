import React from 'react';

export interface StatCardProps {
  label: string;
  value: number | string;
  icon: React.ReactNode;
  variant?: 'default' | 'critical' | 'high' | 'warning' | 'success';
  trend?: string;
  description?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  icon,
  variant = 'default',
  trend,
  description,
}) => {
  const variantStyles = {
    default: {
      border: 'border-slate-800 hover:border-slate-700',
      iconBox: 'bg-slate-800/70 text-slate-300 border-slate-700/60',
      valueColor: 'text-white',
    },
    critical: {
      border: 'border-rose-900/50 hover:border-rose-800/80 bg-rose-950/20',
      iconBox: 'bg-rose-500/15 text-rose-400 border-rose-500/30 shadow-lg shadow-rose-950/50',
      valueColor: 'text-rose-300',
    },
    high: {
      border: 'border-amber-900/50 hover:border-amber-800/80 bg-amber-950/20',
      iconBox: 'bg-amber-500/15 text-amber-400 border-amber-500/30 shadow-lg shadow-amber-950/50',
      valueColor: 'text-amber-300',
    },
    warning: {
      border: 'border-yellow-900/40 hover:border-yellow-800/70 bg-yellow-950/15',
      iconBox: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30',
      valueColor: 'text-yellow-300',
    },
    success: {
      border: 'border-emerald-900/40 hover:border-emerald-800/70 bg-emerald-950/15',
      iconBox: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
      valueColor: 'text-emerald-300',
    },
  }[variant];

  const formattedValue =
    typeof value === 'number' ? value.toLocaleString() : value;

  return (
    <div
      className={`rounded-2xl p-5 border bg-slate-900/80 backdrop-blur-sm shadow-xl transition-all duration-200 flex flex-col justify-between ${variantStyles.border}`}
    >
      <div className="flex items-center justify-between gap-3 mb-3">
        <span className="text-xs uppercase tracking-wider font-semibold text-slate-400 select-none">
          {label}
        </span>
        <div className={`p-2.5 rounded-xl border ${variantStyles.iconBox}`}>
          {icon}
        </div>
      </div>

      <div className="flex items-baseline justify-between mt-1">
        <span className={`text-3xl font-extrabold tracking-tight font-mono ${variantStyles.valueColor}`}>
          {formattedValue}
        </span>
        {trend && (
          <span className="text-xs font-mono font-medium text-slate-400">
            {trend}
          </span>
        )}
      </div>

      {description && (
        <p className="text-[11px] text-slate-500 mt-2 font-medium">
          {description}
        </p>
      )}
    </div>
  );
};

export default StatCard;
