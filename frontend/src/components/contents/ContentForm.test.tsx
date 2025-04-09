// Remove unused React import
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import ContentForm from './ContentForm';
import { Content, ContentStatus } from '../../services/contents';
import * as contentService from '../../services/contents';
import { describe, test, expect, beforeEach, vi } from 'vitest';

// Mock the content service
vi.mock('../../services/contents', () => ({
  __esModule: true,
  default: {
    create: vi.fn(),
    update: vi.fn(),
  },
  ContentStatus: {
    DRAFT: 'DRAFT',
    PENDING_APPROVAL: 'PENDING_APPROVAL',
    REVISION_REQUESTED: 'REVISION_REQUESTED',
    APPROVED: 'APPROVED',
    PUBLISHED: 'PUBLISHED',
  },
}));

// Mock the useNavigate hook
vi.mock('react-router-dom', () => ({
  ...vi.importActual('react-router-dom'),
  useNavigate: () => vi.fn(),
}));

// Mock the markdown components
vi.mock('../common/MarkdownEditor', () => ({
  __esModule: true,
  default: ({ value, onChange, id, required }: any) => (
    <textarea
      data-testid="markdown-editor"
      id={id}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      required={required}
    />
  ),
}));

vi.mock('../common/MarkdownPreview', () => ({
  __esModule: true,
  default: ({ content }: any) => <div data-testid="markdown-preview">{content}</div>,
}));

describe('ContentForm', () => {
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

  const mockSubmit = vi.fn();
  const mockCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('renders empty form in create mode', () => {
    render(
      <BrowserRouter>
        <ContentForm clientId={2} onSubmit={mockSubmit} onCancel={mockCancel} />
      </BrowserRouter>
    );

    // Check form title
    expect(screen.getByText('Create New Content Piece')).toBeInTheDocument();

    // Check form fields
    expect(screen.getByLabelText(/Title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Idea/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Angle/i)).toBeInTheDocument();
    expect(screen.getByTestId('markdown-editor')).toBeInTheDocument();
    expect(screen.getByLabelText(/Due Date/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Active/i)).toBeInTheDocument();

    // Check buttons
    expect(screen.getByRole('button', { name: /Cancel/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Create Content/i })).toBeInTheDocument();
  });

  test('renders form with content data in edit mode', () => {
    render(
      <BrowserRouter>
        <ContentForm
          content={mockContent}
          isEdit={true}
          onSubmit={mockSubmit}
          onCancel={mockCancel}
        />
      </BrowserRouter>
    );

    // Check form title
    expect(screen.getByText('Edit Content Piece')).toBeInTheDocument();

    // Check form fields have correct values
    expect(screen.getByLabelText(/Title/i)).toHaveValue('Test Content');
    expect(screen.getByLabelText(/Idea/i)).toHaveValue('Test idea');
    expect(screen.getByLabelText(/Angle/i)).toHaveValue('Test angle');
    expect(screen.getByTestId('markdown-editor')).toHaveValue('# Test Content\n\nThis is a test content.');
    expect(screen.getByLabelText(/Due Date/i)).toHaveValue('2025-05-01');
    expect(screen.getByLabelText(/Active/i)).toBeChecked();

    // Check status field is present in edit mode
    expect(screen.getByLabelText(/Status/i)).toBeInTheDocument();

    // Check buttons
    expect(screen.getByRole('button', { name: /Cancel/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Update Content/i })).toBeInTheDocument();
  });

  test('toggles between edit and preview mode', async () => {
    render(
      <BrowserRouter>
        <ContentForm
          content={mockContent}
          isEdit={true}
          onSubmit={mockSubmit}
          onCancel={mockCancel}
        />
      </BrowserRouter>
    );

    // Initially in edit mode
    expect(screen.getByTestId('markdown-editor')).toBeVisible();
    expect(screen.queryByTestId('markdown-preview')).not.toBeInTheDocument();

    // Switch to preview mode
    const previewButton = screen.getByRole('button', { name: /Preview/i });
    userEvent.click(previewButton);

    // Check preview content
    await waitFor(() => {
      expect(screen.getByTestId('markdown-preview')).toBeInTheDocument();
      expect(screen.getByTestId('markdown-editor')).not.toBeVisible();
    });

    // Switch back to edit mode
    const editButton = screen.getByRole('button', { name: /Edit/i });
    userEvent.click(editButton);

    // Check edit mode is back
    await waitFor(() => {
      expect(screen.getByTestId('markdown-editor')).toBeVisible();
      expect(screen.queryByTestId('markdown-preview')).not.toBeInTheDocument();
    });
  });

  test('submits form with correct data in create mode', async () => {
    const createMock = contentService.default.create as ReturnType<typeof vi.fn>;
    createMock.mockResolvedValue({ ...mockContent, id: 3 });

    render(
      <BrowserRouter>
        <ContentForm clientId={2} onSubmit={mockSubmit} onCancel={mockCancel} />
      </BrowserRouter>
    );

    // Fill out form
    userEvent.type(screen.getByLabelText(/Title/i), 'New Content');
    userEvent.type(screen.getByLabelText(/Idea/i), 'New idea');
    userEvent.type(screen.getByLabelText(/Angle/i), 'New angle');
    userEvent.type(screen.getByTestId('markdown-editor'), '# New Content\n\nThis is new content.');
    fireEvent.change(screen.getByLabelText(/Due Date/i), { target: { value: '2025-06-01' } });

    // Submit form
    const submitButton = screen.getByRole('button', { name: /Create Content/i });
    userEvent.click(submitButton);

    // Check if service was called with correct data
    await waitFor(() => {
      expect(createMock).toHaveBeenCalledWith({
        client_id: 2,
        title: 'New Content',
        idea: 'New idea',
        angle: 'New angle',
        content_body: '# New Content\n\nThis is new content.',
        due_date: '2025-06-01',
        is_active: true,
      });
    });

    // Check if onSubmit was called
    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalled();
    });
  });

  test('submits form with correct data in edit mode', async () => {
    const updateMock = contentService.default.update as ReturnType<typeof vi.fn>;
    updateMock.mockResolvedValue({ ...mockContent, title: 'Updated Content' });

    render(
      <BrowserRouter>
        <ContentForm
          content={mockContent}
          isEdit={true}
          onSubmit={mockSubmit}
          onCancel={mockCancel}
        />
      </BrowserRouter>
    );

    // Update title
    fireEvent.change(screen.getByLabelText(/Title/i), { target: { value: 'Updated Content' } });

    // Submit form
    const submitButton = screen.getByRole('button', { name: /Update Content/i });
    userEvent.click(submitButton);

    // Check if service was called with correct data
    await waitFor(() => {
      expect(updateMock).toHaveBeenCalledWith(1, {
        title: 'Updated Content',
        idea: 'Test idea',
        angle: 'Test angle',
        content_body: '# Test Content\n\nThis is a test content.',
        due_date: '2025-05-01',
        is_active: true,
        status: ContentStatus.DRAFT,
      });
    });

    // Check if onSubmit was called
    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalled();
    });
  });

  test('calls onCancel when cancel button is clicked', () => {
    render(
      <BrowserRouter>
        <ContentForm clientId={2} onSubmit={mockSubmit} onCancel={mockCancel} />
      </BrowserRouter>
    );

    const cancelButton = screen.getByRole('button', { name: /Cancel/i });
    userEvent.click(cancelButton);

    expect(mockCancel).toHaveBeenCalled();
  });

  test('shows error message on submission failure', async () => {
    const createMock = contentService.default.create as ReturnType<typeof vi.fn>;
    createMock.mockRejectedValue(new Error('Submission failed'));

    render(
      <BrowserRouter>
        <ContentForm clientId={2} onSubmit={mockSubmit} onCancel={mockCancel} />
      </BrowserRouter>
    );

    // Fill out form minimally
    userEvent.type(screen.getByLabelText(/Title/i), 'New Content');
    userEvent.type(screen.getByLabelText(/Idea/i), 'New idea');
    userEvent.type(screen.getByLabelText(/Angle/i), 'New angle');
    userEvent.type(screen.getByTestId('markdown-editor'), 'Content body');

    // Submit form
    const submitButton = screen.getByRole('button', { name: /Create Content/i });
    userEvent.click(submitButton);

    // Check error message
    await waitFor(() => {
      expect(screen.getByText(/Failed to save content piece/i)).toBeInTheDocument();
    });
  });
});
