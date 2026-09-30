import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getTransactionById } from '../services/api/transactions';
import { getFraudAssessment } from '../services/api/fraud';
import type { Transaction } from '../types/transaction';
import type { FraudAssessment } from '../types/fraud';
import { RiskBadge } from '../components/risk/RiskBadge';
import { RiskScore } from '../components/risk/RiskScore';
import { StatusBadge } from '../components/risk/StatusBadge';
import { FraudRuleResult } from '../components/fraud/FraudRuleResult';
import { WhyFlaggedModal } from '../components/fraud/WhyFlaggedModal';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { Card } from '../components/common/Card';
import {
  SAMPLE_TRANSACTIONS,
  SAMPLE_FRAUD_ASSESSMENTS,
} from '../utils/sampleData';
import {
  ArrowLeft,
  Sparkles,
  User,
  CreditCard,
  MapPin,
  Laptop,
  Network,
  Clock,
  ShieldCheck,
  AlertCircle,
  Eye,
} from 'lucide-react';

export const TransactionDetailsPage: React.FC = () => {
  const { transactionId } = useParams<{ transactionId: string }>();

  const [transaction, setTransaction] = useState<Transaction | null>(null);
  const [assessment, setAssessment] = useState<FraudAssessment | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isWhyFlaggedOpen, setIsWhyFlaggedOpen] = useState<boolean>(false);
  const [isInspectionMode, setIsInspectionMode] = useState<boolean>(false);

  const fetchTransactionData = useCallback(async () => {
    if (!transactionId) return;

    setIsLoading(true);
    setError(null);

    try {
      // 1. Fetch transaction details from API service
      const txnData = await getTransactionById(transactionId);
      setTransaction(txnData);

      // 2. Fetch fraud assessment if available
      try {
        const assessmentData = await getFraudAssessment(transactionId);
        setAssessment(assessmentData);
      } catch {
        // Assessment endpoint is optional
      }

      setIsInspectionMode(false);
    } catch (err: unknown) {
      // Check if fallback sample fixture exists for this transaction ID
      const sampleTxn = SAMPLE_TRANSACTIONS.find((t) => t.id === transactionId);

      if (
        err &&
        typeof err === 'object' &&
        'message' in err &&
        typeof (err as { message: unknown }).message === 'string'
      ) {
        setError((err as { message: string }).message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError(`Unable to load transaction ${transactionId} from backend.`);
      }

      // If user navigated from sample dataset or wants fallback:
      if (sampleTxn) {
        // We will offer the preview option on ErrorState
      }
    } finally {
      setIsLoading(false);
    }
  }, [transactionId]);

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect
    fetchTransactionData();
  }, [fetchTransactionData]);

  // Fallback for offline inspection preview
  const enableSamplePreview = () => {
    if (!transactionId) return;
    const sampleTxn =
      SAMPLE_TRANSACTIONS.find((t) => t.id === transactionId) ||
      SAMPLE_TRANSACTIONS[0];
    const sampleAssessment =
      SAMPLE_FRAUD_ASSESSMENTS[sampleTxn.id] ||
      SAMPLE_FRAUD_ASSESSMENTS['TXN-10234'];

    setTransaction(sampleTxn);
    setAssessment(sampleAssessment);
    setIsInspectionMode(true);
    setError(null);
  };

  // Format currency
  const formatAmount = (amount?: number, currency: string = 'USD') => {
    if (amount === undefined) return '--';
    try {
      return new Intl.NumberFormat(undefined, {
        style: 'currency',
        currency: currency.toUpperCase(),
        maximumFractionDigits: 2,
      }).format(amount);
    } catch {
      return `${currency} ${amount.toLocaleString()}`;
    }
  };

  // Loading State
  if (isLoading && !transaction) {
    return (
      <div className="max-w-6xl mx-auto px-6 py-16">
        <LoadingState
          message="Loading transaction details and risk factors..."
          size="lg"
          fullHeight={true}
        />
      </div>
    );
  }

  // Error State
  if (error && !transaction) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-16 space-y-6">
        <ErrorState
          title={`Transaction ${transactionId} unavailable`}
          message={error}
          onRetry={fetchTransactionData}
          retryLabel="Retry API"
        />

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 text-center">
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Dashboard</span>
          </Link>

          <button
            type="button"
            onClick={enableSamplePreview}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 text-xs font-semibold border border-blue-500/40 transition cursor-pointer"
          >
            <Eye className="w-4 h-4 text-blue-400" />
            <span>Preview Sample Record for {transactionId}</span>
          </button>
        </div>
      </div>
    );
  }

  if (!transaction) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-16 text-center">
        <h2 className="text-xl font-bold text-white mb-2">
          Transaction Not Found
        </h2>
        <p className="text-sm text-slate-400 mb-6">
          The requested transaction identifier does not exist.
        </p>
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 text-slate-50 text-xs font-semibold hover:bg-blue-500 transition shadow-md"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Dashboard</span>
        </Link>
      </div>
    );
  }

  // Format device info string
  const deviceDisplay = () => {
    if (!transaction.deviceInfo) {
      return (
        <span className="text-slate-500 italic">Device information unavailable</span>
      );
    }
    if (typeof transaction.deviceInfo === 'string') {
      return <span>{transaction.deviceInfo}</span>;
    }
    return (
      <div className="space-y-0.5 text-xs">
        <div>
          {transaction.deviceInfo.browser || 'Unknown Browser'} /{' '}
          {transaction.deviceInfo.os || 'Unknown OS'}
        </div>
        {transaction.deviceInfo.deviceId && (
          <div className="text-[11px] text-slate-500 font-mono">
            Device ID: {transaction.deviceInfo.deviceId}
          </div>
        )}
      </div>
    );
  };

  // Rules list from assessment or construct from flags
  const ruleResults =
    assessment?.rules ||
    (assessment?.flags || []).map((f) => ({
      ruleName: f.ruleName,
      isTriggered: true,
      reason: f.description,
      evidence: (f.metadata?.evidence as string | Record<string, unknown>) || null,
      scoreContribution: f.scoreImpact,
    }));

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      {/* Inspection Mode Alert Banner */}
      {isInspectionMode && (
        <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>
              <strong>Development Inspection Preview:</strong> Displaying sample transaction data because backend is offline.
            </span>
          </div>
          <button
            type="button"
            onClick={fetchTransactionData}
            className="px-2.5 py-1 rounded-lg bg-amber-500/20 text-amber-200 border border-amber-500/40 text-[11px] font-semibold hover:bg-amber-500/30 cursor-pointer"
          >
            Re-query API
          </button>
        </div>
      )}

      {/* Navigation & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <Link
            to="/dashboard"
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 transition cursor-pointer"
            aria-label="Back to Dashboard"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>

          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-xl font-bold font-mono text-white tracking-tight">
                {transaction.id}
              </h1>
              <StatusBadge status={transaction.status} size="sm" />
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-400 mt-0.5">
              <span className="flex items-center gap-1 font-mono">
                <Clock className="w-3 h-3 text-slate-500" />
                {new Date(transaction.timestamp).toLocaleString()}
              </span>
            </div>
          </div>
        </div>

        {/* PROMINENT "Why Flagged?" Action Button (PHASE F5) */}
        <div>
          <button
            type="button"
            onClick={() => setIsWhyFlaggedOpen(true)}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-slate-50 text-sm font-bold shadow-lg shadow-blue-900/30 border border-blue-400/30 transition-all duration-150 cursor-pointer active:scale-95"
            aria-label="Open Why Flagged investigation panel"
          >
            <Sparkles className="w-4 h-4 text-blue-200 animate-pulse" />
            <span>Why Flagged?</span>
          </button>
        </div>
      </div>

      {/* Grid: Transaction Details + Risk Evaluation */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 1. Transaction Information (2 columns on lg) */}
        <div className="lg:col-span-2 space-y-6">
          <Card variant="default">
            <h2 className="text-xs uppercase tracking-wider font-semibold text-slate-400 mb-4 pb-2 border-b border-slate-800 flex items-center gap-2">
              <CreditCard className="w-4 h-4 text-blue-400" />
              Transaction Information
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-5 gap-x-6">
              {/* Transaction ID */}
              <div>
                <span className="text-[11px] font-mono uppercase text-slate-500 block mb-1">
                  TRANSACTION ID
                </span>
                <span className="font-mono text-sm font-semibold text-white">
                  {transaction.id}
                </span>
              </div>

              {/* User ID */}
              <div>
                <span className="text-[11px] font-mono uppercase text-slate-500 block mb-1">
                  USER IDENTIFIER
                </span>
                <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-950/70 border border-slate-800 font-mono text-xs text-indigo-300">
                  <User className="w-3.5 h-3.5 text-indigo-400" />
                  <span>{transaction.userId}</span>
                </div>
              </div>

              {/* Amount */}
              <div>
                <span className="text-[11px] font-mono uppercase text-slate-500 block mb-1">
                  AMOUNT
                </span>
                <span className="font-mono text-xl font-bold text-white">
                  {formatAmount(transaction.amount, transaction.currency)}
                </span>
              </div>

              {/* Currency */}
              <div>
                <span className="text-[11px] font-mono uppercase text-slate-500 block mb-1">
                  CURRENCY
                </span>
                <span className="font-mono text-sm font-medium text-slate-300">
                  {transaction.currency.toUpperCase()}
                </span>
              </div>

              {/* Location */}
              <div>
                <span className="text-[11px] font-mono uppercase text-slate-500 block mb-1">
                  GEOGRAPHIC LOCATION
                </span>
                <div className="flex items-center gap-1.5 text-xs text-slate-200">
                  <MapPin className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  <span>{transaction.location || 'Location unavailable'}</span>
                </div>
              </div>

              {/* Timestamp */}
              <div>
                <span className="text-[11px] font-mono uppercase text-slate-500 block mb-1">
                  RECORDED TIMESTAMP
                </span>
                <span className="text-xs text-slate-300 font-mono">
                  {new Date(transaction.timestamp).toUTCString()}
                </span>
              </div>

              {/* Merchant / Category */}
              <div>
                <span className="text-[11px] font-mono uppercase text-slate-500 block mb-1">
                  MERCHANT &amp; CATEGORY
                </span>
                <span className="text-xs text-slate-300">
                  {transaction.merchant || 'Direct Transfer'}{' '}
                  {transaction.category && `(${transaction.category})`}
                </span>
              </div>

              {/* Payment Method */}
              <div>
                <span className="text-[11px] font-mono uppercase text-slate-500 block mb-1">
                  PAYMENT METHOD
                </span>
                <span className="text-xs text-slate-300 font-mono">
                  {transaction.paymentMethod || 'Standard Gateway'}
                </span>
              </div>
            </div>

            {/* Device Information section */}
            <div className="mt-6 pt-5 border-t border-slate-800/80">
              <span className="text-[11px] font-mono uppercase text-slate-500 block mb-2 flex items-center gap-1.5">
                <Laptop className="w-3.5 h-3.5 text-slate-400" />
                DEVICE INFORMATION
              </span>
              <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800 text-slate-300">
                {deviceDisplay()}
                {transaction.ipAddress && (
                  <div className="mt-2 pt-2 border-t border-slate-900 flex items-center gap-2 text-[11px] font-mono text-slate-400">
                    <Network className="w-3.5 h-3.5 text-slate-500" />
                    <span>Origin IP: {transaction.ipAddress}</span>
                  </div>
                )}
              </div>
            </div>
          </Card>
        </div>

        {/* 2. Risk Information Card (1 column) */}
        <div className="space-y-6">
          <Card variant="default">
            <h2 className="text-xs uppercase tracking-wider font-semibold text-slate-400 mb-4 pb-2 border-b border-slate-800 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-rose-400" />
              Risk Assessment
            </h2>

            <div className="space-y-6">
              {/* Risk Level */}
              <div>
                <span className="text-[11px] font-mono uppercase text-slate-500 block mb-1.5">
                  OVERALL RISK SEVERITY
                </span>
                <RiskBadge level={transaction.riskLevel} size="lg" />
              </div>

              {/* Risk Score */}
              <div>
                <span className="text-[11px] font-mono uppercase text-slate-500 block mb-1.5">
                  COMPOSITE RISK SCORE
                </span>
                <RiskScore
                  score={transaction.riskScore}
                  riskLevel={transaction.riskLevel}
                  size="lg"
                  showBar={true}
                />
              </div>

              {/* Status */}
              <div>
                <span className="text-[11px] font-mono uppercase text-slate-500 block mb-1.5">
                  REVIEW STATUS
                </span>
                <StatusBadge status={transaction.status} size="md" />
              </div>

              {/* Quick Action Button */}
              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => setIsWhyFlaggedOpen(true)}
                  className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600/15 hover:bg-blue-600/25 text-blue-300 border border-blue-500/30 text-xs font-semibold transition cursor-pointer"
                >
                  <Sparkles className="w-3.5 h-3.5 text-blue-400" />
                  <span>Explain Risk Scoring</span>
                </button>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* 3. Fraud Flags & Evaluation Rules Section */}
      <section aria-labelledby="fraud-rules-heading" className="space-y-4">
        <div className="flex items-center justify-between">
          <h2
            id="fraud-rules-heading"
            className="text-base font-bold text-white flex items-center gap-2"
          >
            <span>Fraud Flags &amp; Rule Evaluations</span>
            <span className="text-xs font-mono text-slate-500">
              ({ruleResults.length} rules evaluated)
            </span>
          </h2>
        </div>

        {ruleResults.length === 0 ? (
          <Card variant="subtle">
            <p className="text-xs text-slate-500 text-center py-4">
              No fraud rule evaluation telemetry has been recorded for this transaction.
            </p>
          </Card>
        ) : (
          <div className="space-y-3">
            {ruleResults.map((rule, idx) => (
              <FraudRuleResult key={idx} rule={rule} />
            ))}
          </div>
        )}
      </section>

      {/* Phase F5 "Why Flagged?" Experience Modal */}
      <WhyFlaggedModal
        isOpen={isWhyFlaggedOpen}
        onClose={() => setIsWhyFlaggedOpen(false)}
        transaction={transaction}
        assessment={assessment}
      />
    </div>
  );
};

export default TransactionDetailsPage;
