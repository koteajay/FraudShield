import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import { ShieldCheck, LayoutDashboard, Compass, Server } from 'lucide-react';

export const Header: React.FC = () => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md px-4 sm:px-6 py-3.5 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <Link to="/dashboard" className="flex items-center space-x-3 group">
          <div className="p-2 rounded-xl bg-blue-600/20 border border-blue-500/30 text-blue-400 shadow-lg shadow-blue-500/10 group-hover:bg-blue-600/30 transition-colors">
            <ShieldCheck className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
              FraudShield
              <span className="text-[11px] px-2 py-0.5 rounded-full font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Phase 10
              </span>
            </h1>
            <p className="text-[11px] text-slate-400 font-medium">
              Reviewer Console &amp; Fraud Surveillance
            </p>
          </div>
        </Link>

        {/* Navigation tabs */}
        <nav className="flex items-center gap-1 sm:gap-2">
          <NavLink
            to="/dashboard"
            className={({ isActive }) =>
              `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                isActive
                  ? 'bg-blue-600/20 text-blue-300 border border-blue-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`
            }
          >
            <LayoutDashboard className="w-3.5 h-3.5" />
            <span>Dashboard</span>
          </NavLink>

          <NavLink
            to="/journey"
            className={({ isActive }) =>
              `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                isActive
                  ? 'bg-blue-600/20 text-blue-300 border border-blue-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`
            }
          >
            <Compass className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Transaction Journey</span>
            <span className="sm:hidden">Journey</span>
          </NavLink>

          <NavLink
            to="/system"
            className={({ isActive }) =>
              `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                isActive
                  ? 'bg-blue-600/20 text-blue-300 border border-blue-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`
            }
          >
            <Server className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">System Health</span>
            <span className="sm:hidden">Health</span>
          </NavLink>
        </nav>
      </div>
    </header>
  );
};
