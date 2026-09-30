import React from 'react';
import {
  Layers,
  Flag,
  AlertTriangle,
  Flame,
  Clock,
  CheckCircle,
  ShieldCheck,
} from 'lucide-react';
import { StatCard } from './StatCard';
import { DashboardSkeleton } from './DashboardSkeleton';
import { ErrorState } from '../common/ErrorState';
import type { DashboardStats } from '../../types/dashboard';

interface DashboardProps {
  stats: DashboardStats | null;
  isLoading: boolean;
  error: string | null;
  onRetry: () => void;
  onFilterSelect?: (filter: { risk_level?: string; status?: string }) => void;
  activeFilter?: { risk_level?: string; status?: string };
}

export const Dashboard: React.FC<DashboardProps> = ({
  stats,
  isLoading,
  error,
  onRetry,
  onFilterSelect,
  activeFilter,
}) => {
  if (isLoading && !stats) {
    return <DashboardSkeleton />;
  }

  if (error && !stats) {
    return (
      <ErrorState
        title="Unable to load dashboard statistics"
        message={error}
        onRetry={onRetry}
      />
    );
  }

  if (!stats) {
    return null;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold tracking-wide text-slate-300 uppercase">
          Reviewer KPIs &amp; Operational Queues
        </h2>
        {stats.average_risk_score > 0 && (
          <span className="text-xs font-mono px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-slate-400">
            Avg Risk Score:{' '}
            <strong className="text-slate-200">{stats.average_risk_score.toFixed(1)}</strong>
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-3">
        {/* 1. Total Transactions */}
        <StatCard
          title="Total"
          value={stats.total_transactions}
          description="Monitored volume"
          icon={Layers}
          variant="default"
          onClick={() => onFilterSelect?.({})}
          className={
            !activeFilter?.risk_level && !activeFilter?.status
              ? 'ring-2 ring-blue-500/50'
              : ''
          }
        />

        {/* 2. Flagged */}
        <StatCard
          title="Flagged"
          value={stats.flagged}
          description="Triggered heuristics"
          icon={Flag}
          variant="warning"
          onClick={() => onFilterSelect?.({ status: 'FLAGGED' })}
          className={activeFilter?.status === 'FLAGGED' ? 'ring-2 ring-amber-500/50' : ''}
        />

        {/* 3. High Risk */}
        <StatCard
          title="High Risk"
          value={stats.high_risk_transactions}
          description="Score 60 - 79"
          icon={AlertTriangle}
          variant="danger"
          onClick={() => onFilterSelect?.({ risk_level: 'HIGH' })}
          className={activeFilter?.risk_level === 'HIGH' ? 'ring-2 ring-orange-500/50' : ''}
        />

        {/* 4. Critical */}
        <StatCard
          title="Critical"
          value={stats.critical_risk_transactions}
          description="Score 80 - 100"
          icon={Flame}
          variant="critical"
          onClick={() => onFilterSelect?.({ risk_level: 'CRITICAL' })}
          className={activeFilter?.risk_level === 'CRITICAL' ? 'ring-2 ring-rose-500/50' : ''}
        />

        {/* 5. Pending Review */}
        <StatCard
          title="Pending"
          value={stats.pending_review}
          description="Queue backlog"
          icon={Clock}
          variant="info"
          onClick={() => onFilterSelect?.({ status: 'PENDING_REVIEW' })}
          className={
            activeFilter?.status === 'PENDING_REVIEW' ? 'ring-2 ring-blue-500/50' : ''
          }
        />

        {/* 6. Reviewed */}
        <StatCard
          title="Reviewed"
          value={stats.reviewed_transactions}
          description="Audited items"
          icon={CheckCircle}
          variant="purple"
          onClick={() => onFilterSelect?.({ status: 'REVIEWED' })}
          className={activeFilter?.status === 'REVIEWED' ? 'ring-2 ring-purple-500/50' : ''}
        />

        {/* 7. Cleared */}
        <StatCard
          title="Cleared"
          value={stats.cleared_transactions}
          description="Resolved benign"
          icon={ShieldCheck}
          variant="success"
          onClick={() => onFilterSelect?.({ status: 'CLEARED' })}
          className={activeFilter?.status === 'CLEARED' ? 'ring-2 ring-emerald-500/50' : ''}
        />
      </div>
    </div>
  );
};
