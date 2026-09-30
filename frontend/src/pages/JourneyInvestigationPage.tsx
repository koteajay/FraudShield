import React from 'react';
import { TransactionJourney } from '../components/transaction-journey';

export const JourneyInvestigationPage: React.FC = () => {
  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      <TransactionJourney />
    </div>
  );
};
