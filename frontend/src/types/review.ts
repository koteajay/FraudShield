/**
 * Types for Phase 12 Reviewer Workflow, Review Actions, and Audit History.
 */

export type ReviewStatus = 'PENDING_REVIEW' | 'REVIEWED' | 'CLEARED' | string;

export interface ReviewRecord {
  id: string;
  transaction_id: string;
  reviewer_id: string;
  previous_status: ReviewStatus;
  new_status: ReviewStatus;
  note?: string | null;
  created_at: string;
}

export interface ReviewHistoryResponse {
  transaction_id: string;
  reviews: ReviewRecord[];
}

export interface ReviewStatusUpdateRequest {
  status: ReviewStatus;
  note?: string;
}

export interface ReviewStatusUpdateResponse {
  id: string;
  transaction_reference: string;
  previous_review_status: string;
  review_status: string;
  updated_at: string;
  review?: ReviewRecord;
}
