import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ClientProfile, ClientProfileCreate, ClientProfileUpdate } from '../../services/clients';

// Define separate types for form state to avoid confusion
interface ClientProfileData {
  company_name: string;
  industry: string;
  website?: string;
  linkedin_url?: string;
  description?: string;
  logo_url?: string;
  is_active: boolean;
}
interface UserData {
  email: string;
  password?: string; // Optional for edit mode display, required for create
  full_name?: string;
}
type ClientFormState = UserData & ClientProfileData;


interface ClientFormProps {
  client?: ClientProfile & { user?: { email: string, full_name?: string } }; // Include user details if editing
  onSubmit: (data: ClientProfileCreate | ClientProfileUpdate) => Promise<void>;
  isEdit?: boolean;
}

const ClientForm: React.FC<ClientFormProps> = ({ 
  client, 
  onSubmit, 
  isEdit = false 
}) => {
  const navigate = useNavigate();
  
  // Initialize state with all fields defined in ClientFormState
  const [formData, setFormData] = useState<ClientFormState>({
    email: '',
    password: '', // Keep password in state, but only submit for create
    full_name: '',
    company_name: '',
    industry: '',
    website: '',
    linkedin_url: '',
    description: '',
    logo_url: '',
    is_active: true, // Default to active
  });
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize form 
  useEffect(() => {
    if (client && isEdit) {
      // Pre-fill for edit mode (excluding password)
      setFormData({
        email: client.user?.email || '', // Display email if available
        password: '', // Never pre-fill password
        full_name: client.user?.full_name || '', // Display name if available
        company_name: client.company_name,
        industry: client.industry,
        website: client.website || '',
        linkedin_url: client.linkedin_url || '',
        description: client.description || '',
        logo_url: client.logo_url || '',
        is_active: client.is_active ?? true,
      });
    } else {
       // Reset form for create mode (ensure all fields are reset)
       setFormData({
         email: '', password: '', full_name: '',
         company_name: '', industry: '', website: '', linkedin_url: '',
         description: '', logo_url: '', is_active: true,
       });
    }
  }, [client, isEdit]);

  // Handle form input changes
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      let submitData: ClientProfileCreate | ClientProfileUpdate;
      
      if (isEdit) {
        // For update, only send profile fields that exist in ClientProfileUpdate
        const updatePayload: ClientProfileUpdate = {
          company_name: formData.company_name || undefined, // Send undefined if empty string
          industry: formData.industry || undefined,
          website: formData.website || undefined, 
          linkedin_url: formData.linkedin_url || undefined,
          description: formData.description || undefined,
          logo_url: formData.logo_url || undefined,
          is_active: formData.is_active,
        };
         // Remove undefined keys before submitting
         Object.keys(updatePayload).forEach(key => updatePayload[key as keyof ClientProfileUpdate] === undefined && delete updatePayload[key as keyof ClientProfileUpdate]);
         submitData = updatePayload;

      } else {
         // For create, ensure all required fields for ClientProfileCreate are present
         if (!formData.email || !formData.password || !formData.company_name || !formData.industry) {
             throw new Error("Email, Password, Company Name, and Industry are required.");
         }
         // Construct the ClientProfileCreate payload
         // Ensure password is not undefined/empty before sending
         const createPayload: ClientProfileCreate = {
           email: formData.email,
           password: formData.password as string, // Assert password is not undefined here
           full_name: formData.full_name || formData.email, 
           company_name: formData.company_name,
           industry: formData.industry,
           website: formData.website || undefined,
           linkedin_url: formData.linkedin_url || undefined,
           description: formData.description || undefined,
           logo_url: formData.logo_url || undefined,
           is_active: formData.is_active ?? true,
         };
         submitData = createPayload;
      }
      
      await onSubmit(submitData);
      // Navigate only on success
      navigate('/admin/clients'); 
    } catch (err: any) {
      console.error('Form submission error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to save client. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="p-4 mb-4 text-sm text-red-700 bg-red-100 rounded-lg border border-red-300" role="alert">
          {error}
        </div>
      )}
      
      {/* User Fields (only show email/name in edit, password only in create) */}
      {isEdit ? (
         <div>
            <label htmlFor="email" className="form-label">User Email</label>
            <input 
               type="email" id="email" name="email" 
               value={formData.email || ''} 
               readOnly 
               className="form-input bg-gray-100 cursor-not-allowed" 
            />
             <label htmlFor="full_name" className="form-label mt-4">Full Name</label>
             <input 
               type="text" id="full_name" name="full_name" 
               value={formData.full_name || ''} 
               readOnly 
               className="form-input bg-gray-100 cursor-not-allowed" 
             />
         </div>
      ) : (
         <>
           <h3 className="text-lg font-medium leading-6 text-gray-900 border-b pb-2 mb-4">Client User Details</h3>
           <div>
             <label htmlFor="full_name" className="form-label">Full Name</label>
             <input
               type="text" id="full_name" name="full_name"
               value={formData.full_name || ''} onChange={handleChange}
               className="form-input" placeholder="e.g., John Doe"
             />
           </div>
           <div>
             <label htmlFor="email" className="form-label">Email <span className="text-red-600">*</span></label>
             <input
               type="email" id="email" name="email"
               value={formData.email || ''} onChange={handleChange} required
               className="form-input" placeholder="client@company.com"
             />
           </div>
           <div>
             <label htmlFor="password" className="form-label">Initial Password <span className="text-red-600">*</span></label>
             <input
               type="password" id="password" name="password"
               value={formData.password || ''} onChange={handleChange} required
               className="form-input" placeholder="Enter a secure password"
             />
              <p className="mt-1 text-xs text-gray-500">Client can change this later.</p>
           </div>
            <h3 className="text-lg font-medium leading-6 text-gray-900 border-b pb-2 mb-4 pt-6">Company Details</h3>
         </>
      )}
      
      {/* Company name (always shown) */}
      <div>
        <label htmlFor="company_name" className="form-label">Company Name <span className="text-red-600">*</span></label>
        <input
          type="text" id="company_name" name="company_name"
          value={formData.company_name || ''} onChange={handleChange} required
          className="form-input"
        />
      </div>
      
      {/* Industry */}
      <div>
        <label htmlFor="industry" className="form-label">Industry <span className="text-red-600">*</span></label>
        <input
          type="text" id="industry" name="industry"
          value={formData.industry || ''} onChange={handleChange} required
          className="form-input"
        />
      </div>
      
      {/* Website */}
      <div>
        <label htmlFor="website" className="form-label">Website</label>
        <input
          type="url" id="website" name="website"
          value={formData.website || ''} onChange={handleChange}
          placeholder="https://example.com" className="form-input"
        />
      </div>
      
      {/* LinkedIn URL */}
      <div>
        <label htmlFor="linkedin_url" className="form-label">LinkedIn URL</label>
        <input
          type="url" id="linkedin_url" name="linkedin_url"
          value={formData.linkedin_url || ''} onChange={handleChange}
          placeholder="https://linkedin.com/company/example" className="form-input"
        />
      </div>
      
      {/* Description */}
      <div>
        <label htmlFor="description" className="form-label">Description</label>
        <textarea
          id="description" name="description"
          value={formData.description || ''} onChange={handleChange}
          rows={4} className="form-input"
        />
      </div>
      
      {/* Logo URL */}
      <div>
        <label htmlFor="logo_url" className="form-label">Logo URL</label>
        <input
          type="url" id="logo_url" name="logo_url"
          value={formData.logo_url || ''} onChange={handleChange}
          placeholder="https://example.com/logo.png" className="form-input"
        />
      </div>
      
      {/* Active status */}
      <div className="flex items-center">
        <input
          type="checkbox" id="is_active" name="is_active"
          checked={formData.is_active ?? true} // Default to true if undefined
          onChange={handleChange}
          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
        />
        <label htmlFor="is_active" className="ml-3 block text-sm font-medium text-gray-700">
          Client is Active
        </label>
      </div>
      
      {/* Form actions */}
      <div className="flex justify-end space-x-3 pt-5 border-t border-gray-200">
        <button
          type="button"
          onClick={() => navigate('/admin/clients')}
          className="btn btn-secondary" // Use new style
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={loading}
          className="btn btn-primary" // Use new style
        >
          {loading ? 'Saving...' : isEdit ? 'Update Client' : 'Create Client'}
        </button>
      </div>
    </form>
  );
};

export default ClientForm;
