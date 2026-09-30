import React from 'react';

export type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info' | 'neutral';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
  dot?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'default',
  size = 'md',
  dot = false,
  children,
  className = '',
  ...props
}) => {
  const variantStyles: Record<BadgeVariant, { badge: string; dot: string }> = {
    default: {
      badge: 'bg-slate-800 text-slate-300 border-slate-700',
      dot: 'bg-slate-400',
    },
    success: {
      badge: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
      dot: 'bg-emerald-400',
    },
    warning: {
      badge: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      dot: 'bg-amber-400',
    },
    danger: {
      badge: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
      dot: 'bg-rose-400',
    },
    info: {
      badge: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
      dot: 'bg-blue-400',
    },
    neutral: {
      badge: 'bg-slate-900 text-slate-400 border-slate-800',
      dot: 'bg-slate-500',
    },
  };

  const sizeStyles = {
    sm: 'text-[11px] px-2 py-0.5 gap-1 font-mono',
    md: 'text-xs px-2.5 py-1 gap-1.5 font-medium',
  }[size];

  const config = variantStyles[variant];

  return (
    <span
      className={`inline-flex items-center rounded-full border ${config.badge} ${sizeStyles} ${className}`}
      {...props}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />}
      {children}
    </span>
  );
};

export default Badge;
