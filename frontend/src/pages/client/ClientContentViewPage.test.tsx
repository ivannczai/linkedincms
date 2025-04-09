import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { vi } from 'vitest';
import ClientContentViewPage from './ClientContentViewPage';
import { AuthContext, AuthContextType } from '../../context/AuthContext';
import { UserInfo } from '../../services/auth'; // Import UserInfo from correct source
import api from '../../services/api';

// Define ContentPieceRead locally if not globally available or imported correctly
interface ContentPieceRead {
  id: number;
  client_id: number;
  title: string;
  idea: string;
  angle: string;
  body: string; // Assuming HTML content
  status: 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'POSTED'; // Add other statuses if needed
  created_at: string;
  updated_at: string;
  client_rating?: number | null;
  client_notes?: string | null;
  posted_at?: string | null;
}


// Mock the API service
vi.mock('../../services/api');

// Mock react-router-dom navigation hooks
const mockNavigate = vi.fn();
const mockUseParams = vi.fn(() => ({ id: '1' })); // Mock useParams to return a content ID
vi.mock('react-router-dom', () => ({
  // Keep minimal exports needed
  MemoryRouter: require('react-router-dom').MemoryRouter,
  Routes: require('react-router-dom').Routes,
  Route: require('react-router-dom').Route,
  useParams: mockUseParams,
  useNavigate: () => mockNavigate,
}));

// Mock AuthContext
const mockClientUser: UserInfo = { id: 1, email: 'client@example.com', role: 'client', client_id: 1 }; // Explicitly type role
const mockAuthContextValue: AuthContextType = {
  user: mockClientUser,
  isLoading: false,
  isAuthenticated: true,
  login: vi.fn(),
  logout: vi.fn(),
  error: null,
  refetchUser: vi.fn().mockResolvedValue(undefined), // Add mock refetchUser
};

// Mock content data
const mockContent: ContentPieceRead = {
  id: 1,
  client_id: 1,
  title: 'Test Content Title',
  idea: 'Test Idea',
  angle: 'Test Angle',
  body: '<p>Test Body Content</p>', // Assuming HTML content
  status: 'PENDING_APPROVAL',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  client_rating: null,
  client_notes: null,
  posted_at: null,
};

// Helper to render with context and router
const renderWithProviders = (ui: React.ReactElement) => {
  // Reset useParams mock before each render if needed, or ensure it's consistent
  mockUseParams.mockReturnValue({ id: '1' });
  return render(
    <AuthContext.Provider value={mockAuthContextValue}>
      <MemoryRouter initialEntries={['/client/contents/1']}>
        <Routes>
          <Route path="/client/contents/:id" element={ui} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
};

describe('ClientContentViewPage', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    // Mock successful API calls by default
    vi.mocked(api.get).mockResolvedValue({ data: mockContent });
    vi.mocked(api.patch).mockResolvedValue({ data: { ...mockContent, status: 'APPROVED' } }); // Mock approve action
  });

  test('renders content details correctly', async () => {
    renderWithProviders(<ClientContentViewPage />);

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/api/v1/contents/1');
    });

    expect(screen.getByText('Test Content Title')).toBeInTheDocument();
    expect(screen.getByText('Test Idea')).toBeInTheDocument();
    expect(screen.getByText('Test Angle')).toBeInTheDocument();
    // Check for body content (might need specific query if HTML is rendered)
    expect(screen.getByText('Test Body Content')).toBeInTheDocument();
    expect(screen.getByText('PENDING_APPROVAL')).toBeInTheDocument();
  });

  test('shows Approve and Request Revision buttons for pending content', async () => {
    renderWithProviders(<ClientContentViewPage />);
    await waitFor(() => {
      expect(screen.getByText('Test Content Title')).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: /approve/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /request revision/i })).toBeInTheDocument();
  });

  test('calls approve API when Approve button is clicked', async () => {
    renderWithProviders(<ClientContentViewPage />);
    await waitFor(() => {
      expect(screen.getByText('Test Content Title')).toBeInTheDocument();
    });

    const approveButton = screen.getByRole('button', { name: /approve/i });
    fireEvent.click(approveButton);

    await waitFor(() => {
      expect(api.patch).toHaveBeenCalledWith('/api/v1/contents/1/status', { status: 'APPROVED' });
    });
    // Optionally check for navigation or status update
    // expect(mockNavigate).toHaveBeenCalledWith('/client/library'); // Example navigation check
  });

  // Add more tests for Request Revision, different statuses, error handling etc.
});
