import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import contentService, { Content, ContentUpdateInput, ContentStatus } from '../../services/contents';
import { ArrowLeft, X } from 'lucide-react';
import TipTapEditor from '../../components/TipTapEditor';

const ClientContentEditPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const contentId = parseInt(id || '0', 10);
  const isScheduleMode = searchParams.get('schedule') === 'true';

  const [content, setContent] = useState<Content | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [scheduleDate, setScheduleDate] = useState<string>('');
  const [formData, setFormData] = useState<ContentUpdateInput>({
    title: '',
    content_body: '',
    idea: '',
    angle: '',
    status: ContentStatus.DRAFT,
    is_active: true
  });
  const [attachments, setAttachments] = useState<File[]>([]);
  const [existingAttachments, setExistingAttachments] = useState<string[]>([]);

  useEffect(() => {
    const fetchContent = async () => {
      if (!contentId) return;
      try {
        const data = await contentService.getById(contentId);
        if (user?.role !== 'client' || data.client_id !== user?.client_id) {
          setError('You do not have permission to edit this content.');
          setContent(null);
        } else if (data.status === ContentStatus.PUBLISHED) {
          setError('Cannot edit published content.');
          setContent(null);
        } else {
          setContent(data);
          setFormData({
            title: data.title,
            content_body: data.content_body,
            idea: data.idea,
            angle: data.angle,
            status: data.status,
            is_active: data.is_active
          });
          if (data.attachments) {
            setExistingAttachments(data.attachments);
          }
          if (data.scheduled_at) {
            const d = new Date(data.scheduled_at);
            const localString = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}T${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
            setScheduleDate(localString);
          }
          setError(null);
        }
      } catch (err) {
        console.error('Failed to fetch content:', err);
        setError('Failed to load content');
      } finally {
        setLoading(false);
      }
    };

    fetchContent();
  }, [contentId, user]);

  // const getImageUrl = (path: string) => {
  //   return `http://localhost:8000/${path}`; // TODO: change to the correct URL
  // };
  const getImageUrl = (path: string) => {
    const isLocalhost = window.location.hostname === 'localhost';
    const baseUrl = isLocalhost
      ? 'http://localhost:8000'
      : 'https://linkedin.rafinhafaria.com.br';
    return `${baseUrl}/${path}`;
  };
  

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      if (files.length > 9) {
        setError('You can only upload up to 9 files.');
        return;
      }
      setAttachments(files);
    }
  };

  const handleRemoveAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const handleRemoveExistingAttachment = (index: number) => {
    setExistingAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('title', formData.title || '');
      formDataToSend.append('content_body', formData.content_body || '');
      formDataToSend.append('idea', formData.idea || '');
      formDataToSend.append('angle', formData.angle || '');
      formDataToSend.append('status', formData.status || ContentStatus.DRAFT);
      formDataToSend.append('is_active', String(formData.is_active));
      
      attachments.forEach((file) => {
        formDataToSend.append('attachments', file);
      });
      existingAttachments.forEach((path) => {
        formDataToSend.append('existing_attachments', path);
      });

      if (isScheduleMode && scheduleDate) {
        const localDate = new Date(scheduleDate);
        if (isNaN(localDate.getTime())) {
          throw new Error('Invalid date format');
        }
        if (localDate <= new Date()) {
          throw new Error('Scheduled time must be in the future.');
        }
        const scheduledAtUTC = localDate.toISOString();
        await contentService.schedule(content.id, scheduledAtUTC);
      } else {
        await contentService.updateClient(content.id, formDataToSend as any);
      }
      navigate('/client/library');
    } catch (err: any) {
      console.error('Failed to update content:', err);
      setError(err.message || 'Failed to update content. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error || !content) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="m-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded" role="alert">
          <strong className="font-bold">Error!</strong>
          <span className="block sm:inline"> {error || 'Content not found or not accessible.'}</span>
        </div>
        <button onClick={() => navigate('/client/library')} className="btn btn-secondary mt-4">
          Back to Library
        </button>
      </div>
    );
  }
  const now = new Date();
  const pad = (n: number) => (n < 10 ? '0' + n : n);
  const localMin = `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`;


  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Edit Content</h1>
        <button onClick={() => navigate(`/client/contents/${content?.id}`)} className="btn btn-secondary">
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to Content
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-gray-700">
            Title
          </label>
          <input
            type="text"
            id="title"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            required
          />
        </div>

        <div>
          <label htmlFor="content_body" className="block text-sm font-medium text-gray-700">
            Content
          </label>
          <div className="mt-1">
            <TipTapEditor
              content={formData.content_body || ''}
              onChange={(value) => setFormData({ ...formData, content_body: value })}
              className="min-h-[200px] border border-gray-300 rounded-md"
            />
          </div>
        </div>

        {/* Attachments Section */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Attachments
          </label>
          
          {/* Existing Attachments */}
          {existingAttachments.length > 0 && (
            <div className="mb-4">
              <div className="flex flex-wrap gap-2">
                {existingAttachments.map((attachment, index) => (
                  <div key={index} className="relative w-24 h-24">
                    <img
                      src={getImageUrl(attachment)}
                      alt={`Attachment ${index + 1}`}
                      className="w-full h-full object-cover rounded-md"
                    />
                    <button
                      type="button"
                      onClick={() => handleRemoveExistingAttachment(index)}
                      className="absolute top-1 right-1 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center hover:bg-red-600"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* New Attachments Upload */}
          <div className="mb-4">
            <input
              type="file"
              multiple
              accept="image/*"
              onChange={handleFileChange}
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
            <div className="mb-4">
              <div className="flex flex-wrap gap-2">
                {attachments.map((file, index) => (
                  <div key={index} className="relative w-24 h-24">
                    <div
                      className="w-full h-full bg-gray-100 rounded-md overflow-hidden"
                      style={{
                        backgroundImage: `url(${URL.createObjectURL(file)})`,
                        backgroundSize: 'cover',
                        backgroundPosition: 'center'
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => handleRemoveAttachment(index)}
                      className="absolute top-1 right-1 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center hover:bg-red-600"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {isScheduleMode && (
          <div>
            <label htmlFor="scheduleDate" className="block text-sm font-medium text-gray-700">
              Schedule Date and Time (Your Local Time)
            </label>
            <input
              type="datetime-local"
              id="scheduleDate"
              value={scheduleDate}
              onChange={(e) => setScheduleDate(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
              required={isScheduleMode}
              min={localMin}
            />
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded" role="alert">
            {error}
          </div>
        )}

        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={() => navigate(`/client/contents/${content?.id}`)}
            className="btn btn-secondary"
          >
            Cancel
          </button>
          {isScheduleMode ? (
            <button
              type="submit"
              disabled={isSubmitting || !scheduleDate}
              className="btn btn-primary"
            >
              {isSubmitting ? 'Saving...' : 'Save and Schedule'}
            </button>
          ) : (
            <button
              type="submit"
              disabled={isSubmitting}
              className="btn btn-primary"
            >
              {isSubmitting ? 'Saving...' : 'Save Changes'}
            </button>
          )}
        </div>
      </form>
    </div>
  );
};

export default ClientContentEditPage;
