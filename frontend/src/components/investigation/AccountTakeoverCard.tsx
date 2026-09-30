import React from 'react';
import { UserX, ShieldAlert, CheckCircle2, Circle } from 'lucide-react';
import { RiskBadge } from '../transactions/RiskBadge';
import type { AccountTakeoverDetail } from '../../types/transaction';

interface AccountTakeoverCardProps {
  ato?: AccountTakeoverDetail | null;
}

export const AccountTakeoverCard: React.FC<AccountTakeoverCardProps> = ({ ato }) => {
  if (!ato) {
    return null;
  }

  // Pre-defined canonical signals
  const knownSignals = [
    { key: 'new_device', label: 'New Device Detected' },
    { key: 'unusual_time', label: 'Unusual Transaction Time' },
    { key: 'new_location', label: 'Unrecognized Location' },
    { key: 'failed_login', label: 'Recent Failed Login Activity' },
    { key: 'unusual_amount', label: 'Significant Amount Surge' },
  ];

  const signalsMap = ato.signals || {};

  return (
    <div
      className={`rounded-2xl border p-6 backdrop-blur-md shadow-xl space-y-4 ${
        ato.is_at_risk
          ? 'border-rose-500/40 bg-gradient-to-br from-rose-950/20 via-slate-900/70 to-slate-900/60 shadow-rose-950/30'
          : 'border-slate-800 bg-slate-900/60'
      }`}
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <UserX className={`w-5 h-5 ${ato.is_at_risk ? 'text-rose-400' : 'text-slate-400'}`} />
          <div>
            <h3 className="text-base font-bold text-white tracking-tight">
              Account Takeover (ATO) Assessment
            </h3>
            <p className="text-xs text-slate-400">
              Cross-telemetry correlation across device, authentication, and behavioural patterns.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <RiskBadge level={ato.risk_level || (ato.is_at_risk ? 'HIGH' : 'LOW')} />
          {ato.signal_count > 0 && (
            <span className="text-xs font-mono font-bold text-rose-300 bg-rose-950/40 border border-rose-500/30 px-2 py-0.5 rounded-full">
              {ato.signal_count} {ato.signal_count === 1 ? 'signal' : 'signals'}
            </span>
          )}
        </div>
      </div>

      {/* Explanation banner */}
      {ato.explanation && (
        <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 text-xs text-slate-300 leading-relaxed flex items-start gap-2.5">
          <ShieldAlert className={`w-4 h-4 shrink-0 mt-0.5 ${ato.is_at_risk ? 'text-rose-400' : 'text-slate-400'}`} />
          <span>{ato.explanation}</span>
        </div>
      )}

      {/* Signals Checklist */}
      <div>
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">
          Observed ATO Correlation Signals:
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
          {knownSignals.map(({ key, label }) => {
            const isTriggered = Boolean(signalsMap[key]);
            return (
              <div
                key={key}
                className={`flex items-center gap-2.5 p-2.5 rounded-lg border text-xs transition-colors ${
                  isTriggered
                    ? 'border-rose-500/40 bg-rose-950/30 text-rose-200 font-semibold'
                    : 'border-slate-800/80 bg-slate-950/40 text-slate-400 font-normal'
                }`}
              >
                {isTriggered ? (
                  <CheckCircle2 className="w-4 h-4 text-rose-400 shrink-0" />
                ) : (
                  <Circle className="w-4 h-4 text-slate-600 shrink-0" />
                )}
                <span>{label}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
