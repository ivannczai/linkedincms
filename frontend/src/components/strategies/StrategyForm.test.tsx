// Remove unused React import
import { describe, test, expect, vi } from 'vitest'; // Remove unused beforeEach
import { render, screen, waitFor } from '@testing-library/react'; // Remove unused fireEvent
import userEvent from '@testing-library/user-event';
import StrategyForm from './StrategyForm';
import { Strategy } from '../../services/strategies';

// Mock strategy data
const mockStrategy: Strategy = {
  id: 1,
  client_id: 1,
  title: 'Test Strategy',
  details: '# Strategy Title\n\nThis is a **test** strategy with *markdown* content.',
  is_active: true,
  created_at: '2025-04-01T12:00:00Z',
  updated_at: '2025-04-02T12:00:00Z',
};

describe('StrategyForm', () => {
  test('renders empty form in create mode', () => {
    const handleSubmit = vi.fn();
    render(<StrategyForm clientId={1} onSubmit={handleSubmit} />);
    
    // Check form elements
    expect(screen.getByLabelText(/Title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Content Strategy/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Active/i)).toBeInTheDocument();
    
    // Check button text for create mode
    expect(screen.getByRole('button', { name: /Create Strategy/i })).toBeInTheDocument();
  });

  test('renders form with strategy data in edit mode', () => {
    const handleSubmit = vi.fn();
    render(<StrategyForm strategy={mockStrategy} onSubmit={handleSubmit} isEdit={true} />);
    
    // Check form elements have correct values
    expect(screen.getByLabelText(/Title/i)).toHaveValue('Test Strategy');
    expect(screen.getByLabelText(/Content Strategy/i)).toHaveValue(mockStrategy.details);
    expect(screen.getByLabelText(/Active/i)).toBeChecked();
    
    // Check button text for edit mode
    expect(screen.getByRole('button', { name: /Update Strategy/i })).toBeInTheDocument();
  });

  test('toggles between edit and preview mode', async () => {
    const handleSubmit = vi.fn();
    render(<StrategyForm strategy={mockStrategy} onSubmit={handleSubmit} isEdit={true} />);
    
    // Initially in edit mode
    const textarea = screen.getByLabelText(/Content Strategy/i);
    expect(textarea).toBeInTheDocument();
    
    // Switch to preview mode
    const previewButton = screen.getByText(/Preview/i);
    userEvent.click(previewButton);
    
    // Check preview content
    const previewDiv = await screen.findByText('Strategy Title');
    expect(previewDiv).toBeInTheDocument();
    expect(screen.queryByLabelText(/Content Strategy/i)).not.toBeVisible();
    
    // Switch back to edit mode
    const editButton = screen.getByText(/Edit/i);
    userEvent.click(editButton);
    
    // Check edit mode is back
    expect(screen.getByLabelText(/Content Strategy/i)).toBeVisible();
  });

  test('submits form with correct data', async () => {
    const handleSubmit = vi.fn().mockResolvedValue({});
    render(<StrategyForm clientId={1} onSubmit={handleSubmit} />);
    
    // Fill out form
    userEvent.type(screen.getByLabelText(/Title/i), 'New Strategy');
    userEvent.type(screen.getByLabelText(/Content Strategy/i), '# New Content\n\nThis is new content.');
    
    // Submit form
    const submitButton = screen.getByRole('button', { name: /Create Strategy/i });
    userEvent.click(submitButton);
    
    // Check if handleSubmit was called with correct data
    await waitFor(() => {
      expect(handleSubmit).toHaveBeenCalledWith({
        client_id: 1,
        title: 'New Strategy',
        details: '# New Content\n\nThis is new content.',
        is_active: true,
      });
    });
  });

  test('shows loading state during submission', async () => {
    // Create a promise that we can resolve manually
    let resolveSubmit: (value: unknown) => void;
    const submitPromise = new Promise((resolve) => {
      resolveSubmit = resolve;
    });
    
    const handleSubmit = vi.fn().mockImplementation(() => submitPromise);
    render(<StrategyForm clientId={1} onSubmit={handleSubmit} />);
    
    // Fill out form
    userEvent.type(screen.getByLabelText(/Title/i), 'New Strategy');
    
    // Submit form
    const submitButton = screen.getByRole('button', { name: /Create Strategy/i });
    userEvent.click(submitButton);
    
    // Check loading state
    expect(screen.getByText(/Saving.../i)).toBeInTheDocument();
    
    // Resolve the promise
    resolveSubmit!({});
    
    // Check button text is back to normal
    await waitFor(() => {
      expect(screen.queryByText(/Saving.../i)).not.toBeInTheDocument();
    });
  });

  test('shows error message on submission failure', async () => {
    const handleSubmit = vi.fn().mockRejectedValue(new Error('Submission failed'));
    render(<StrategyForm clientId={1} onSubmit={handleSubmit} />);
    
    // Fill out form
    userEvent.type(screen.getByLabelText(/Title/i), 'New Strategy');
    
    // Submit form
    const submitButton = screen.getByRole('button', { name: /Create Strategy/i });
    userEvent.click(submitButton);
    
    // Check error message
    await waitFor(() => {
      expect(screen.getByText(/Failed to save strategy/i)).toBeInTheDocument();
    });
  });
});
