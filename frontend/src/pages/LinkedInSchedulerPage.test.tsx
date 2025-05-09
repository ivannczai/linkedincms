import { render, screen, fireEvent, waitFor } from '@testing-library/react';
// Removed unused BrowserRouter, Route, Routes
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';
import LinkedInSchedulerPage from './LinkedInSchedulerPage';
import { AuthContext, AuthContextType } from '../context/AuthContext';
import { UserInfo } from '../services/auth'; // Import UserInfo from correct source
import api from '../services/api';
import { format } from 'date-fns'; // Import format for date checking

// Mock the api service
vi.mock('../services/api');

// Define type locally for mock data
interface ScheduledLinkedInPostRead {
  id: number;
  user_id: number;
  content_text: string;
  scheduled_at: string; // ISO string format from backend
  status: 'pending' | 'published' | 'failed';
  linkedin_post_id?: string | null;
  error_message?: string | null; // Error message from backend
  created_at: string;
  updated_at: string;
  retry_count?: number; // Include retry_count if needed for display
}


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
const renderWithProviders = (
  ui: React.ReactElement,
  { authValue = mockAuthContextValue } = {}
) => {
  return render(
    <AuthContext.Provider value={authValue}>
      <MemoryRouter> {/* Simple router setup is enough here */}
        {ui}
      </MemoryRouter>
    </AuthContext.Provider>
  );
};

// Mock scheduled posts data
const mockPosts: ScheduledLinkedInPostRead[] = [
  { id: 1, user_id: 1, content_text: 'Post 1 content', scheduled_at: new Date(Date.now() + 3600 * 1000).toISOString(), status: 'pending', created_at: new Date().toISOString(), updated_at: new Date().toISOString(), retry_count: 0 },
  { id: 2, user_id: 1, content_text: 'Post 2 published', scheduled_at: new Date(Date.now() - 3600 * 1000).toISOString(), status: 'published', linkedin_post_id: 'li123', created_at: new Date().toISOString(), updated_at: new Date().toISOString(), retry_count: 0 },
  { id: 3, user_id: 1, content_text: 'Post 3 failed', scheduled_at: new Date(Date.now() - 7200 * 1000).toISOString(), status: 'failed', error_message: 'API Error: 500 - Internal Server Error', created_at: new Date().toISOString(), updated_at: new Date().toISOString(), retry_count: 3 },
];

// Define type for the payload sent to api.post
interface SchedulePayload {
    content_text: string;
    scheduled_at: string;
    user_id: number;
}


describe('LinkedInSchedulerPage', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    // Mock initial fetch
    vi.mocked(api.get).mockResolvedValue({ data: mockPosts });
    // Mock window.confirm for delete tests
    window.confirm = vi.fn(() => true);
  });

  test('renders the form and initial list of scheduled posts including failed status', async () => {
    renderWithProviders(<LinkedInSchedulerPage />);

    // Check form elements
    expect(screen.getByRole('heading', { name: /schedule linkedin post/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/post content/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/schedule date and time/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /schedule post/i })).toBeInTheDocument();

    // Check list heading
    expect(screen.getByRole('heading', { name: /scheduled posts/i })).toBeInTheDocument();

    // Wait for posts to load and check list items
    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/api/v1/linkedin/scheduled');
    });
    expect(await screen.findByText(/post 1 content/i)).toBeInTheDocument();
    expect(await screen.findByText(/post 2 published/i)).toBeInTheDocument();
    expect(await screen.findByText(/post 3 failed/i)).toBeInTheDocument(); // Check failed post
    expect(screen.getByText('pending')).toBeInTheDocument();
    expect(screen.getByText('published')).toBeInTheDocument();
    expect(screen.getByText('failed')).toBeInTheDocument(); // Check failed status badge

    // Check if error message is displayed for the failed post
    const failedPostElement = screen.getByText(/post 3 failed/i).closest('li');
    expect(failedPostElement).toHaveTextContent(/Error: API Error: 500/);
  });

  test('allows scheduling a new post', async () => {
    const mockApiPost = vi.mocked(api.post).mockResolvedValue({ data: {}, status: 201 });
    // Mock fetch after successful post
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockPosts }) // Initial fetch
                      .mockResolvedValueOnce({ data: [...mockPosts, { id: 4, user_id: 1, content_text: 'New scheduled post', scheduled_at: new Date(Date.now() + 7200 * 1000).toISOString(), status: 'pending', created_at: new Date().toISOString(), updated_at: new Date().toISOString(), retry_count: 0 }] }); // Fetch after post

    renderWithProviders(<LinkedInSchedulerPage />);

    // Wait for initial load
    await screen.findByText(/post 1 content/i);

    // Fill form
    const contentInput = screen.getByLabelText(/post content/i);
    const dateTimeInput = screen.getByLabelText(/schedule date and time/i);
    const scheduleButton = screen.getByRole('button', { name: /schedule post/i });

    fireEvent.change(contentInput, { target: { value: 'New scheduled post' } });
    // Set a future date/time for the input (format YYYY-MM-DDTHH:mm)
    const futureDate = new Date(Date.now() + 7200 * 1000); // 2 hours from now
    const futureDateTimeLocal = format(futureDate, "yyyy-MM-dd'T'HH:mm");
    fireEvent.change(dateTimeInput, { target: { value: futureDateTimeLocal } });

    // Submit form
    fireEvent.click(scheduleButton);

    // Check API call
    await waitFor(() => {
      expect(mockApiPost).toHaveBeenCalledWith('/api/v1/linkedin/schedule', expect.objectContaining({
        content_text: 'New scheduled post',
        user_id: 1, // From mockAuthContextValue
        scheduled_at: expect.any(String),
      }));
      const payload = mockApiPost.mock.calls[0][1] as SchedulePayload;
      expect(new Date(payload.scheduled_at).toISOString()).toBe(futureDate.toISOString());
    });

    // Check success message and list update
    expect(await screen.findByText(/post scheduled successfully!/i)).toBeInTheDocument();
    expect(await screen.findByText(/new scheduled post/i)).toBeInTheDocument();
  });

   test('displays error if scheduling fails', async () => {
    vi.mocked(api.post).mockRejectedValue({ response: { data: { detail: 'Token is invalid' } } });
    renderWithProviders(<LinkedInSchedulerPage />);
    await screen.findByText(/post 1 content/i); // Wait for initial load

    fireEvent.change(screen.getByLabelText(/post content/i), { target: { value: 'Fail post' } });
    const futureDate = new Date(Date.now() + 3600 * 1000);
    const futureDateTimeLocal = format(futureDate, "yyyy-MM-dd'T'HH:mm");
    fireEvent.change(screen.getByLabelText(/schedule date and time/i), { target: { value: futureDateTimeLocal } });
    fireEvent.click(screen.getByRole('button', { name: /schedule post/i }));

    expect(await screen.findByText(/failed to schedule post: token is invalid/i)).toBeInTheDocument();
  });

  test('allows cancelling a pending post', async () => {
    const mockApiDelete = vi.mocked(api.delete).mockResolvedValue({});
     // Mock fetch after successful delete (remove post 1)
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockPosts }) // Initial fetch
                      .mockResolvedValueOnce({ data: [mockPosts[1], mockPosts[2]] }); // Posts 2 and 3 remain

    renderWithProviders(<LinkedInSchedulerPage />);

    // Find the cancel button for the first pending post (Post 1)
    const post1Element = await screen.findByText(/post 1 content/i);
    // Use a more specific selector if multiple cancel buttons exist
    const cancelButton = post1Element.closest('li')?.querySelector('button.text-red-600') as HTMLButtonElement;
    expect(cancelButton).toBeInTheDocument();
    fireEvent.click(cancelButton);


    // Confirm deletion (mocked to return true)
    expect(window.confirm).toHaveBeenCalled();

    // Check API call
    await waitFor(() => {
      expect(mockApiDelete).toHaveBeenCalledWith('/api/v1/linkedin/schedule/1');
    });

    // Check success message and list update
    expect(await screen.findByText(/scheduled post cancelled successfully!/i)).toBeInTheDocument();
    expect(screen.queryByText(/post 1 content/i)).not.toBeInTheDocument(); // Post 1 should be gone
    expect(screen.getByText(/post 2 published/i)).toBeInTheDocument(); // Post 2 should remain
    expect(screen.getByText(/post 3 failed/i)).toBeInTheDocument(); // Post 3 should remain
  });

});
