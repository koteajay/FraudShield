import React, { useState, useEffect } from 'react';
import { fetchTransactionJourney } from '../../services/journeyService';
import type { TransactionJourneyResponse } from './journey.types';
import { JourneyEventItem } from './JourneyEventItem';
import {
  Compass,
  Search,
  AlertTriangle,
  MapPin,
  Laptop,
  Activity,
  Calendar,
  RefreshCw,
} from 'lucide-react';

interface TransactionJourneyProps {
  initialTransactionId?: string;
}

export const TransactionJourney: React.FC<TransactionJourneyProps> = ({ initialTransactionId = '' }) => {
  const [transactionId, setTransactionId] = useState<string>(initialTransactionId);
  const [beforeMinutes, setBeforeMinutes] = useState<number>(30);
  const [afterMinutes, setAfterMinutes] = useState<number>(30);
  const [journeyData, setJourneyData] = useState<TransactionJourneyResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const loadJourney = async (idToFetch: string) => {
    const trimmed = idToFetch.trim();
    if (!trimmed) {
      setError('Please provide a valid Transaction ID.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const data = await fetchTransactionJourney(trimmed, beforeMinutes, afterMinutes);
      setJourneyData(data);
    } catch (err: unknown) {
      setJourneyData(null);
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to fetch transaction journey.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadJourney(transactionId);
  };

  useEffect(() => {
    if (initialTransactionId) {
      setTransactionId(initialTransactionId);
      loadJourney(initialTransactionId);
    }
  }, [initialTransactionId]);

  return (
    <div className="w-full bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs font-semibold mb-2">
            <Compass className="w-3.5 h-3.5" />
            Phase 8 Feature
          </div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            Chronological Transaction Journey
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Aggregates transactions, authentication attempts, device lifecycle markers, and triggered fraud rules around the selected transaction.
          </p>
        </div>

        {/* Time Window Config */}
        <div className="flex items-center gap-3 bg-slate-950/60 border border-slate-800 px-3 py-2 rounded-xl text-xs">
          <Calendar className="w-4 h-4 text-slate-400" />
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">Window:</span>
            <input
              type="number"
              min="0"
              max="1440"
              value={beforeMinutes}
              onChange={(e) => setBeforeMinutes(Math.max(0, parseInt(e.target.value) || 0))}
              className="w-12 bg-slate-900 border border-slate-700 rounded px-1.5 py-0.5 text-center text-slate-200 font-mono focus:outline-none focus:border-blue-500"
              title="Minutes before transaction"
            />
            <span className="text-slate-500">m before /</span>
            <input
              type="number"
              min="0"
              max="1440"
              value={afterMinutes}
              onChange={(e) => setAfterMinutes(Math.max(0, parseInt(e.target.value) || 0))}
              className="w-12 bg-slate-900 border border-slate-700 rounded px-1.5 py-0.5 text-center text-slate-200 font-mono focus:outline-none focus:border-blue-500"
              title="Minutes after transaction"
            />
            <span className="text-slate-500">m after</span>
          </div>
        </div>
      </div>

      {/* Search Input Bar */}
      <form onSubmit={handleSearch} className="mt-6 flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Enter Transaction ID or Reference (e.g. TXN-1001 or UUID)..."
            value={transactionId}
            onChange={(e) => setTransactionId(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors font-mono"
          />
        </div>
        <button
          type="submit"
          disabled={isLoading}
          className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition-colors shadow-lg shadow-blue-600/20 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
          Investigate Journey
        </button>
      </form>

      {/* Error Message */}
      {error && (
        <div className="mt-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-semibold text-red-400">Timeline Retrieval Notice</h4>
            <p className="text-xs text-red-300 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* Journey Content */}
      {journeyData && (
        <div className="mt-6 space-y-6">
          {/* Summary Stats Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-950/60 border border-slate-800 p-3.5 rounded-xl">
              <span className="text-slate-400 text-xs">Transactions</span>
              <p className="text-xl font-bold text-slate-100 mt-1 font-mono">
                {journeyData.summary.transaction_count}
              </p>
            </div>
            <div className="bg-slate-950/60 border border-slate-800 p-3.5 rounded-xl">
              <span className="text-slate-400 text-xs">Login Attempts</span>
              <p className="text-xl font-bold text-amber-400 mt-1 font-mono">
                {journeyData.summary.login_attempt_count}
              </p>
            </div>
            <div className="bg-slate-950/60 border border-slate-800 p-3.5 rounded-xl">
              <span className="text-slate-400 text-xs">Triggered Rules</span>
              <p className="text-xl font-bold text-rose-400 mt-1 font-mono">
                {journeyData.summary.rule_trigger_count}
              </p>
            </div>
            <div className="bg-slate-950/60 border border-slate-800 p-3.5 rounded-xl">
              <span className="text-slate-400 text-xs">Risk Events</span>
              <p className="text-xl font-bold text-red-400 mt-1 font-mono">
                {journeyData.summary.risk_event_count}
              </p>
            </div>
          </div>

          {/* New Device Alert Banner */}
          {journeyData.summary.new_device_detected && (
            <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-between text-xs text-amber-300">
              <span className="flex items-center gap-2 font-medium">
                <Laptop className="w-4 h-4 text-amber-400" />
                New client device detected in this investigation window.
              </span>
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
                Threat Signal
              </span>
            </div>
          )}

          {/* Locations & Devices Tags */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-xl bg-slate-950/40 border border-slate-800 text-xs text-slate-400">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold text-slate-300 flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-emerald-400" /> Locations:
              </span>
              {journeyData.summary.locations.length > 0 ? (
                journeyData.summary.locations.map((loc, idx) => (
                  <span key={idx} className="bg-slate-900 border border-slate-800 px-2 py-0.5 rounded text-slate-200">
                    {loc}
                  </span>
                ))
              ) : (
                <span className="text-slate-500">None recorded</span>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold text-slate-300 flex items-center gap-1">
                <Laptop className="w-3.5 h-3.5 text-purple-400" /> Devices:
              </span>
              {journeyData.summary.devices.length > 0 ? (
                journeyData.summary.devices.map((dev, idx) => (
                  <span key={idx} className="bg-slate-900 border border-slate-800 px-2 py-0.5 rounded font-mono text-slate-200">
                    {dev}
                  </span>
                ))
              ) : (
                <span className="text-slate-500">None recorded</span>
              )}
            </div>
          </div>

          {/* Vertical Timeline */}
          <div className="pt-4">
            <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-400" />
              Chronological Activity Timeline ({journeyData.events.length} events)
            </h3>

            {journeyData.events.length === 0 ? (
              <div className="text-center py-8 text-xs text-slate-500 bg-slate-950/30 rounded-xl border border-slate-800/60">
                No activity recorded in the specified time window.
              </div>
            ) : (
              <div className="space-y-0">
                {journeyData.events.map((evt, idx) => (
                  <JourneyEventItem
                    key={evt.event_id || idx}
                    event={evt}
                    isLast={idx === journeyData.events.length - 1}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Initial Empty State Instruction */}
      {!journeyData && !error && !isLoading && (
        <div className="mt-8 text-center py-10 px-4 rounded-xl border border-dashed border-slate-800 bg-slate-950/20">
          <Compass className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <h4 className="text-sm font-medium text-slate-300">Transaction Journey Aggregation</h4>
          <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
            Provide a Transaction ID above to examine the user's journey timeline, including device switches, geo-displacements, login failures, and triggered fraud rules.
          </p>
        </div>
      )}
    </div>
  );
};
