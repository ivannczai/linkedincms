// Remove unused React import
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react'; // Remove unused fireEvent
import userEvent from '@testing-library/user-event';
import ContentView from './ContentView';
import { Content, ContentStatus } from '../../services/contents';
import * as contentService from '../../services/contents';
import { useAuth } from '../../context/AuthContext';

// Mock the content service
vi.mock('../../services/contents', () => ({
  __esModule: true,
  default: {
    submitForApproval: vi.fn(),
    approve: vi.fn(),
    publish: vi.fn(),
    requestRevision: vi.fn(),
  },
  ContentStatus: {
    DRAFT: 'DRAFT',
    PENDING_APPROVAL: 'PENDING_APPROVAL',
    REVISION_REQUESTED: 'REVISION_REQUESTED',
    APPROVED: 'APPROVED',
    PUBLISHED: 'PUBLISHED',
  },
}));

// Mock the auth context
vi.mock('../../context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

// Mock the markdown preview component
vi.mock('../common/MarkdownPreview', () => ({
  __esModule: true,
  default: ({ content }: any) => <div data-testid="markdown-preview">{content}</div>,
}));

describe('ContentView', () => {
  const mockContent: Content = {
    id: 1,
    client_id: 2,
    title: 'Test Content',
    idea: 'Test idea',
    angle: 'Test angle',
    content_body: '# Test Content\n\nThis is a test content.',
    status: ContentStatus.DRAFT,
    due_date: '2025-05-01',
    is_active: true,
  review_comment: null,
  published_at: null, // Add missing field
  created_at: '2025-04-01T12:00:00Z',
  updated_at: null,
};

  const mockContentUpdated = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('renders content details correctly', () => {
    // Mock auth context as admin
    (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
      user: { id: 1, email: 'admin@example.com', role: 'admin' },
    });

    render(<ContentView content={mockContent} onContentUpdated={mockContentUpdated} />);

    // Check content details
    expect(screen.getByText('Test Content')).toBeInTheDocument();
    expect(screen.getByText('Test idea')).toBeInTheDocument();
    expect(screen.getByText('Test angle')).toBeInTheDocument();
    expect(screen.getByTestId('markdown-preview')).toHaveTextContent('# Test Content\n\nThis is a test content.');
  });

  test('shows review comment when present', () => {
    // Mock auth context as admin
    (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
      user: { id: 1, email: 'admin@example.com', role: 'admin' },
    });

    const contentWithComment = {
      ...mockContent,
      status: ContentStatus.REVISION_REQUESTED,
      review_comment: 'Please revise the introduction.',
    };

    render(<ContentView content={contentWithComment} onContentUpdated={mockContentUpdated} />);

    // Check review comment is displayed
    expect(screen.getByText('Revision Requested')).toBeInTheDocument();
    expect(screen.getByText('Please revise the introduction.')).toBeInTheDocument();
  });

  test('shows submit for approval button for admin when content is in DRAFT status', async () => {
    // Mock auth context as admin
    (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
      user: { id: 1, email: 'admin@example.com', role: 'admin' },
    });

    const submitMock = contentService.default.submitForApproval as ReturnType<typeof vi.fn>;
    submitMock.mockResolvedValue({ ...mockContent, status: ContentStatus.PENDING_APPROVAL });

    render(<ContentView content={mockContent} onContentUpdated={mockContentUpdated} />);

    // Check submit button is displayed
    const submitButton = screen.getByText('Submit for Approval');
    expect(submitButton).toBeInTheDocument();

    // Click submit button
    userEvent.click(submitButton);

    // Check if service was called
    await waitFor(() => {
      expect(submitMock).toHaveBeenCalledWith(mockContent.id);
      expect(mockContentUpdated).toHaveBeenCalled();
    });
  });

  test('shows publish button for admin when content is in APPROVED status', async () => {
    // Mock auth context as admin
    (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
      user: { id: 1, email: 'admin@example.com', role: 'admin' },
    });

    const approvedContent = {
      ...mockContent,
      status: ContentStatus.APPROVED,
    };

    const publishMock = contentService.default.publish as ReturnType<typeof vi.fn>;
    publishMock.mockResolvedValue({ ...approvedContent, status: ContentStatus.PUBLISHED });

    render(<ContentView content={approvedContent} onContentUpdated={mockContentUpdated} />);

    // Check publish button is displayed
    const publishButton = screen.getByText('Publish');
    expect(publishButton).toBeInTheDocument();

    // Click publish button
    userEvent.click(publishButton);

    // Check if service was called
    await waitFor(() => {
      expect(publishMock).toHaveBeenCalledWith(approvedContent.id);
      expect(mockContentUpdated).toHaveBeenCalled();
    });
  });

  test('shows approve and request revision buttons for client when content is in PENDING_APPROVAL status', async () => {
    // Mock auth context as client
    (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
      user: { id: 2, email: 'client@example.com', role: 'client' },
    });

    const pendingContent = {
      ...mockContent,
      status: ContentStatus.PENDING_APPROVAL,
    };

    const approveMock = contentService.default.approve as ReturnType<typeof vi.fn>;
    approveMock.mockResolvedValue({ ...pendingContent, status: ContentStatus.APPROVED });

    render(<ContentView content={pendingContent} onContentUpdated={mockContentUpdated} />);

    // Check approve and request revision buttons are displayed
    const approveButton = screen.getByText('Approve');
    const revisionButton = screen.getByText('Request Revision');
    expect(approveButton).toBeInTheDocument();
    expect(revisionButton).toBeInTheDocument();

    // Click approve button
    userEvent.click(approveButton);

    // Check if service was called
    await waitFor(() => {
      expect(approveMock).toHaveBeenCalledWith(pendingContent.id);
      expect(mockContentUpdated).toHaveBeenCalled();
    });
  });

  test('allows client to request revision with comment', async () => {
    // Mock auth context as client
    (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
      user: { id: 2, email: 'client@example.com', role: 'client' },
    });

    const pendingContent = {
      ...mockContent,
      status: ContentStatus.PENDING_APPROVAL,
    };

    const revisionMock = contentService.default.requestRevision as ReturnType<typeof vi.fn>;
    revisionMock.mockResolvedValue({
      ...pendingContent,
      status: ContentStatus.REVISION_REQUESTED,
      review_comment: 'Please improve the introduction.',
    });

    render(<ContentView content={pendingContent} onContentUpdated={mockContentUpdated} />);

    // Click request revision button
    const revisionButton = screen.getByText('Request Revision');
    userEvent.click(revisionButton);

    // Check if comment form is displayed
    const commentTextarea = await screen.findByLabelText('Revision Comments');
    expect(commentTextarea).toBeInTheDocument();

    // Enter comment and submit
    userEvent.type(commentTextarea, 'Please improve the introduction.');
    const submitButton = screen.getByText('Submit Revision Request');
    userEvent.click(submitButton);

    // Check if service was called with correct parameters
    await waitFor(() => {
      expect(revisionMock).toHaveBeenCalledWith(pendingContent.id, 'Please improve the introduction.');
      expect(mockContentUpdated).toHaveBeenCalled();
    });
  });

  test('handles error during status change', async () => {
    // Mock auth context as admin
    (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
      user: { id: 1, email: 'admin@example.com', role: 'admin' },
    });

    const submitMock = contentService.default.submitForApproval as ReturnType<typeof vi.fn>;
    submitMock.mockRejectedValue(new Error('API error'));

    render(<ContentView content={mockContent} onContentUpdated={mockContentUpdated} />);

    // Click submit button
    const submitButton = screen.getByText('Submit for Approval');
    userEvent.click(submitButton);

    // Check if error message is displayed
    await waitFor(() => {
      expect(screen.getByText(/Failed to submit content/i)).toBeInTheDocument();
    });
  });
});
