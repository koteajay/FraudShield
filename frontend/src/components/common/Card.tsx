import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'subtle';
  className?: string;
  children: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({
  variant = 'default',
  className = '',
  children,
  ...props
}) => {
  const variantStyles = {
    default: 'bg-slate-900/80 border-slate-800 shadow-xl backdrop-blur-sm',
    elevated: 'bg-slate-900 border-slate-700/80 shadow-2xl',
    subtle: 'bg-slate-950/60 border-slate-800/80',
  }[variant];

  return (
    <div
      className={`border rounded-2xl p-6 transition-all duration-200 ${variantStyles} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export default Card;
