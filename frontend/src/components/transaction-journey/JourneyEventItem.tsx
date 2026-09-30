import React, { useState } from 'react';
import type { JourneyEvent } from './journey.types';
import {
  CreditCard,
  LogIn,
  AlertTriangle,
  Laptop,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  MapPin,
  Clock,
  Zap,
} from 'lucide-react';

interface JourneyEventItemProps {
  event: JourneyEvent;
  isLast: boolean;
}

export const JourneyEventItem: React.FC<JourneyEventItemProps> = ({ event, isLast }) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);

  // Format timestamp (e.g. "10:21:45" or "10:21")
  const dateObj = new Date(event.timestamp);
  const timeFormatted = isNaN(dateObj.getTime())
    ? event.timestamp
    : dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  // Node styling and icon based on event type & severity
  const getIconAndColors = () => {
    switch (event.event_type) {
      case 'TRANSACTION':
        if (event.severity === 'CRITICAL' || event.severity === 'HIGH') {
          return {
            icon: <AlertTriangle className="w-4 h-4 text-red-400" />,
            border: 'border-red-500/30',
            bg: 'bg-red-500/10',
            nodeBg: 'bg-red-500',
            nodeRing: 'ring-red-400/40',
          };
        }
        return {
          icon: <CreditCard className="w-4 h-4 text-blue-400" />,
          border: 'border-blue-500/20',
          bg: 'bg-blue-500/5',
          nodeBg: 'bg-blue-500',
          nodeRing: 'ring-blue-400/30',
        };

      case 'LOGIN_ATTEMPT':
        const isSuccess = event.metadata?.is_successful !== false;
        if (!isSuccess) {
          return {
            icon: <LogIn className="w-4 h-4 text-amber-400" />,
            border: 'border-amber-500/30',
            bg: 'bg-amber-500/10',
            nodeBg: 'bg-amber-500',
            nodeRing: 'ring-amber-400/40',
          };
        }
        return {
          icon: <LogIn className="w-4 h-4 text-emerald-400" />,
          border: 'border-emerald-500/20',
          bg: 'bg-emerald-500/5',
          nodeBg: 'bg-emerald-500',
          nodeRing: 'ring-emerald-400/30',
        };

      case 'DEVICE_EVENT':
        return {
          icon: <Laptop className="w-4 h-4 text-purple-400" />,
          border: 'border-purple-500/30',
          bg: 'bg-purple-500/10',
          nodeBg: 'bg-purple-500',
          nodeRing: 'ring-purple-400/40',
        };

      case 'RULE_TRIGGER':
        return {
          icon: <Zap className="w-4 h-4 text-rose-400" />,
          border: 'border-rose-500/30',
          bg: 'bg-rose-500/10',
          nodeBg: 'bg-rose-500',
          nodeRing: 'ring-rose-400/40',
        };

      case 'RISK_EVENT':
      default:
        return {
          icon: <ShieldAlert className="w-4 h-4 text-red-400" />,
          border: 'border-red-500/40',
          bg: 'bg-red-500/10',
          nodeBg: 'bg-red-500',
          nodeRing: 'ring-red-400/50',
        };
    }
  };

  const { icon, border, bg, nodeRing } = getIconAndColors();

  // Severity pill style
  const getSeverityBadge = () => {
    switch (event.severity) {
      case 'CRITICAL':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'HIGH':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'MEDIUM':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'LOW':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'INFO':
      default:
        return 'bg-slate-500/20 text-slate-300 border-slate-500/30';
    }
  };

  return (
    <div className="relative flex gap-4">
      {/* Vertical Connecting Line */}
      {!isLast && (
        <div className="absolute left-[15px] top-8 bottom-0 w-[2px] bg-slate-800" />
      )}

      {/* Node Dot with Glow Ring */}
      <div className="relative z-10 flex items-center justify-center flex-shrink-0 mt-1">
        <div className={`w-8 h-8 rounded-full flex items-center justify-center bg-slate-900 border border-slate-700 ring-4 ${nodeRing} shadow-md`}>
          {icon}
        </div>
      </div>

      {/* Event Content Card */}
      <div className={`flex-1 rounded-xl p-4 mb-4 border ${border} ${bg} backdrop-blur-sm transition-all hover:border-slate-600`}>
        <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1 text-xs font-mono font-medium text-slate-400">
              <Clock className="w-3 h-3" />
              {timeFormatted}
            </span>
            <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full border ${getSeverityBadge()}`}>
              {event.severity}
            </span>
            {event.metadata?.is_target_transaction && (
              <span className="text-[10px] font-semibold bg-blue-500/20 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded-full">
                Target Transaction
              </span>
            )}
          </div>

          {/* Amount / Risk Score Badge */}
          <div className="flex items-center gap-2">
            {event.amount !== undefined && event.amount !== null && (
              <span className="text-sm font-semibold text-slate-100 font-mono">
                {event.currency || '₹'} {event.amount.toLocaleString()}
              </span>
            )}
            {event.risk_score !== undefined && event.risk_score !== null && (
              <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                Score: <strong className="text-slate-100">{event.risk_score.toFixed(0)}</strong>
              </span>
            )}
          </div>
        </div>

        {/* Title & Description */}
        <h4 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
          {event.title}
        </h4>
        <p className="text-xs text-slate-300 mt-1 leading-relaxed">
          {event.description}
        </p>

        {/* Context Badges (Location, Device) */}
        <div className="flex flex-wrap items-center gap-2 mt-3 text-xs text-slate-400">
          {event.location && (
            <span className="inline-flex items-center gap-1 bg-slate-900/60 border border-slate-800 px-2.5 py-1 rounded-md">
              <MapPin className="w-3 h-3 text-emerald-400" />
              {event.location}
            </span>
          )}
          {event.device_id && (
            <span className="inline-flex items-center gap-1 bg-slate-900/60 border border-slate-800 px-2.5 py-1 rounded-md font-mono text-[11px]">
              <Laptop className="w-3 h-3 text-purple-400" />
              {event.device_id}
            </span>
          )}
          {event.rule_id && (
            <span className="inline-flex items-center gap-1 bg-rose-500/10 border border-rose-500/20 text-rose-300 px-2.5 py-1 rounded-md text-[11px]">
              <Zap className="w-3 h-3" />
              Rule: {event.rule_id}
            </span>
          )}
        </div>

        {/* Expandable Details Accordion */}
        {event.metadata && Object.keys(event.metadata).length > 0 && (
          <div className="mt-3 pt-2.5 border-t border-slate-800/80">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="inline-flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-200 transition-colors font-medium focus:outline-none"
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="w-3 h-3" /> Hide Reviewer Telemetry
                </>
              ) : (
                <>
                  <ChevronDown className="w-3 h-3" /> Show Reviewer Telemetry
                </>
              )}
            </button>

            {isExpanded && (
              <div className="mt-2.5 p-3 rounded-lg bg-slate-950/70 border border-slate-800/80 text-[11px] text-slate-300 font-mono overflow-x-auto">
                <pre className="whitespace-pre-wrap break-words">
                  {JSON.stringify(event.metadata, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
