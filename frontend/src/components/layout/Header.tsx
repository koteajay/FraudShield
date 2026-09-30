import React from 'react';
import { ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Header: React.FC = () => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md px-6 py-3.5 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <Link
          to="/"
          className="flex items-center space-x-3 group transition-opacity hover:opacity-90"
        >
          <div className="p-2 rounded-xl bg-blue-600/20 border border-blue-500/30 text-blue-400 shadow-lg shadow-blue-500/10">
            <ShieldCheck className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold tracking-tight text-white font-sans">
                FraudShield
              </span>
              <span className="text-[11px] px-2 py-0.5 rounded-full font-mono font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
                v0.1.0
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">
              Fraud Detection &amp; Investigation Platform
            </p>
          </div>
        </Link>

        <div className="flex items-center gap-4 text-xs text-slate-400">
          <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-lg bg-slate-950/60 border border-slate-800">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-slate-300 font-medium">Core API Layer Active</span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
