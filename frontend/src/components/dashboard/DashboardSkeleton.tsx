import React from 'react';

export const DashboardSkeleton: React.FC = () => {
  return (
    <div
      role="status"
      aria-label="Loading dashboard statistics"
      className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-3.5"
    >
      {Array.from({ length: 7 }).map((_, index) => (
        <div
          key={index}
          className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-4 animate-pulse space-y-3"
        >
          <div className="flex items-center justify-between">
            <div className="h-3 w-16 bg-slate-800 rounded"></div>
            <div className="h-7 w-7 bg-slate-800 rounded-lg"></div>
          </div>
          <div className="h-7 w-14 bg-slate-800 rounded"></div>
          <div className="h-2 w-20 bg-slate-800/60 rounded"></div>
        </div>
      ))}
    </div>
  );
};
