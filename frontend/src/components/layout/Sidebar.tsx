import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Activity,
  UserCheck,
  GitBranch,
  Flame,
  Radio,
} from 'lucide-react';

interface NavItem {
  name: string;
  to: string;
  icon: React.ReactNode;
  isAvailable: boolean;
  phaseTag?: string;
}

export const Sidebar: React.FC = () => {
  const navItems: NavItem[] = [
    {
      name: 'Dashboard',
      to: '/dashboard',
      icon: <LayoutDashboard className="w-4 h-4" />,
      isAvailable: true,
    },
    {
      name: 'System Status',
      to: '/system-status',
      icon: <Activity className="w-4 h-4" />,
      isAvailable: true,
    },
    {
      name: 'User Profiles',
      to: '/users',
      icon: <UserCheck className="w-4 h-4" />,
      isAvailable: false,
      phaseTag: 'F6',
    },
    {
      name: 'Txn Journey',
      to: '/journey',
      icon: <GitBranch className="w-4 h-4" />,
      isAvailable: false,
      phaseTag: 'F7',
    },
    {
      name: 'Incident Mode',
      to: '/incident',
      icon: <Flame className="w-4 h-4" />,
      isAvailable: false,
      phaseTag: 'F12',
    },
    {
      name: 'Real-Time Alerts',
      to: '/alerts',
      icon: <Radio className="w-4 h-4" />,
      isAvailable: false,
      phaseTag: 'F16',
    },
  ];

  return (
    <aside className="w-60 shrink-0 border-r border-slate-800/80 bg-slate-900/40 p-4 hidden md:flex flex-col justify-between">
      <div className="space-y-6">
        <div>
          <div className="px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-2 font-mono">
            Navigation
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => {
              if (item.isAvailable) {
                return (
                  <NavLink
                    key={item.name}
                    to={item.to}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-colors ${
                        isActive
                          ? 'bg-blue-600/15 text-blue-400 border border-blue-500/20'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                      }`
                    }
                  >
                    {item.icon}
                    <span>{item.name}</span>
                  </NavLink>
                );
              }

              // Non-available future phases that do not lead to fake pages
              return (
                <div
                  key={item.name}
                  className="flex items-center justify-between px-3 py-2 rounded-xl text-sm font-medium text-slate-500 cursor-not-allowed select-none opacity-60"
                  title={`${item.name} will be introduced in ${item.phaseTag}`}
                >
                  <div className="flex items-center gap-3">
                    {item.icon}
                    <span>{item.name}</span>
                  </div>
                  {item.phaseTag && (
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                      {item.phaseTag}
                    </span>
                  )}
                </div>
              );
            })}
          </nav>
        </div>
      </div>

      <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 text-[11px] text-slate-400 space-y-1">
        <div className="font-semibold text-slate-300">FraudShield Console</div>
        <div className="text-emerald-400 font-mono">✓ Phase F0 - F5 Active</div>
        <div className="text-slate-400">Reviewer Console Ready</div>
      </div>
    </aside>
  );
};

export default Sidebar;
