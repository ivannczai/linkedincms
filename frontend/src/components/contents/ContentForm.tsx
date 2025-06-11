import React, { useState, useEffect, useRef } from 'react';
import { Content, ContentStatus } from '../../services/contents';
import contentService from '../../services/contents';
import { useNavigate } from 'react-router-dom';
import { ClientProfile } from '../../services/clients';
import TipTapEditor from '../TipTapEditor';

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
  const [attachments, setAttachments] = useState<File[]>([]);
  const [existingAttachments, setExistingAttachments] = useState<string[]>(content?.attachments?.map(a => a.toString()) || []);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const editorWrapperRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (content) {
      console.log('Content:', content);
      console.log('Content attachments:', content.attachments);
      setTitle(content.title);
      setIdea(content.idea);
      setAngle(content.angle);
      setExistingAttachments(content.attachments?.map(a => a.toString()) || []);
      setContentBody(content.content_body || '');
      setDueDate(content.due_date || '');
      setIsActive(content.is_active);
      setStatus(content.status);
    }
  }, [content]);

  // const getImageUrl = (path: string) => {
  //   return `http://localhost:8000/${path}`; // TODO: Change to the correct URL
  // };
  const getImageUrl = (path: string) => {
    const isLocalhost = window.location.hostname === 'localhost';
    const baseUrl = isLocalhost
      ? 'http://localhost:8000'
      : 'https://linkedin.rafinhafaria.com.br';
      const encodedPath = encodeURI(path);
    return `${baseUrl}/${encodedPath}`;
  };

  const handleClick = () => {
    if (editorWrapperRef.current) {
      (editorWrapperRef.current.querySelector('.ProseMirror') as HTMLElement)?.focus();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    // Basic check if editor content is effectively empty (ignoring empty tags)
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = contentBody;
    const isContentEmpty = tempDiv.textContent?.trim().length === 0;

    if (isContentEmpty) {
      setError('Content Body cannot be empty.');
      setLoading(false);
      return;
    }

    try {
      const formData = new FormData();
      formData.append('title', title);
      formData.append('idea', idea);
      formData.append('angle', angle);
      formData.append('content_body', contentBody);
      formData.append('is_active', String(isActive));
      formData.append('status', status);
      const client_id = selectedClientId ?? content?.client_id;
        if (!client_id) {
          setError('Client ID is required.');
          setLoading(false);
          return;
        }
      formData.append('client_id', String(client_id));
      // formData.append('client_id', String(selectedClientId || content?.client_id));

      attachments.forEach((file) => {
        formData.append('attachments', file);
      });
      
      existingAttachments.forEach((path) => {
        formData.append('existing_attachments', path);
      });

      let savedContent: Content;
      if (isEdit && content) {
        savedContent = await contentService.update(content.id, formData as any);
        setSuccess('Content piece updated successfully');
      } else {
        savedContent = await contentService.create(formData as any);
        setSuccess('Content piece created successfully');
      }

      if (onSubmit) {
        onSubmit(savedContent);
      } else {
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

  const handleRemoveAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const handleRemoveExistingAttachment = (index: number) => {
    setExistingAttachments(prev => prev.filter((_, i) => i !== index));
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
            style={{ padding: '5px 10px' }}
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
            style={{ padding: '5px 10px' }}
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
            style={{ padding: '5px 10px' }}
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
            style={{ padding: '5px 10px' }}
            required
          />
        </div>

        {/* Content Body */}
        <div>
          <label htmlFor="content_body" className="block text-sm font-medium text-gray-700">
            Content Body
          </label>
          <div className="mt-1 cursor-text"  ref={editorWrapperRef} onClick={handleClick}>
            <TipTapEditor
              content={contentBody}
              onChange={setContentBody}
              className="min-h-[200px] border border-gray-300 rounded-md"
            />
          </div>
        </div>

        {/* Attachments Preview */}
        {existingAttachments && existingAttachments.length > 0 && (
          <div className="mt-4">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Attached Images</h3>
            <div className="flex flex-wrap gap-2">
              {existingAttachments.map((attachment, index) => (
                <div key={index} className="relative w-[20%] aspect-square">
                  <img
                    src={getImageUrl(attachment)}
                    alt={`Attachment ${index + 1}`}
                    className="w-full h-full object-contain rounded-md"
                  />
                  <button
                    type="button"
                    onClick={() => handleRemoveExistingAttachment(index)}
                    className="absolute top-1 right-1 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center hover:bg-red-600"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Attachments Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Attachments
          </label>
          <div className="mt-1">
            <input
              type="file"
              multiple
              accept="image/*"
              onChange={(e) => {
                if (e.target.files) {
                  const files = Array.from(e.target.files);
                  if (files.length > 9) {
                    setError('You can only upload up to 9 files.');
                    return;
                  }
                  setAttachments(files);
                }
              }}
              className="block w-full text-sm text-gray-500
                file:mr-4 file:py-2 file:px-4
                file:rounded-md file:border-0
                file:text-sm file:font-semibold
                file:bg-blue-50 file:text-blue-700
                hover:file:bg-blue-100"
            />
          </div>
          
          {/* New Attachments Preview */}
          {attachments.length > 0 && (
            <div className="mt-4">
              <h3 className="text-sm font-medium text-gray-700 mb-2">New Images</h3>
              <div className="flex flex-wrap gap-2">
                {attachments.map((file, index) => (
                  <div key={index} className="relative w-[20%] aspect-square">
                    <div
                      className="w-full h-full bg-gray-100 rounded-md overflow-hidden"
                      style={{
                        backgroundImage: `url(${URL.createObjectURL(file)})`,
                        backgroundSize: 'contain',
                        backgroundPosition: 'center',
                        backgroundRepeat: 'no-repeat'
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => handleRemoveAttachment(index)}
                      className="absolute top-1 right-1 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center hover:bg-red-600"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div>
          <label htmlFor="due_date" className="block text-sm font-medium text-gray-700">
          Proposed posting date
          </label>
          <input
            type="date"
            id="due_date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            style={{ padding: '5px 10px' }}
          />
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="is_active"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            className="mt-1  rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            // style={{ padding: '5px 10px' }}
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
              style={{ padding: '5px 10px' }}
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
