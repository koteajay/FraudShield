import React from 'react';
import { Laptop, AlertTriangle, ShieldCheck, Globe, Cpu, Network, Clock } from 'lucide-react';
import { formatTimestamp } from '../../utils/formatters';

interface DeviceData {
  device_id?: string;
  browser?: string;
  operating_system?: string;
  ip_address?: string;
  is_trusted?: boolean;
  is_new?: boolean;
  first_seen_at?: string;
  last_seen_at?: string;
}

interface DeviceInformationCardProps {
  device?: DeviceData | null;
}

export const DeviceInformationCard: React.FC<DeviceInformationCardProps> = ({ device }) => {
  if (!device || (!device.device_id && !device.browser && !device.operating_system)) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
        <div className="flex items-center gap-2 mb-2">
          <Laptop className="w-5 h-5 text-slate-500" />
          <h3 className="text-base font-bold text-white tracking-tight">Device Information</h3>
        </div>
        <p className="text-xs text-slate-400 italic">
          No hardware or client device telemetry was captured with this transaction.
        </p>
      </div>
    );
  }

  const isNewDevice = device.is_new === true;

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 backdrop-blur-md shadow-xl space-y-4">
      {/* Card Header with Status Badge */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <Laptop className="w-5 h-5 text-blue-400" />
          <h3 className="text-base font-bold text-white tracking-tight">
            Device Information
          </h3>
        </div>

        <div>
          {isNewDevice ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold tracking-wide bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>NEW DEVICE ⚠️</span>
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold tracking-wide bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>KNOWN DEVICE</span>
            </span>
          )}
        </div>
      </div>

      {/* Grid of Device Attributes */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
        {/* Device ID */}
        <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800">
          <span className="text-[10px] font-medium text-slate-400 uppercase tracking-wider block">
            Device Identifier
          </span>
          <span className="text-xs font-mono font-bold text-white mt-1 block truncate" title={device.device_id}>
            {device.device_id || 'Unknown ID'}
          </span>
        </div>

        {/* Browser & OS */}
        <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800">
          <span className="text-[10px] font-medium text-slate-400 uppercase tracking-wider block">
            Client Environment
          </span>
          <div className="flex items-center gap-2 mt-1 text-xs text-slate-200">
            <Globe className="w-3.5 h-3.5 text-blue-400 shrink-0" />
            <span className="font-semibold">{device.browser || 'Unknown Browser'}</span>
            <span className="text-slate-600">/</span>
            <Cpu className="w-3.5 h-3.5 text-purple-400 shrink-0" />
            <span className="font-semibold">{device.operating_system || 'Unknown OS'}</span>
          </div>
        </div>

        {/* IP Address */}
        <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800">
          <span className="text-[10px] font-medium text-slate-400 uppercase tracking-wider block">
            Network IP Address
          </span>
          <div className="flex items-center gap-2 mt-1 text-xs font-mono text-slate-300">
            <Network className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span>{device.ip_address || 'Not Recorded'}</span>
          </div>
        </div>

        {/* First Seen */}
        <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800">
          <span className="text-[10px] font-medium text-slate-400 uppercase tracking-wider block">
            First Seen
          </span>
          <div className="flex items-center gap-1.5 mt-1 text-xs font-mono text-slate-300">
            <Clock className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <span>{device.first_seen_at ? formatTimestamp(device.first_seen_at) : 'First detected today'}</span>
          </div>
        </div>

        {/* Last Seen */}
        <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800">
          <span className="text-[10px] font-medium text-slate-400 uppercase tracking-wider block">
            Last Seen
          </span>
          <div className="flex items-center gap-1.5 mt-1 text-xs font-mono text-slate-300">
            <Clock className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <span>{device.last_seen_at ? formatTimestamp(device.last_seen_at) : 'Current session'}</span>
          </div>
        </div>

        {/* Trust State */}
        <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800">
          <span className="text-[10px] font-medium text-slate-400 uppercase tracking-wider block">
            Trust Classification
          </span>
          <span className="text-xs font-semibold text-slate-300 mt-1 block">
            {device.is_trusted ? 'Verified by User' : 'Unconfirmed / New Device'}
          </span>
        </div>
      </div>
    </div>
  );
};
