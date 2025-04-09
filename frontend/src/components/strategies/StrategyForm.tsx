import React, { useState, useEffect } from 'react';
import { Strategy, StrategyCreate, StrategyUpdate } from '../../services/strategies';
// Removed MarkdownPreview import
import RichTextEditor from '../common/RichTextEditor'; // Import RichTextEditor

interface StrategyFormProps {
  strategy?: Strategy;
  clientId?: number; // Make clientId optional as it might not be needed if strategy exists
  onSubmit: (data: StrategyCreate | StrategyUpdate) => Promise<void>;
  isEdit?: boolean;
  onCancel?: () => void;
}

// Define a type for the form state, excluding client_id initially
type StrategyFormData = Omit<StrategyUpdate, 'client_id'> & { title: string; details: string };

const StrategyForm: React.FC<StrategyFormProps> = ({
  strategy,
  clientId,
  onSubmit,
  isEdit = false,
  onCancel,
}) => {
  // Initialize state with common fields
  const [formData, setFormData] = useState<StrategyFormData>({
    title: '',
    details: '<p></p>', // Initialize with empty paragraph for Tiptap
    is_active: true,
  });

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  // Removed previewMode state

  // Update form data when strategy or mode changes
  useEffect(() => {
    if (strategy && isEdit) {
      setFormData({
        title: strategy.title,
        // Ensure existing details (potentially Markdown) are loaded.
        // Tiptap handles basic conversion. Initialize with empty paragraph if null/empty.
        details: strategy.details || '<p></p>',
        is_active: strategy.is_active ?? true, // Ensure default
      });
    } else {
       // Reset for create mode
       setFormData({
         title: '',
         details: '<p></p>', // Default empty paragraph
         is_active: true,
       });
    }
  }, [strategy, isEdit]);

  // Handle form input changes (for title and is_active)
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement> // Only for input elements now
  ) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  // Handle RichTextEditor changes
  const handleDetailsChange = (htmlValue: string) => {
    setFormData(prev => ({
      ...prev,
      details: htmlValue,
    }));
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Basic check if editor content is effectively empty
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = formData.details;
    const isDetailsEmpty = tempDiv.textContent?.trim().length === 0;

    if (isDetailsEmpty) {
        setError('Strategy Details cannot be empty.');
        setLoading(false);
        return;
    }

    try {
       let submitData: StrategyCreate | StrategyUpdate;
       if (isEdit) {
          // For update, send updated fields including HTML details
          submitData = {
             title: formData.title,
             details: formData.details, // Send HTML
             is_active: formData.is_active,
          };
       } else {
          // For create, ensure required fields are present
          if (!formData.title || !formData.details || clientId === undefined) {
             throw new Error("Title, Details, and Client ID are required for creation.");
          }
          // Construct StrategyCreate payload with HTML details
          submitData = {
             client_id: clientId,
             title: formData.title,
             details: formData.details, // Send HTML
             is_active: formData.is_active ?? true,
          };
       }
      // IMPORTANT: Backend needs to sanitize this HTML 'details' field before saving!
      await onSubmit(submitData);
      // Let the parent component handle navigation or state changes on success
    } catch (err: any) {
      console.error('Form submission error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to save strategy.');
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

      {/* Title */}
      <div>
        <label htmlFor="title" className="form-label">
          Strategy Title <span className="text-red-600">*</span>
        </label>
        <input
          type="text" id="title" name="title"
          value={formData.title || ''} onChange={handleChange} required
          className="form-input"
        />
      </div>

      {/* Details (Rich Text Editor) */}
      <div>
        <label htmlFor="details_editor" className="form-label mb-2">
           Details <span className="text-red-600">*</span>
        </label>
        <RichTextEditor
           id="details_editor"
           value={formData.details}
           onChange={handleDetailsChange}
           minHeight={250} // Adjust height as needed
           required // Pass required for basic validation
        />
      </div>

      {/* Active status */}
      <div className="flex items-center">
        <input
          type="checkbox" id="is_active" name="is_active"
          checked={formData.is_active ?? true} onChange={handleChange}
          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
        />
        <label htmlFor="is_active" className="ml-3 block text-sm font-medium text-gray-700">
          Strategy is Active
        </label>
      </div>

      {/* Form actions */}
      <div className="flex justify-end space-x-3 pt-5 border-t border-gray-200">
         {/* Add Cancel button if onCancel prop is provided */}
         {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="btn btn-secondary"
            >
              Cancel
            </button>
         )}
        <button
          type="submit"
          disabled={loading}
          className="btn btn-primary"
        >
          {loading ? 'Saving...' : isEdit ? 'Update Strategy' : 'Create Strategy'}
        </button>
      </div>
    </form>
  );
};

export default StrategyForm;
