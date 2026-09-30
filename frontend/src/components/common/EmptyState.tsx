import React from 'react';
import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  message?: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No records found',
  message = 'There are currently no items matching your criteria.',
  actionLabel,
  onAction,
  className = '',
}) => {
  return (
    <div
      className={`rounded-xl border border-slate-800 bg-slate-900/30 p-8 text-center max-w-md mx-auto space-y-3 ${className}`}
    >
      <div className="inline-flex p-3 rounded-full bg-slate-800/80 text-slate-400 border border-slate-700/50">
        <Inbox className="w-6 h-6 text-slate-400" aria-hidden="true" />
      </div>
      <div>
        <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
        <p className="mt-1 text-xs text-slate-400 leading-relaxed">{message}</p>
      </div>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          type="button"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-950"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
};
