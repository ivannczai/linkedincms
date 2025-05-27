import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { vi } from 'vitest';
import ClientContentViewPage from './ClientContentViewPage';
import { AuthContext, AuthContextType } from '../../context/AuthContext';
import contentService, { Content, ContentStatus } from '../../services/contents'; // Import Content type and ContentStatus enum
import { UserInfo } from '../../services/auth'; // Import UserInfo type

// Mock the contentService
vi.mock('../../services/contents');

// Mock content data
const mockContent: Content = { // Add Content type annotation
    id: 1,
    client_id: 10,
    title: 'Test Content Title',
    idea: 'Test Idea',
    angle: 'Test Angle',
    content_body: '## Test Body\n\nThis is markdown content.',
    status: ContentStatus.APPROVED, // Use enum member
    due_date: new Date().toISOString(),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    client_rating: 4.5,
    review_comment: null,
    published_at: null,
    scheduled_at: null,
    is_active: true, // Add missing is_active property
};

// Mock useAuth context for a client user
const mockClientAuthContextValue: AuthContextType = {
    user: {
        id: 1,
        email: 'client@example.com',
        role: 'client',
        client_id: 10,
        // Add missing properties required by UserInfo
        full_name: 'Test Client User',
        is_active: true,
    } as UserInfo, // Cast to UserInfo
    login: vi.fn(),
    logout: vi.fn(),
    isLoading: false,
    isAuthenticated: true,
    error: null,
    refetchUser: vi.fn().mockResolvedValue(undefined),
};

// Helper to render with context and router, setting initial route
const renderWithProviders = (
    ui: React.ReactElement,
    { route = '/client/contents/1', path = '/client/contents/:contentId', authValue = mockClientAuthContextValue } = {}
) => {
    window.history.pushState({}, 'Test page', route);
    return render(
        <AuthContext.Provider value={authValue}>
            <MemoryRouter initialEntries={[route]}>
                <Routes>
                    <Route path={path} element={ui} />
                </Routes>
            </MemoryRouter>
        </AuthContext.Provider>
    );
};

describe('ClientContentViewPage', () => {
    beforeEach(() => {
        vi.resetAllMocks();
        // Mock the API call to get content by ID
        vi.mocked(contentService.getById).mockResolvedValue(mockContent);
    });

    test('renders content details correctly for a client', async () => {
        renderWithProviders(<ClientContentViewPage />);

        // Wait for API call and check content rendering
        await waitFor(() => {
            expect(contentService.getById).toHaveBeenCalledWith('1'); // ID from route param
        });

        expect(await screen.findByRole('heading', { name: /test content title/i })).toBeInTheDocument();
        expect(screen.getByText(/test idea/i)).toBeInTheDocument();
        expect(screen.getByText(/test angle/i)).toBeInTheDocument();
        // Check for markdown rendering (e.g., presence of h2)
        expect(await screen.findByRole('heading', { level: 2, name: /test body/i })).toBeInTheDocument();
        expect(screen.getByText(/this is markdown content/i)).toBeInTheDocument();
        // Check for status badge
        expect(screen.getByText(/approved/i)).toBeInTheDocument();
        // Check for rating display
        expect(screen.getByText(/your rating:/i)).toBeInTheDocument();
        // Check action buttons (Approve/Revise should NOT be visible to client)
        expect(screen.queryByRole('button', { name: /approve/i })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /request revision/i })).not.toBeInTheDocument();
        // Check Mark as Posted button IS visible
        expect(screen.getByRole('button', { name: /mark as posted/i })).toBeInTheDocument();
    });

    test('displays loading state initially', () => {
        // Mock API call to be pending, explicitly typing the promise
        vi.mocked(contentService.getById).mockImplementation(() => new Promise<Content>(() => {}));
        renderWithProviders(<ClientContentViewPage />);
        expect(screen.getByText(/loading content/i)).toBeInTheDocument();
    });

    test('displays error message on fetch failure', async () => {
        // Mock API call to reject
        vi.mocked(contentService.getById).mockRejectedValue(new Error('Failed to fetch'));
        renderWithProviders(<ClientContentViewPage />);
        expect(await screen.findByText(/failed to load content details/i)).toBeInTheDocument();
    });

    // Add more tests:
    // - Test clicking "Mark as Posted" button
    // - Test rating submission (if rating input is added here)
});
