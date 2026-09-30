import React from 'react';
import type { DashboardStats } from '../../types/dashboard';
import { StatCard } from './StatCard';
import {
  CreditCard,
  ShieldAlert,
  AlertTriangle,
  Flame,
  Clock,
  CheckCircle2,
} from 'lucide-react';

export interface DashboardStatsGridProps {
  stats: DashboardStats;
  isLoading?: boolean;
}

export const DashboardStatsGrid: React.FC<DashboardStatsGridProps> = ({
  stats,
  isLoading = false,
}) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 animate-pulse">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="h-32 bg-slate-900/60 rounded-2xl border border-slate-800/80 p-5"
          />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {/* 1. Total Transactions */}
      <StatCard
        label="Total Transactions"
        value={stats.totalTransactions}
        icon={<CreditCard className="w-5 h-5" />}
        variant="default"
        description="Ingested volume"
      />

      {/* 2. Flagged Transactions */}
      <StatCard
        label="Flagged"
        value={stats.flaggedTransactions}
        icon={<ShieldAlert className="w-5 h-5" />}
        variant="high"
        description="Rules triggered"
      />

      {/* 3. High Risk */}
      <StatCard
        label="High Risk"
        value={stats.highRisk}
        icon={<AlertTriangle className="w-5 h-5" />}
        variant="high"
        description="Score >= 60"
      />

      {/* 4. Critical */}
      <StatCard
        label="Critical"
        value={stats.critical}
        icon={<Flame className="w-5 h-5" />}
        variant="critical"
        description="Score >= 80"
      />

      {/* 5. Pending Review */}
      <StatCard
        label="Pending Review"
        value={stats.pendingReview}
        icon={<Clock className="w-5 h-5" />}
        variant="warning"
        description="Awaiting action"
      />

      {/* 6. Cleared */}
      <StatCard
        label="Cleared"
        value={stats.cleared}
        icon={<CheckCircle2 className="w-5 h-5" />}
        variant="success"
        description="Verified safe"
      />
    </div>
  );
};

export default DashboardStatsGrid;
