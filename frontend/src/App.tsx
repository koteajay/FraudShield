import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Header } from './components/Header';
import { ReviewerDashboard } from './pages/ReviewerDashboard';
import { TransactionInvestigation } from './pages/TransactionInvestigation';
import { JourneyInvestigationPage } from './pages/JourneyInvestigationPage';
import { SystemHealthPage } from './pages/SystemHealthPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-blue-500 selection:text-white">
        <Header />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<ReviewerDashboard />} />
            <Route path="/transactions/:id" element={<TransactionInvestigation />} />
            <Route path="/journey" element={<JourneyInvestigationPage />} />
            <Route path="/system" element={<SystemHealthPage />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
        <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-400">
          FraudShield Platform &bull; Phase 11 &ldquo;Why Flagged?&rdquo; Investigation UI Active
        </footer>
      </div>
    </BrowserRouter>
  );
};

export default App;
