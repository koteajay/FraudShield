import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppLayout } from '../components/layout/AppLayout';
import { DashboardPage } from '../pages/DashboardPage';
import { TransactionDetailsPage } from '../pages/TransactionDetailsPage';
import { HomePage } from '../pages/HomePage';

/**
 * Application routing configuration for FraudShield.
 * Root route ('/') loads the primary Reviewer Dashboard (Phase F2).
 * Dedicated transaction investigations are routed at '/transactions/:transactionId' (Phase F4).
 * System health and foundation telemetry is preserved at '/system-status'.
 */
export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: 'dashboard',
        element: <DashboardPage />,
      },
      {
        path: 'transactions/:transactionId',
        element: <TransactionDetailsPage />,
      },
      {
        path: 'system-status',
        element: <HomePage />,
      },
      {
        path: '*',
        element: <Navigate to="/" replace />,
      },
    ],
  },
]);

export default router;
