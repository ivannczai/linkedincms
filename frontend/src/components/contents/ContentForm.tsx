import React, { useState, useEffect } from 'react';
import { Content, ContentCreateInput, ContentUpdateInput, ContentStatus } from '../../services/contents';
import contentService from '../../services/contents';
import { useNavigate } from 'react-router-dom';
import { ClientProfile } from '../../services/clients';

interface ContentFormProps {
  clientId?: number; // Provided when creating content for a specific client
  clients?: ClientProfile[]; // Provided when creating content globally (admin selects client)
  content?: Content;
  isEdit?: boolean;
  onSubmit?: (content: Content) => void;
  onCancel?: () => void;
}

const ContentForm: React.FC<ContentFormProps> = ({
  clientId: initialClientId, // Rename prop to avoid conflict with state
  clients, // Receive clients list
  content,
  isEdit = false,
  onSubmit,
  onCancel,
}) => {
  const navigate = useNavigate();
  // State for selected client ID if creating globally
  const [selectedClientId, setSelectedClientId] = useState<number | undefined>(initialClientId);
  const [title, setTitle] = useState(content?.title || '');
  const [idea, setIdea] = useState(content?.idea || '');
  const [angle, setAngle] = useState(content?.angle || '');
  // Initialize contentBody with an empty paragraph tag for Tiptap if creating new
  const [contentBody, setContentBody] = useState(content?.content_body || '');
  const [dueDate, setDueDate] = useState(content?.due_date || '');
  const [isActive, setIsActive] = useState(content?.is_active ?? true);
  const [status, setStatus] = useState<ContentStatus>(content?.status || ContentStatus.DRAFT);
  // Removed showPreview state
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (content) {
      setTitle(content.title);
      setIdea(content.idea);
      setAngle(content.angle);
      // Ensure existing content (potentially Markdown) is loaded,
      // Tiptap will handle basic Markdown conversion on load if needed,
      // but ideally, this should be HTML after migration.
      // If content is empty, initialize with empty paragraph for Tiptap.
      setContentBody(content.content_body || '');
      setDueDate(content.due_date || '');
      setIsActive(content.is_active);
      setStatus(content.status);
    }
  }, [content]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    // Basic check if editor content is effectively empty (ignoring empty tags)
    // This relies on Tiptap usually having at least <p></p>
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = contentBody;
    const isContentEmpty = tempDiv.textContent?.trim().length === 0;

    if (isContentEmpty) {
        setError('Content Body cannot be empty.');
        setLoading(false);
        return;
    }


    try {
      // IMPORTANT: Backend needs to sanitize this HTML contentBody before saving!
      const formData: ContentCreateInput | ContentUpdateInput = {
        title,
        idea,
        angle,
        content_body: contentBody, // Send HTML
        is_active: isActive,
      };

      // Determine the client ID to use for creation
      const finalClientId = isEdit ? content?.client_id : selectedClientId;

      if (!isEdit && finalClientId) {
        (formData as ContentCreateInput).client_id = finalClientId;
      } else if (!isEdit && !finalClientId) {
         setError('Please select a client.');
         setLoading(false);
          return; // Stop submission if client not selected in global create mode
       }
 
       if (isEdit && content) {
         formData.status = status;
       }

      let savedContent: Content;
      if (isEdit && content) {
        savedContent = await contentService.update(content.id, formData as ContentUpdateInput);
        setSuccess('Content piece updated successfully');
      } else {
        savedContent = await contentService.create(formData as ContentCreateInput);
        setSuccess('Content piece created successfully');
      }

      if (onSubmit) {
        onSubmit(savedContent);
      } else {
        // Wait a bit to show the success message before navigating
        setTimeout(() => {
          navigate(`/admin/clients/${savedContent.client_id}/contents/${savedContent.id}`);
        }, 1500);
      }
    } catch (err) {
      console.error('Error saving content piece:', err);
      setError('Failed to save content piece. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    } else {
      navigate(-1);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-xl font-semibold mb-4">
        {isEdit ? 'Edit Content Piece' : 'Create New Content Piece'}
      </h2>

      {/* Client Selector (only for global create mode) */}
      {!isEdit && clients && clients.length > 0 && !initialClientId && (
        <div className="mb-4">
          <label htmlFor="client_id_select" className="block text-sm font-medium text-gray-700">
            Client
          </label>
          <select
            id="client_id_select"
            value={selectedClientId || ''}
            onChange={(e) => setSelectedClientId(parseInt(e.target.value, 10))}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            required
          >
            <option value="" disabled>Select a client</option>
            {clients.map((client) => (
              <option key={client.id} value={client.id}>
                {client.company_name}
              </option>
            ))}
          </select>
        </div>
      )}

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
          {success}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-gray-700">
            Title
          </label>
          <input
            type="text"
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            required
          />
        </div>

        <div>
          <label htmlFor="idea" className="block text-sm font-medium text-gray-700">
            Idea
          </label>
          <input
            type="text"
            id="idea"
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            required
          />
        </div>

        <div>
          <label htmlFor="angle" className="block text-sm font-medium text-gray-700">
            Angle
          </label>
          <input
            type="text"
            id="angle"
            value={angle}
            onChange={(e) => setAngle(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            required
          />
        </div>

        {/* Replace Markdown Editor/Preview with Rich Text Editor */}
        <div>
          <label htmlFor="content_body" className="block text-sm font-medium text-gray-700">
            Content
          </label>
          <textarea
            id="content_body"
            value={contentBody}
            onChange={(e) => setContentBody(e.target.value)}
            rows={10}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            required
          />
        </div>

        <div>
          <label htmlFor="due_date" className="block text-sm font-medium text-gray-700">
            Due Date
          </label>
          <input
            type="date"
            id="due_date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="is_active"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <label htmlFor="is_active" className="ml-2 block text-sm text-gray-700">
            Active
          </label>
        </div>

        {isEdit && (
          <div>
            <label htmlFor="status" className="block text-sm font-medium text-gray-700">
              Status
            </label>
            <select
              id="status"
              value={status}
              onChange={(e) => setStatus(e.target.value as ContentStatus)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              {Object.values(ContentStatus).map((statusOption) => (
                <option key={statusOption} value={statusOption}>
                  {statusOption.replace('_', ' ')}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="flex justify-end space-x-3 pt-4">
          <button
            type="button"
            onClick={handleCancel}
            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-blue-300"
          >
            {loading ? 'Saving...' : isEdit ? 'Update Content' : 'Create Content'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ContentForm;
