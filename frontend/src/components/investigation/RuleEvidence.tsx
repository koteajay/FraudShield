import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Terminal } from 'lucide-react';

interface RuleEvidenceProps {
  evidence?: Record<string, unknown> | null;
}

/**
 * Converts a snake_case or camelCase key into Title Case label.
 */
function formatKey(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/\b\w/g, (str) => str.toUpperCase());
}

/**
 * Formats evidence values safely into readable strings.
 */
function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '—';
  }
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No';
  }
  if (typeof value === 'number') {
    // If it's a ratio or multiplier
    return Number.isInteger(value) ? value.toLocaleString() : value.toFixed(2);
  }
  if (typeof value === 'string') {
    return value;
  }
  if (Array.isArray(value)) {
    if (value.length === 0) return 'None';
    return value.map((item) => (typeof item === 'object' ? JSON.stringify(item) : String(item))).join(', ');
  }
  if (typeof value === 'object') {
    return JSON.stringify(value);
  }
  return String(value);
}

export const RuleEvidence: React.FC<RuleEvidenceProps> = ({ evidence }) => {
  const [showRaw, setShowRaw] = useState<boolean>(false);

  if (!evidence || Object.keys(evidence).length === 0) {
    return (
      <div className="text-xs text-slate-500 italic py-1">
        No specific telemetry evidence captured for this rule.
      </div>
    );
  }

  const entries = Object.entries(evidence);

  return (
    <div className="space-y-3">
      {/* Human-readable key-value grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
        {entries.map(([key, val]) => {
          // If value is an object or array of objects, handle specially
          const isComplex = typeof val === 'object' && val !== null;
          return (
            <div key={key} className="flex flex-col bg-slate-900/60 p-2 rounded border border-slate-800/50">
              <span className="text-[10px] font-medium text-slate-400 uppercase tracking-wider">
                {formatKey(key)}
              </span>
              <span className="text-xs font-mono font-semibold text-slate-200 mt-0.5 break-words">
                {isComplex ? (
                  <pre className="text-[11px] font-mono text-slate-300 whitespace-pre-wrap">
                    {formatValue(val)}
                  </pre>
                ) : (
                  formatValue(val)
                )}
              </span>
            </div>
          );
        })}
      </div>

      {/* Technical details toggle */}
      <div>
        <button
          type="button"
          onClick={() => setShowRaw((prev) => !prev)}
          className="inline-flex items-center gap-1.5 text-[11px] text-slate-500 hover:text-slate-300 font-mono transition-colors"
        >
          <Terminal className="w-3 h-3 text-slate-500" />
          <span>Technical details (Raw JSON)</span>
          {showRaw ? (
            <ChevronDown className="w-3 h-3" />
          ) : (
            <ChevronRight className="w-3 h-3" />
          )}
        </button>

        {showRaw && (
          <pre className="mt-2 p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-[11px] font-mono text-emerald-400/90 overflow-x-auto">
            {JSON.stringify(evidence, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
};
