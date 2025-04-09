// Remove unused React import
import { render, screen, waitFor } from '@testing-library/react'; // Remove unused fireEvent
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import ClientForm from './ClientForm';
import { ClientProfile } from '../../services/clients'; // Remove unused ClientProfileCreate, ClientProfileUpdate
import * as clientService from '../../services/clients'; 
import { describe, test, expect, beforeEach, vi } from 'vitest';

// Mock the client service
vi.mock('../../services/clients', () => ({
  __esModule: true,
  default: {
    create: vi.fn(),
    update: vi.fn(),
  },
  // Need to export the types as well if they are used directly in tests, 
  // but it's better to import them from the actual module like above.
}));

// Mock the useNavigate hook
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom') as object;
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('ClientForm', () => {
  // Mock data for editing
  const mockClient: ClientProfile & { user: { email: string, full_name: string } } = {
    id: 1,
    user_id: 10,
    company_name: 'Existing Co',
    industry: 'Existing Industry',
    website: 'https://existing.com',
    linkedin_url: 'https://linkedin.com/company/existing',
    description: 'Existing description',
    logo_url: 'https://existing.com/logo.png',
    is_active: true,
    created_at: '2025-01-01T10:00:00Z',
    updated_at: undefined, // Use undefined instead of null
    user: { // Add mock user data for edit display
        email: 'existing@example.com',
        full_name: 'Existing User'
    }
  };

  const mockSubmit = vi.fn();
  // Remove unused mockCancel

  beforeEach(() => {
    vi.clearAllMocks();
    // Reset mocks before each test
    (clientService.default.create as ReturnType<typeof vi.fn>).mockReset();
    (clientService.default.update as ReturnType<typeof vi.fn>).mockReset();
    mockNavigate.mockReset();
    mockSubmit.mockReset();
  });

  test('renders empty form with user fields in create mode', () => {
    render(
      <BrowserRouter>
        <ClientForm onSubmit={mockSubmit} /> 
      </BrowserRouter>
    );

    expect(screen.getByText('Create New Client')).toBeInTheDocument();
    // Check user fields are present
    expect(screen.getByLabelText(/Full Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Initial Password/i)).toBeInTheDocument();
    // Check profile fields
    expect(screen.getByLabelText(/Company Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Industry/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Active/i)).toBeInTheDocument();
    // Check buttons
    expect(screen.getByRole('button', { name: /Cancel/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Create Client/i })).toBeInTheDocument();
  });

  test('renders form with profile data and read-only user fields in edit mode', () => {
    render(
      <BrowserRouter>
        <ClientForm
          client={mockClient}
          isEdit={true}
          onSubmit={mockSubmit}
        />
      </BrowserRouter>
    );

    expect(screen.getByText('Edit Client')).toBeInTheDocument();
    // Check user fields are present and read-only
    expect(screen.getByLabelText(/User Email/i)).toHaveValue(mockClient.user.email);
    expect(screen.getByLabelText(/User Email/i)).toHaveAttribute('readOnly');
    expect(screen.getByLabelText(/Full Name/i)).toHaveValue(mockClient.user.full_name);
     expect(screen.getByLabelText(/Full Name/i)).toHaveAttribute('readOnly');
    expect(screen.queryByLabelText(/Initial Password/i)).not.toBeInTheDocument(); // Password field hidden
    // Check profile fields
    expect(screen.getByLabelText(/Company Name/i)).toHaveValue(mockClient.company_name);
    expect(screen.getByLabelText(/Industry/i)).toHaveValue(mockClient.industry);
    expect(screen.getByLabelText(/Website/i)).toHaveValue(mockClient.website);
    expect(screen.getByLabelText(/Active/i)).toBeChecked();
    // Check buttons
    expect(screen.getByRole('button', { name: /Cancel/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Update Client/i })).toBeInTheDocument();
  });

  test('submits form with correct data in create mode', async () => {
    const createMock = clientService.default.create as ReturnType<typeof vi.fn>;
    createMock.mockResolvedValue({ ...mockClient, id: 3 }); // Simulate successful creation

    render(
      <BrowserRouter>
        <ClientForm onSubmit={mockSubmit} />
      </BrowserRouter>
    );

    // Fill out form
    await userEvent.type(screen.getByLabelText(/Full Name/i), 'New User');
    await userEvent.type(screen.getByLabelText(/Email/i), 'new.user@company.com');
    await userEvent.type(screen.getByLabelText(/Initial Password/i), 'password123');
    await userEvent.type(screen.getByLabelText(/Company Name/i), 'New Company');
    await userEvent.type(screen.getByLabelText(/Industry/i), 'New Industry');
    await userEvent.type(screen.getByLabelText(/Website/i), 'https://new.com');

    // Submit form
    const submitButton = screen.getByRole('button', { name: /Create Client/i });
    await userEvent.click(submitButton);

    // Check if onSubmit prop was called with correct data
    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledWith({
        email: 'new.user@company.com',
        password: 'password123',
        full_name: 'New User',
        company_name: 'New Company',
        industry: 'New Industry',
        website: 'https://new.com',
        linkedin_url: undefined, // Ensure optional fields are handled
        description: undefined,
        logo_url: undefined,
        is_active: true,
      });
    });
  });

  test('submits form with correct data in edit mode', async () => {
    const updateMock = clientService.default.update as ReturnType<typeof vi.fn>;
    updateMock.mockResolvedValue({ ...mockClient, company_name: 'Updated Co Name' });

    render(
      <BrowserRouter>
        <ClientForm
          client={mockClient}
          isEdit={true}
          onSubmit={mockSubmit}
        />
      </BrowserRouter>
    );

    // Update company name
    const companyInput = screen.getByLabelText(/Company Name/i);
    await userEvent.clear(companyInput);
    await userEvent.type(companyInput, 'Updated Co Name');
    
    // Uncheck active status
    const activeCheckbox = screen.getByLabelText(/Active/i);
    await userEvent.click(activeCheckbox);


    // Submit form
    const submitButton = screen.getByRole('button', { name: /Update Client/i });
    await userEvent.click(submitButton);

    // Check if onSubmit prop was called with correct data (only changed fields)
    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledWith({
        company_name: 'Updated Co Name',
        industry: 'Existing Industry', // Ensure unchanged fields are still there if needed by update schema
        website: 'https://existing.com',
        linkedin_url: 'https://linkedin.com/company/existing',
        description: 'Existing description',
        logo_url: 'https://existing.com/logo.png',
        is_active: false, // Check updated value
      });
    });
  });

  test('calls navigate on cancel button click', async () => {
    render(
      <BrowserRouter>
        <ClientForm onSubmit={mockSubmit} />
      </BrowserRouter>
    );

    const cancelButton = screen.getByRole('button', { name: /Cancel/i });
    await userEvent.click(cancelButton);

    expect(mockNavigate).toHaveBeenCalledWith('/admin/clients');
  });

  test('shows error message on submission failure', async () => {
     const createMock = clientService.default.create as ReturnType<typeof vi.fn>;
     createMock.mockRejectedValue({ response: { data: { detail: 'Email already exists' } } }); // Simulate API error

    render(
      <BrowserRouter>
        <ClientForm onSubmit={mockSubmit} />
      </BrowserRouter>
    );

    // Fill required fields
    await userEvent.type(screen.getByLabelText(/Email/i), 'test@fail.com');
    await userEvent.type(screen.getByLabelText(/Initial Password/i), 'password');
    await userEvent.type(screen.getByLabelText(/Company Name/i), 'Fail Co');
    await userEvent.type(screen.getByLabelText(/Industry/i), 'Failure');

    // Submit form
    const submitButton = screen.getByRole('button', { name: /Create Client/i });
    await userEvent.click(submitButton);

    // Check error message
    await waitFor(() => {
      expect(screen.getByText(/Email already exists/i)).toBeInTheDocument();
    });
     expect(mockSubmit).toHaveBeenCalled(); // onSubmit should still be called
     expect(mockNavigate).not.toHaveBeenCalled(); // Navigate should not happen on error
  });
});
