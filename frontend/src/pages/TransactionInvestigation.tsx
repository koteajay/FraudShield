import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, AlertTriangle, RotateCw, Loader2 } from 'lucide-react';
import { getTransaction, updateTransactionStatus } from '../services/transactionService';
import { getUserProfile } from '../services/profileService';
import { getTransactionReviews } from '../services/reviewService';
import { InvestigationHeader } from '../components/investigation/InvestigationHeader';
import { WhyFlagged } from '../components/investigation/WhyFlagged';
import { BehaviourProfileCard } from '../components/investigation/BehaviourProfileCard';
import { DeviceInformationCard } from '../components/investigation/DeviceInformationCard';
import { AccountTakeoverCard } from '../components/investigation/AccountTakeoverCard';
import { ReviewerActions } from '../components/review/ReviewerActions';
import { ReviewHistory } from '../components/review/ReviewHistory';
import { TransactionJourney } from '../components/transaction-journey/TransactionJourney';
import type { TransactionDetail } from '../types/transaction';
import type { UserBehaviourProfile } from '../types/profile';
import type { ReviewRecord } from '../types/review';

export const TransactionInvestigation: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Transaction state
  const [transaction, setTransaction] = useState<TransactionDetail | null>(null);
  const [isTxLoading, setIsTxLoading] = useState<boolean>(true);
  const [txError, setTxError] = useState<string | null>(null);

  // Profile state (loaded independently)
  const [profile, setProfile] = useState<UserBehaviourProfile | null>(null);
  const [isProfileLoading, setIsProfileLoading] = useState<boolean>(false);
  const [profileError, setProfileError] = useState<string | null>(null);

  // Reviews audit history state
  const [reviews, setReviews] = useState<ReviewRecord[]>([]);
  const [isReviewsLoading, setIsReviewsLoading] = useState<boolean>(false);
  const [reviewsError, setReviewsError] = useState<string | null>(null);

  // Load review audit history
  const fetchReviewsData = useCallback(async (txId: string) => {
    setIsReviewsLoading(true);
    setReviewsError(null);
    try {
      const data = await getTransactionReviews(txId);
      setReviews(data.reviews || []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unable to load review history.';
      setReviewsError(msg);
    } finally {
      setIsReviewsLoading(false);
    }
  }, []);

  // Load transaction details
  const fetchTransactionData = useCallback(async (txId: string) => {
    setIsTxLoading(true);
    setTxError(null);
    try {
      const data = await getTransaction(txId);
      setTransaction(data);

      // Fetch user behaviour profile if user_id is present
      if (data.user_id) {
        fetchUserProfileData(data.user_id);
      }

      // Fetch review audit history
      fetchReviewsData(txId);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unable to load transaction details.';
      setTxError(msg);
      setTransaction(null);
    } finally {
      setIsTxLoading(false);
    }
  }, [fetchReviewsData]);

  // Load user profile
  const fetchUserProfileData = useCallback(async (userId: string) => {
    setIsProfileLoading(true);
    setProfileError(null);
    try {
      const profileData = await getUserProfile(userId);
      setProfile(profileData);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unable to load user behaviour profile.';
      setProfileError(msg);
      setProfile(null);
    } finally {
      setIsProfileLoading(false);
    }
  }, []);

  useEffect(() => {
    if (id) {
      fetchTransactionData(id);
    } else {
      setTxError('No transaction ID provided in URL.');
      setIsTxLoading(false);
    }
  }, [id, fetchTransactionData]);

  // Handle reviewer status update from header or actions
  const handleStatusChange = async (txId: string, newStatus: string) => {
    await updateTransactionStatus(txId, newStatus);
    // Update local transaction state
    setTransaction((prev) =>
      prev
        ? {
            ...prev,
            review_status: newStatus,
          }
        : null
    );
    fetchReviewsData(txId);
  };

  const handleBack = () => {
    if (window.history.length > 2) {
      navigate(-1);
    } else {
      navigate('/dashboard');
    }
  };

  // 1. Transaction Loading State
  if (isTxLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
          <span>Loading transaction investigation data...</span>
        </div>
        {/* Skeletons */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 h-36 animate-pulse" />
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-4 rounded-2xl border border-slate-800 bg-slate-900/40 p-6 h-64 animate-pulse" />
          <div className="lg:col-span-8 rounded-2xl border border-slate-800 bg-slate-900/40 p-6 h-64 animate-pulse" />
        </div>
      </div>
    );
  }

  // 2. Transaction Error State
  if (txError || !transaction) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center space-y-6">
        <div className="w-16 h-16 rounded-full bg-rose-500/10 border border-rose-500/30 text-rose-400 flex items-center justify-center mx-auto">
          <AlertTriangle className="w-8 h-8" />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-white tracking-tight">Transaction Not Found</h2>
          <p className="text-sm text-slate-400 max-w-md mx-auto">
            {txError || 'The requested transaction could not be located in the fraud database.'}
          </p>
        </div>
        <div className="flex items-center justify-center gap-3">
          <button
            type="button"
            onClick={handleBack}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-sm font-medium text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Transactions</span>
          </button>
          {id && (
            <button
              type="button"
              onClick={() => fetchTransactionData(id)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-sm font-medium text-white transition-colors"
            >
              <RotateCw className="w-4 h-4" />
              <span>Retry</span>
            </button>
          )}
        </div>
      </div>
    );
  }

  // 3. Normal Presentation
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-in fade-in duration-300">
      {/* Investigation Header */}
      <InvestigationHeader
        transaction={transaction}
        onBack={handleBack}
        onStatusChange={handleStatusChange}
      />

      {/* WHY FLAGGED? Section (Risk Score Visualization & Triggered Rules) */}
      <WhyFlagged transaction={transaction} />

      {/* User Behaviour Profile */}
      <section aria-labelledby="behaviour-profile-heading">
        <BehaviourProfileCard
          profile={profile}
          transaction={transaction}
          isLoading={isProfileLoading}
          error={profileError}
          onRetry={() => transaction.user_id && fetchUserProfileData(transaction.user_id)}
        />
      </section>

      {/* Device Information */}
      <section aria-labelledby="device-info-heading">
        <DeviceInformationCard device={transaction.device} />
      </section>

      {/* Account Takeover Risk Section (if available or at risk) */}
      {transaction.account_takeover && (
        <section aria-labelledby="ato-heading">
          <AccountTakeoverCard ato={transaction.account_takeover} />
        </section>
      )}

      {/* Transaction Journey (Reusing Phase 8 Component) */}
      <section aria-labelledby="journey-heading" className="space-y-4">
        <div className="border-t border-slate-800 pt-6">
          <TransactionJourney initialTransactionId={transaction.id} />
        </div>
      </section>
    </div>
  );
};
