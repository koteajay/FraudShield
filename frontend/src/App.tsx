import React from 'react';
import { Header } from './components/Header';
import { HomePage } from './pages/HomePage';

export const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-blue-500 selection:text-white">
      <Header />
      <main className="flex-1">
        <HomePage />
      </main>
      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-400">
        FraudShield Platform &bull; Phase 0 Foundation Complete
      </footer>
    </div>
  );
};

export default App;
