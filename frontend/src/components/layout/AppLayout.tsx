import React from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

export interface AppLayoutProps {
  children?: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-blue-500 selection:text-white">
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          {children || <Outlet />}
        </main>
      </div>
      <footer className="border-t border-slate-900 py-4 px-6 text-center text-xs text-slate-500">
        FraudShield Platform &bull; Phase F0 Foundation &amp; Phase F1 API Layer
      </footer>
    </div>
  );
};

export default AppLayout;
