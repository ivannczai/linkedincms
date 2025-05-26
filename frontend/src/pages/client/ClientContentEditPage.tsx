import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import contentService, { Content, ContentUpdateInput } from '../../services/contents';
import { ArrowLeft } from 'lucide-react';

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
  });

  useEffect(() => {
    const fetchContent = async () => {
      try {
        const data = await contentService.getById(contentId);
        if (user?.role !== 'client' || data.client_id !== user?.client_id) {
          setError('You do not have permission to edit this content.');
          setContent(null);
        } else if (data.status === 'PUBLISHED') {
          setError('Cannot edit published content.');
          setContent(null);
        } else {
          setContent(data);
          setFormData({
            title: data.title,
            content_body: data.content_body,
          });
          if (data.scheduled_at) {
            setScheduleDate(data.scheduled_at);
          }
        }
      } catch (err) {
        console.error('Failed to fetch content:', err);
        setError('Failed to load content.');
      } finally {
        setLoading(false);
      }
    };

    fetchContent();
  }, [contentId, user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content) return;

    setIsSubmitting(true);
    setError(null);

    try {
      if (isScheduleMode && scheduleDate) {
        const localDate = new Date(scheduleDate);
        await contentService.schedule(content.id, localDate.toISOString());
      } else {
        await contentService.updateClient(content.id, formData);
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

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Edit Content</h1>
        <button onClick={() => navigate(`/client/contents/${content.id}`)} className="btn btn-secondary">
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
          <textarea
            id="content_body"
            rows={10}
            value={formData.content_body || ''}
            onChange={(e) => setFormData({ ...formData, content_body: e.target.value })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            required
          />
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
              min={new Date().toISOString().slice(0, 16)}
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
            onClick={() => navigate(`/client/contents/${content.id}`)}
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