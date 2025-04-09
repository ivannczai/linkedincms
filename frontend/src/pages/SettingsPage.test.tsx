import { render, screen, fireEvent, waitFor } from '@testing-library/react';
// Removed unused BrowserRouter
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { vi } from 'vitest'; // Using vitest's mocking utilities
import SettingsPage from './SettingsPage';
import { AuthContext, AuthContextType } from '../context/AuthContext'; // Adjust path if needed
import { UserInfo } from '../services/auth'; // Import UserInfo from correct source
import api from '../services/api'; // Default import

// Mock the api service
vi.mock('../services/api');

// Mock only useLocation from react-router-dom
const mockUseLocation = vi.fn();
vi.mock('react-router-dom', () => ({
  // Keep minimal exports needed, primarily useLocation
  MemoryRouter: require('react-router-dom').MemoryRouter, // Keep router components if needed by helper
  Routes: require('react-router-dom').Routes,
  Route: require('react-router-dom').Route,
  useLocation: mockUseLocation,
}));

// Mock useAuth context
const mockAuthContextValue: AuthContextType = {
  user: { id: 1, email: 'test@example.com', role: 'admin' } as UserInfo, // Cast to UserInfo
  login: vi.fn(),
  logout: vi.fn(),
  isLoading: false,
  isAuthenticated: true,
  error: null,
  refetchUser: vi.fn().mockResolvedValue(undefined), // Add mock refetchUser
};

// Helper to render with context and router
interface RenderOptions {
  route?: string;
  initialEntries?: string[];
  authValue?: AuthContextType;
}

const renderWithProviders = (
  ui: React.ReactElement,
  {
    route = '/dashboard/settings',
    initialEntries = [route],
    authValue = mockAuthContextValue
  }: RenderOptions = {}
) => {
  // Mock useLocation return value based on initialEntries
  const mockLocation = {
    pathname: route.split('?')[0],
    search: route.includes('?') ? `?${route.split('?')[1]}` : '',
    hash: '',
    state: null,
    key: 'testkey',
  };
  mockUseLocation.mockReturnValue(mockLocation);


  return render(
    <AuthContext.Provider value={authValue}>
      <MemoryRouter initialEntries={initialEntries}>
        <Routes>
          <Route path="/dashboard/settings" element={ui} />
          {/* Add other routes if navigation occurs */}
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
};


describe('SettingsPage', () => {
  beforeEach(() => {
    // Reset mocks before each test
    vi.resetAllMocks();
    // Reset window.location.href mock
    Object.defineProperty(window, 'location', {
      writable: true,
      value: { assign: vi.fn(), href: '' },
    });
    // Reset history mock
    Object.defineProperty(window, 'history', {
        writable: true,
        value: { replaceState: vi.fn() },
    });
  });

  test('renders initial state correctly (not connected)', () => {
    renderWithProviders(<SettingsPage />);

    expect(screen.getByRole('heading', { name: /settings/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /integrations/i })).toBeInTheDocument();
    expect(screen.getByText(/linkedin account/i)).toBeInTheDocument();
    // Use queryByText for potentially absent elements or check state if needed
    expect(screen.getByText(/not connected/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /connect linkedin account/i })).toBeInTheDocument();
  });

  test('calls API and redirects when "Connect" button is clicked', async () => {
    const mockApiGet = vi.mocked(api.get).mockResolvedValue({
      data: { authorization_url: 'https://linkedin.com/auth/mock' },
    });

    renderWithProviders(<SettingsPage />);

    const connectButton = screen.getByRole('button', { name: /connect linkedin account/i });
    fireEvent.click(connectButton);

    // Check loading state
    expect(screen.getByRole('button', { name: /connecting.../i })).toBeDisabled();

    // Wait for API call and redirection
    await waitFor(() => {
      expect(mockApiGet).toHaveBeenCalledWith('/api/v1/linkedin/connect'); // Corrected path
    });
    await waitFor(() => {
      expect(window.location.href).toBe('https://linkedin.com/auth/mock');
    });
  });

   test('displays error message if API call fails', async () => {
    const mockApiGet = vi.mocked(api.get).mockRejectedValue(new Error('Network Error'));

    renderWithProviders(<SettingsPage />);

    const connectButton = screen.getByRole('button', { name: /connect linkedin account/i });
    fireEvent.click(connectButton);

    await waitFor(() => {
      expect(mockApiGet).toHaveBeenCalledWith('/api/v1/linkedin/connect'); // Corrected path
    });

    // Check for error message
    expect(await screen.findByText(/error initiating connection: network error/i)).toBeInTheDocument();
    // Button should be enabled again
    expect(screen.getByRole('button', { name: /connect linkedin account/i })).not.toBeDisabled();
  });

  test('displays success message and connected status on successful callback', async () => { // Made async
    // Mock refetchUser being called
    const mockRefetch = vi.fn().mockResolvedValue(undefined);
    // Ensure the updated user object matches UserInfo structure
    const updatedUser: UserInfo = {
        id: 1,
        email: 'test@example.com',
        role: 'admin',
        linkedin_id: 'mock-li-id' // Add linkedin_id
    };
    const authValueWithRefetch = {
        ...mockAuthContextValue,
        user: updatedUser, // Use the fully defined updated user
        refetchUser: mockRefetch
    };


    renderWithProviders(<SettingsPage />, {
        route: '/dashboard/settings?linkedin_status=success',
        authValue: authValueWithRefetch // Use the context with the mocked refetch and updated user
    });

    expect(screen.getByText(/linkedin account connected successfully!/i)).toBeInTheDocument();
    // Wait for refetch to be called
    await waitFor(() => {
        expect(mockRefetch).toHaveBeenCalled();
    });
    // Status should update based on the new user object provided by the context after refetch
    expect(screen.getByText(/connected/i)).toBeInTheDocument();
    // Connect button should not be present
    expect(screen.queryByRole('button', { name: /connect linkedin account/i })).not.toBeInTheDocument();
    // Check if history.replaceState was called to clean URL
    expect(window.history.replaceState).toHaveBeenCalled();
  });

  test('displays error message on failed callback', () => {
    renderWithProviders(<SettingsPage />, { route: '/dashboard/settings?linkedin_status=error&detail=Invalid+code' });

    expect(screen.getByText(/failed to connect linkedin account: invalid code/i)).toBeInTheDocument();
    // Should show not connected status and button
    expect(screen.getByText(/not connected/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /connect linkedin account/i })).toBeInTheDocument();
     // Check if history.replaceState was called to clean URL
    expect(window.history.replaceState).toHaveBeenCalled();
  });

  // TODO: Add test for checking initial connected status based on user context
  // TODO: Add test for disconnect functionality when implemented
});
