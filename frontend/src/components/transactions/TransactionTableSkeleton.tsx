import React from 'react';

export const TransactionTableSkeleton: React.FC<{ rows?: number }> = ({ rows = 6 }) => {
  return (
    <div
      role="status"
      aria-label="Loading transactions table"
      className="divide-y divide-slate-800/80 animate-pulse"
    >
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="px-6 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="h-4 w-24 bg-slate-800 rounded"></div>
            <div className="h-4 w-20 bg-slate-800/70 rounded"></div>
          </div>
          <div className="h-4 w-20 bg-slate-800 rounded"></div>
          <div className="h-4 w-24 bg-slate-800/70 rounded"></div>
          <div className="h-4 w-12 bg-slate-800 rounded"></div>
          <div className="h-6 w-20 bg-slate-800 rounded-full"></div>
          <div className="h-6 w-24 bg-slate-800 rounded-full"></div>
          <div className="h-4 w-16 bg-slate-800/60 rounded"></div>
        </div>
      ))}
    </div>
  );
};
