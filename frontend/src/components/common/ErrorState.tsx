import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  retryLabel?: string;
  isRetrying?: boolean;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'An error occurred',
  message = 'Unable to load data. Please try again.',
  onRetry,
  retryLabel = 'Retry',
  isRetrying = false,
}) => {
  return (
    <div
      role="alert"
      className="flex flex-col items-center justify-center p-8 text-center bg-rose-950/20 border border-rose-900/40 rounded-2xl max-w-lg mx-auto my-4"
    >
      <div className="p-3 bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded-full mb-3 shadow-lg shadow-rose-950/50">
        <AlertTriangle className="w-6 h-6" />
      </div>
      <h3 className="text-base font-semibold text-white mb-1">{title}</h3>
      <p className="text-sm text-slate-400 mb-5 max-w-sm leading-relaxed">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          disabled={isRetrying}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-xl bg-rose-600 hover:bg-rose-500 text-white transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-rose-900/30 cursor-pointer"
        >
          <RefreshCw className={`w-4 h-4 ${isRetrying ? 'animate-spin' : ''}`} />
          {isRetrying ? 'Retrying...' : retryLabel}
        </button>
      )}
    </div>
  );
};

export default ErrorState;
