import React from 'react';
import {
  UserCheck,
  TrendingUp,
  Clock,
  MapPin,
  Laptop,
  Store,
  ShieldAlert,
  Calendar,
  AlertTriangle,
  RotateCw,
} from 'lucide-react';
import { formatCurrency } from '../../utils/formatters';
import type { UserBehaviourProfile } from '../../types/profile';
import type { TransactionDetail } from '../../types/transaction';

interface BehaviourProfileCardProps {
  profile: UserBehaviourProfile | null;
  transaction: TransactionDetail;
  isLoading: boolean;
  error?: string | null;
  onRetry?: () => void;
}

export const BehaviourProfileCard: React.FC<BehaviourProfileCardProps> = ({
  profile,
  transaction,
  isLoading,
  error,
  onRetry,
}) => {
  if (isLoading) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 animate-pulse">
        <div className="h-5 w-48 bg-slate-800 rounded mb-4" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="h-16 bg-slate-800/60 rounded-xl" />
          <div className="h-16 bg-slate-800/60 rounded-xl" />
          <div className="h-16 bg-slate-800/60 rounded-xl" />
          <div className="h-16 bg-slate-800/60 rounded-xl" />
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-300">User Behaviour Profile</h3>
          <p className="text-xs text-slate-400 mt-1">
            {error || 'Behavioural profile not available for this user.'}
          </p>
        </div>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 transition-colors w-fit"
          >
            <RotateCw className="w-3.5 h-3.5" />
            <span>Retry Profile</span>
          </button>
        )}
      </div>
    );
  }

  // Profile Status styling
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ESTABLISHED':
        return 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
      case 'DEVELOPING':
        return 'bg-blue-500/15 text-blue-300 border-blue-500/30';
      case 'INSUFFICIENT_DATA':
      default:
        return 'bg-amber-500/15 text-amber-300 border-amber-500/30';
    }
  };

  // Safe checks for comparisons
  const avgAmount = profile.average_transaction_amount ?? 0;
  const currentAmount = transaction.amount;
  const amountRatio = avgAmount > 0 ? (currentAmount / avgAmount) : 0;
  const isHighAmountDeviation = amountRatio >= 3.0;

  // Location check
  const txLocation = (transaction.city || transaction.location || '').toLowerCase();
  const isKnownLocation =
    txLocation === '' ||
    profile.known_locations.some((loc) => loc.toLowerCase().includes(txLocation) || txLocation.includes(loc.toLowerCase()));

  // Time window check
  const normalHours = profile.normal_transaction_hours;
  const normalHoursLabel = normalHours
    ? `${String(normalHours.start_hour).padStart(2, '0')}:00 – ${String(normalHours.end_hour).padStart(2, '0')}:00`
    : 'Not established';

  let isOutsideNormalHours = false;
  if (normalHours && transaction.timestamp) {
    try {
      const txHour = new Date(transaction.timestamp).getHours();
      if (normalHours.start_hour <= normalHours.end_hour) {
        isOutsideNormalHours = txHour < normalHours.start_hour || txHour > normalHours.end_hour;
      } else {
        // Overnight window
        isOutsideNormalHours = txHour < normalHours.start_hour && txHour > normalHours.end_hour;
      }
    } catch {
      // Ignore date parsing failure
    }
  }

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 backdrop-blur-md shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <UserCheck className="w-5 h-5 text-blue-400" />
          <h3 className="text-base font-bold text-white tracking-tight">
            User Behaviour Profile
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Profile Status:</span>
          <span
            className={`px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide border ${getStatusBadge(
              profile.profile_status
            )}`}
          >
            {profile.profile_status}
          </span>
        </div>
      </div>

      {/* Comparisons & Anomaly Highlights */}
      {(isHighAmountDeviation || !isKnownLocation || isOutsideNormalHours) && (
        <div className="p-3.5 rounded-xl bg-amber-950/20 border border-amber-500/30 text-xs text-amber-200/90 space-y-2">
          <div className="flex items-center gap-1.5 font-semibold text-amber-300">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <span>Observed Deviations from Baseline</span>
          </div>
          <div className="flex flex-wrap gap-2 pt-1">
            {isHighAmountDeviation && (
              <span className="px-2.5 py-1 rounded-md bg-amber-500/20 border border-amber-500/40 text-[11px] font-mono font-medium text-amber-200">
                Amount is {amountRatio.toFixed(1)}× user average ({formatCurrency(currentAmount, transaction.currency)} vs avg {formatCurrency(avgAmount, transaction.currency)})
              </span>
            )}
            {!isKnownLocation && txLocation && (
              <span className="px-2.5 py-1 rounded-md bg-amber-500/20 border border-amber-500/40 text-[11px] font-mono font-medium text-amber-200">
                Unrecognized location: &ldquo;{transaction.location || transaction.city}&rdquo;
              </span>
            )}
            {isOutsideNormalHours && (
              <span className="px-2.5 py-1 rounded-md bg-amber-500/20 border border-amber-500/40 text-[11px] font-mono font-medium text-amber-200">
                Transaction time is outside established activity window ({normalHoursLabel})
              </span>
            )}
          </div>
        </div>
      )}

      {/* Profile Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Avg Amount & Range */}
        <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
          <div className="flex items-center justify-between text-slate-400 mb-1.5">
            <span className="text-[11px] uppercase tracking-wider font-medium">Avg Transaction</span>
            <TrendingUp className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-xl font-bold font-mono text-white">
            {avgAmount > 0 ? formatCurrency(avgAmount, transaction.currency) : '—'}
          </div>
          <div className="text-[11px] text-slate-400 font-mono mt-1">
            Normal: {profile.normal_amount_range
              ? `${formatCurrency(profile.normal_amount_range.min, transaction.currency)} – ${formatCurrency(profile.normal_amount_range.max, transaction.currency)}`
              : '—'}
          </div>
        </div>

        {/* Metric 2: Frequency */}
        <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
          <div className="flex items-center justify-between text-slate-400 mb-1.5">
            <span className="text-[11px] uppercase tracking-wider font-medium">Activity Frequency</span>
            <Calendar className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xl font-bold font-mono text-white">
            {profile.average_transactions_per_day?.toFixed(1) ?? '—'}{' '}
            <span className="text-xs font-normal text-slate-400">/ day</span>
          </div>
          <div className="text-[11px] text-slate-400 font-mono mt-1">
            {profile.profile_transaction_count} txns across {profile.total_active_days || profile.profile_period_days} days
          </div>
        </div>

        {/* Metric 3: Normal Hours */}
        <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
          <div className="flex items-center justify-between text-slate-400 mb-1.5">
            <span className="text-[11px] uppercase tracking-wider font-medium">Normal Hours</span>
            <Clock className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-lg font-bold font-mono text-white">
            {normalHoursLabel}
          </div>
          <div className="text-[11px] text-slate-400 font-mono mt-1">
            Historical active window
          </div>
        </div>

        {/* Metric 4: Failed Logins */}
        <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
          <div className="flex items-center justify-between text-slate-400 mb-1.5">
            <span className="text-[11px] uppercase tracking-wider font-medium">Failed Logins</span>
            <ShieldAlert className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-xl font-bold font-mono text-white">
            {profile.failed_login_count ?? 0}
          </div>
          <div className="text-[11px] text-slate-400 font-mono mt-1">
            Recent: {profile.recent_failed_login_count ?? 0}
          </div>
        </div>
      </div>

      {/* Baseline Inventory Chips */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
        {/* Known Locations */}
        <div className="bg-slate-950/40 p-3.5 rounded-xl border border-slate-800/60">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-300 mb-2">
            <MapPin className="w-3.5 h-3.5 text-blue-400" />
            <span>Known Locations ({profile.known_locations?.length ?? 0})</span>
          </div>
          {profile.known_locations && profile.known_locations.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {profile.known_locations.map((loc) => (
                <span
                  key={loc}
                  className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-xs font-mono"
                >
                  {loc}
                </span>
              ))}
            </div>
          ) : (
            <span className="text-xs text-slate-500 italic">None recorded</span>
          )}
        </div>

        {/* Known Devices */}
        <div className="bg-slate-950/40 p-3.5 rounded-xl border border-slate-800/60">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-300 mb-2">
            <Laptop className="w-3.5 h-3.5 text-emerald-400" />
            <span>Known Devices ({profile.known_devices ?? profile.known_device_ids?.length ?? 0})</span>
          </div>
          {profile.known_device_ids && profile.known_device_ids.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {profile.known_device_ids.map((dev) => (
                <span
                  key={dev}
                  className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-xs font-mono truncate max-w-[140px]"
                  title={dev}
                >
                  {dev}
                </span>
              ))}
            </div>
          ) : (
            <span className="text-xs text-slate-500 italic">None recorded</span>
          )}
        </div>

        {/* Known Merchants */}
        <div className="bg-slate-950/40 p-3.5 rounded-xl border border-slate-800/60">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-300 mb-2">
            <Store className="w-3.5 h-3.5 text-purple-400" />
            <span>Known Merchants ({profile.known_merchants?.length ?? 0})</span>
          </div>
          {profile.known_merchants && profile.known_merchants.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {profile.known_merchants.slice(0, 6).map((m) => (
                <span
                  key={m}
                  className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-xs font-mono truncate max-w-[130px]"
                  title={m}
                >
                  {m}
                </span>
              ))}
              {profile.known_merchants.length > 6 && (
                <span className="px-1.5 py-0.5 text-xs text-slate-500">
                  +{profile.known_merchants.length - 6} more
                </span>
              )}
            </div>
          ) : (
            <span className="text-xs text-slate-500 italic">None recorded</span>
          )}
        </div>
      </div>
    </div>
  );
};
