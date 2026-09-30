import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { TransactionTable } from '../components/transactions/TransactionTable';
import type { PaginatedTransactionsResponse, Transaction } from '../types/transaction';

const mockTransactions: Transaction[] = [
  {
    id: 'txn-101',
    transaction_reference: 'TXN-REF-101',
    user_id: 'user-alpha',
    amount: 75000,
    currency: 'INR',
    merchant_name: 'Electronics Store',
    location: 'Delhi, IN',
    city: 'Delhi',
    country: 'IN',
    timestamp: '2026-09-30T10:21:00Z',
    risk_score: 82,
    risk_level: 'CRITICAL',
    status: 'FLAGGED',
    review_status: 'PENDING_REVIEW',
  },
  {
    id: 'txn-102',
    transaction_reference: 'TXN-REF-102',
    user_id: 'user-beta',
    amount: 3500,
    currency: 'INR',
    merchant_name: 'Coffee Cafe',
    location: 'Hyderabad, IN',
    city: 'Hyderabad',
    country: 'IN',
    timestamp: '2026-09-30T10:15:00Z',
    risk_score: 15,
    risk_level: 'LOW',
    status: 'APPROVED',
    review_status: 'CLEARED',
  },
];

const mockPaginatedData: PaginatedTransactionsResponse = {
  items: mockTransactions,
  page: 1,
  page_size: 20,
  total: 2,
  total_pages: 1,
};

describe('TransactionTable Component', () => {
  it('renders all required columns and transaction data', () => {
    const handleSelect = vi.fn();
    render(
      <TransactionTable
        data={mockPaginatedData}
        isLoading={false}
        error={null}
        filters={{ page: 1, page_size: 20 }}
        onFilterChange={vi.fn()}
        onRefresh={vi.fn()}
        onSelectTransaction={handleSelect}
      />
    );

    // Columns
    expect(screen.getByText('Transaction ID')).toBeInTheDocument();
    expect(screen.getByText('User')).toBeInTheDocument();
    expect(screen.getByText('Amount')).toBeInTheDocument();
    expect(screen.getByText('Location')).toBeInTheDocument();
    expect(screen.getByText('Score')).toBeInTheDocument();
    expect(screen.getByText('Risk Level')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Time')).toBeInTheDocument();

    // Data rows
    expect(screen.getByText('TXN-REF-101')).toBeInTheDocument();
    expect(screen.getByText('user-alpha')).toBeInTheDocument();
    expect(screen.getByText('Delhi, IN')).toBeInTheDocument();
    expect(screen.getByText('82')).toBeInTheDocument();
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();

    expect(screen.getByText('TXN-REF-102')).toBeInTheDocument();
    expect(screen.getByText('user-beta')).toBeInTheDocument();
    expect(screen.getByText('Hyderabad, IN')).toBeInTheDocument();
    expect(screen.getByText('15')).toBeInTheDocument();
    expect(screen.getByText('LOW')).toBeInTheDocument();
  });

  it('triggers onSelectTransaction when row is clicked', () => {
    const handleSelect = vi.fn();
    render(
      <TransactionTable
        data={mockPaginatedData}
        isLoading={false}
        error={null}
        filters={{ page: 1 }}
        onFilterChange={vi.fn()}
        onRefresh={vi.fn()}
        onSelectTransaction={handleSelect}
      />
    );

    const firstRowRef = screen.getByText('TXN-REF-101');
    fireEvent.click(firstRowRef.closest('tr')!);
    expect(handleSelect).toHaveBeenCalledWith(mockTransactions[0]);
  });

  it('renders loading skeleton when loading with no data', () => {
    render(
      <TransactionTable
        data={null}
        isLoading={true}
        error={null}
        filters={{ page: 1 }}
        onFilterChange={vi.fn()}
        onRefresh={vi.fn()}
        onSelectTransaction={vi.fn()}
      />
    );

    expect(screen.getByRole('status', { name: /loading transactions table/i })).toBeInTheDocument();
  });

  it('renders error state and allows retry', () => {
    const handleRefresh = vi.fn();
    render(
      <TransactionTable
        data={null}
        isLoading={false}
        error="Network timeout occurred"
        filters={{ page: 1 }}
        onFilterChange={vi.fn()}
        onRefresh={handleRefresh}
        onSelectTransaction={vi.fn()}
      />
    );

    expect(screen.getByText('Unable to load transactions')).toBeInTheDocument();
    expect(screen.getByText('Network timeout occurred')).toBeInTheDocument();

    const retryBtn = screen.getByRole('button', { name: /retry/i });
    fireEvent.click(retryBtn);
    expect(handleRefresh).toHaveBeenCalled();
  });

  it('renders empty state when items list is empty', () => {
    render(
      <TransactionTable
        data={{ items: [], page: 1, page_size: 20, total: 0, total_pages: 1 }}
        isLoading={false}
        error={null}
        filters={{ page: 1 }}
        onFilterChange={vi.fn()}
        onRefresh={vi.fn()}
        onSelectTransaction={vi.fn()}
      />
    );

    expect(screen.getByText('No transactions found')).toBeInTheDocument();
  });

  it('manages pagination disabled states and triggers page navigation', () => {
    const handleFilterChange = vi.fn();
    const multiPageData: PaginatedTransactionsResponse = {
      items: mockTransactions,
      page: 1,
      page_size: 2,
      total: 10,
      total_pages: 5,
    };

    render(
      <TransactionTable
        data={multiPageData}
        isLoading={false}
        error={null}
        filters={{ page: 1, page_size: 2 }}
        onFilterChange={handleFilterChange}
        onRefresh={vi.fn()}
        onSelectTransaction={vi.fn()}
      />
    );

    const prevBtn = screen.getByRole('button', { name: /previous page/i });
    const nextBtn = screen.getByRole('button', { name: /next page/i });

    expect(prevBtn).toBeDisabled();
    expect(nextBtn).not.toBeDisabled();

    fireEvent.click(nextBtn);
    expect(handleFilterChange).toHaveBeenCalledWith({ page: 2 });
  });
});
