import { describe, it, expect, vi, beforeEach, afterAll } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event'; 
import { BrowserRouter } from 'react-router-dom';
import ClientsList from './ClientsList';
import { ClientProfile } from '../../services/clients'; // Remove clientService import
// Remove unused formatDate import

// Mock the clients service - Mock the actual functions
const mockGetAll = vi.fn();
const mockDelete = vi.fn();
vi.mock('../../services/clients', () => ({
  default: {
    getAll: mockGetAll,
    delete: mockDelete,
  }
}));

// Mock window.confirm
const originalConfirm = window.confirm;

// Sample client data
const mockClients: ClientProfile[] = [
  {
    id: 1,
    user_id: 1,
    company_name: 'Test Company 1',
    industry: 'Technology',
    website: 'https://example1.com',
    is_active: true,
    created_at: '2025-04-01T12:00:00Z',
    updated_at: undefined,
  },
  {
    id: 2,
    user_id: 2,
    company_name: 'Test Company 2',
    industry: 'Finance',
    is_active: false,
    created_at: '2025-04-02T12:00:00Z',
    updated_at: undefined,
  },
];

describe('ClientsList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.confirm = vi.fn().mockReturnValue(true); // Default to confirming
    mockGetAll.mockReset(); // Reset mocks
    mockDelete.mockReset();
  });

  // Restore original confirm after tests
  afterAll(() => {
    window.confirm = originalConfirm;
  });

  it('renders loading state initially', () => {
    mockGetAll.mockImplementation(() => new Promise<any>(() => {})); // Never resolves

    render(
      <BrowserRouter>
        <ClientsList />
      </BrowserRouter>
    );
    // Check for loading indicator (adjust selector if needed)
    expect(screen.getByText(/Loading content pieces/i)).toBeInTheDocument(); // Assuming loading text from component
  });

  it('renders clients list when loaded', async () => {
    mockGetAll.mockResolvedValue(mockClients);

    render(
      <BrowserRouter>
        <ClientsList />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Test Company 1')).toBeInTheDocument();
    });

    expect(screen.getByText('Test Company 2')).toBeInTheDocument();
    expect(screen.getByText('Technology')).toBeInTheDocument();
    expect(screen.getByText('Finance')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText('Inactive')).toBeInTheDocument();
    // Check links are correct
    expect(screen.getByTitle('View Details').closest('a')).toHaveAttribute('href', '/admin/clients/1');
    expect(screen.getByTitle('Edit Client').closest('a')).toHaveAttribute('href', '/admin/clients/1/edit');
  });

  it('renders empty state when no clients', async () => {
    mockGetAll.mockResolvedValue([]);

    render(
      <BrowserRouter>
        <ClientsList />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No clients found.')).toBeInTheDocument();
    });
    expect(screen.getByText('Create New Client')).toBeInTheDocument();
  });

  it('renders error state when loading fails', async () => {
    mockGetAll.mockRejectedValue(new Error('Failed to load'));

    render(
      <BrowserRouter>
        <ClientsList />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Failed to load clients/)).toBeInTheDocument();
    });
  });

  // Test for onClientSelected removed

  it('deletes client when Delete button is clicked and confirmed', async () => {
    mockGetAll.mockResolvedValue([...mockClients]); // Use spread to avoid modifying original
    mockDelete.mockResolvedValue(mockClients[0]);
    const onClientDeleted = vi.fn();

    render(
      <BrowserRouter>
        <ClientsList onClientDeleted={onClientDeleted} />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Test Company 1')).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByTitle('Delete Client');
    await userEvent.click(deleteButtons[0]);

    expect(window.confirm).toHaveBeenCalled();
    expect(mockDelete).toHaveBeenCalledWith(1); // Call mock directly

    // Check if the row is removed (or if onClientDeleted was called)
    await waitFor(() => {
       expect(screen.queryByText('Test Company 1')).not.toBeInTheDocument();
    });
     expect(onClientDeleted).toHaveBeenCalled();
  });

  it('does not delete client when Delete is clicked but not confirmed', async () => {
    mockGetAll.mockResolvedValue(mockClients);
    window.confirm = vi.fn().mockReturnValue(false); // Reject confirmation

    render(
      <BrowserRouter>
        <ClientsList />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Test Company 1')).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByTitle('Delete Client');
    await userEvent.click(deleteButtons[0]);

    expect(window.confirm).toHaveBeenCalled();
    expect(mockDelete).not.toHaveBeenCalled(); // Check mock directly
  });
});
