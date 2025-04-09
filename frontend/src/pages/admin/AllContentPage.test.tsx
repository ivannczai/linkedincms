import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import AllContentPage from './AllContentPage';
import clientService, { ClientProfile } from '../../services/clients';
import { ContentStatus } from '../../services/contents';

// Mock clientService
vi.mock('../../services/clients', () => ({
  default: {
    getAll: vi.fn(),
  },
}));

// Mock ContentsList component
vi.mock('../../components/contents/ContentsList', () => ({
  default: vi.fn(({ clientId, status }) => (
    <div data-testid="contents-list" data-clientid={clientId} data-status={status}>
      Mocked ContentsList
    </div>
  )),
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom') as object; // Cast to object
  return {
    ...actual, // Spread as object
    useNavigate: () => mockNavigate,
  };
});

const mockClients: ClientProfile[] = [
  { id: 1, user_id: 10, company_name: 'Client A', industry: 'Tech', is_active: true, created_at: '' },
  { id: 2, user_id: 11, company_name: 'Client B', industry: 'Finance', is_active: true, created_at: '' },
];

describe('AllContentPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(clientService.getAll).mockResolvedValue(mockClients);
  });

  it('renders the page title and create button', async () => {
    render(<MemoryRouter><AllContentPage /></MemoryRouter>);
    expect(await screen.findByText('All Content Pieces')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Create New Content/i })).toBeInTheDocument();
  });

  it('fetches and displays clients in the filter dropdown', async () => {
    render(<MemoryRouter><AllContentPage /></MemoryRouter>);
    
    // Wait for clients to load
    await waitFor(() => expect(clientService.getAll).toHaveBeenCalled());

    // Check if dropdown options are rendered
    expect(screen.getByRole('option', { name: 'All Clients' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Client A' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Client B' })).toBeInTheDocument();
  });

  it('renders status filter buttons', async () => {
    render(<MemoryRouter><AllContentPage /></MemoryRouter>);
    await waitFor(() => expect(clientService.getAll).toHaveBeenCalled()); // Ensure page is loaded

    expect(screen.getByRole('button', { name: 'All' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: ContentStatus.DRAFT.replace('_', ' ') })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: ContentStatus.PENDING_APPROVAL.replace('_', ' ') })).toBeInTheDocument();
    // ... check other statuses
  });

  it('updates ContentsList props when client filter changes', async () => {
    render(<MemoryRouter><AllContentPage /></MemoryRouter>);
    await waitFor(() => expect(clientService.getAll).toHaveBeenCalled()); 

    const clientSelect = screen.getByLabelText(/Filter by Client/i);
    const contentsList = screen.getByTestId('contents-list');

    // Initial state (no client filter)
    expect(contentsList).toHaveAttribute('data-clientid', 'undefined');

    // Select Client A
    fireEvent.change(clientSelect, { target: { value: '1' } });
    await waitFor(() => {
       expect(contentsList).toHaveAttribute('data-clientid', '1');
       expect(contentsList).toHaveAttribute('data-status', 'undefined'); // Status shouldn't change
    });
     
    // Select All Clients
    fireEvent.change(clientSelect, { target: { value: '' } });
     await waitFor(() => {
       expect(contentsList).toHaveAttribute('data-clientid', 'undefined');
    });
  });

  it('updates ContentsList props when status filter changes', async () => {
    render(<MemoryRouter><AllContentPage /></MemoryRouter>);
    await waitFor(() => expect(clientService.getAll).toHaveBeenCalled());

    const pendingButton = screen.getByRole('button', { name: ContentStatus.PENDING_APPROVAL.replace('_', ' ') });
    const allButton = screen.getByRole('button', { name: 'All' });
    const contentsList = screen.getByTestId('contents-list');

    // Initial state (no status filter)
    expect(contentsList).toHaveAttribute('data-status', 'undefined');

    // Click Pending Approval
    fireEvent.click(pendingButton);
    await waitFor(() => {
       expect(contentsList).toHaveAttribute('data-status', ContentStatus.PENDING_APPROVAL);
       expect(contentsList).toHaveAttribute('data-clientid', 'undefined'); // Client shouldn't change
    });

    // Click All
    fireEvent.click(allButton);
    await waitFor(() => {
       expect(contentsList).toHaveAttribute('data-status', 'undefined');
    });
  });

  it('navigates to create page when "Create New Content" is clicked', async () => {
     render(<MemoryRouter><AllContentPage /></MemoryRouter>);
     await waitFor(() => expect(clientService.getAll).toHaveBeenCalled());

     const createButton = screen.getByRole('button', { name: /Create New Content/i });
     fireEvent.click(createButton);

     expect(mockNavigate).toHaveBeenCalledWith('/admin/content/new');
  });

});
