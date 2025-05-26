import React from 'react';
import { Content, ContentStatus } from '../../services/contents';
import contentService from '../../services/contents';
// Removed MarkdownPreview import
import { formatDate } from '../../utils/formatters';
import { useAuth } from '../../context/AuthContext';
import CustomStarRating from '../common/CustomStarRating'; // Заменяем импорт

interface ContentViewProps {
  content: Content;
  onContentUpdated?: () => void; // Keep this for admin actions
}

const ContentView: React.FC<ContentViewProps> = ({ content, onContentUpdated }) => {
  const { user } = useAuth();
  const [loading, setLoading] = React.useState(false); // Keep for admin actions
  const [error, setError] = React.useState<string | null>(null); // Keep for admin actions

  const isAdmin = user?.role === 'admin';

  // Keep handleStatusChange only for admin actions (submit, publish)
  const handleStatusChange = async (action: 'submit' | 'publish') => {
    try {
      setLoading(true);
      setError(null);

      if (action === 'submit') {
        await contentService.submitForApproval(content.id);
      } else if (action === 'publish') {
        await contentService.publish(content.id);
      }

      if (onContentUpdated) {
        onContentUpdated();
      }
    } catch (err) {
      console.error(`Error ${action} content:`, err);
      setError(`Failed to ${action} content. Please try again.`);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadgeClass = (status: ContentStatus) => {
    switch (status) {
      case ContentStatus.DRAFT:
        return 'bg-gray-200 text-gray-800';
      case ContentStatus.PENDING_APPROVAL:
        return 'bg-yellow-200 text-yellow-800';
      case ContentStatus.REVISION_REQUESTED:
        return 'bg-red-200 text-red-800';
      case ContentStatus.APPROVED:
        return 'bg-green-200 text-green-800';
      case ContentStatus.SCHEDULED:
        return 'bg-purple-200 text-purple-800';
      case ContentStatus.PUBLISHED:
        return 'bg-blue-200 text-blue-800';
      default:
        return 'bg-gray-200 text-gray-800';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <div className="p-6">
        <div className="flex justify-between items-start mb-4">
          <h1 className="text-2xl font-bold">{content.title}</h1>
          <span
            className={`inline-block px-3 py-1 text-sm rounded-full ${getStatusBadgeClass(
              content.status
            )}`}
          >
            {content.status.replace('_', ' ')}
          </span>
        </div>

        {content.review_comment && (
          <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-4">
            <div className="flex">
              <div className="ml-3">
                <p className="text-sm text-red-700 font-medium">Revision Requested</p>
                <p className="text-sm text-red-700 mt-1">{content.review_comment}</p>
              </div>
            </div>
          </div>
        )}

        {/* Display Client Rating (if available) - For Admin View */}
        {isAdmin && content.client_rating !== null && content.client_rating !== undefined && (
           <div className="mt-4 pt-4 border-t border-gray-100 flex items-center gap-2">
              <span className="text-sm font-medium text-gray-500">Client Rating:</span>
              <CustomStarRating rating={content.client_rating} readOnly={true} size={20} />
           </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <h3 className="text-sm font-medium text-gray-500">Idea</h3>
            <p className="mt-1">{content.idea}</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500">Angle</h3>
            <p className="mt-1">{content.angle}</p>
          </div>
        </div>

        {/* Render HTML content directly */}
        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Content</h3>
          {/* WARNING: Ensure content.content_body is sanitized on the BACKEND before saving */}
          <div
            className="prose prose-sm sm:prose lg:prose-lg xl:prose-xl max-w-none border rounded-md p-4 bg-gray-50"
            dangerouslySetInnerHTML={{ __html: content.content_body || '' }}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-500">
          <div>
            <span className="font-medium">Due Date:</span>{' '}
            {content.due_date ? formatDate(content.due_date) : 'No due date'}
          </div>
          <div>
            <span className="font-medium">Created:</span> {formatDate(content.created_at)}
          </div>
          <div>
            <span className="font-medium">Last Updated:</span>{' '}
            {content.updated_at ? formatDate(content.updated_at) : formatDate(content.created_at)}
            {/* Show created_at if never updated */}
          </div>
          {content.scheduled_at && (
            <div>
              <span className="font-medium">Scheduled for:</span> {formatDate(content.scheduled_at)}
            </div>
          )}
          {content.published_at && (
            <div>
              <span className="font-medium">Published:</span> {formatDate(content.published_at)}
            </div>
          )}
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mt-4">
            {error}
          </div>
        )}

        {/* Admin Actions */}
        {isAdmin && (
          <div className="mt-6 pt-4 border-t border-gray-200">
            <div className="flex flex-wrap gap-2">
              {content.status === ContentStatus.DRAFT && (
                <button
                  onClick={() => handleStatusChange('submit')}
                  disabled={loading}
                  className="btn-primary"
                >
                  Submit for Approval
                </button>
              )}

              {content.status === ContentStatus.APPROVED && (
                <button
                  onClick={() => handleStatusChange('publish')}
                  disabled={loading}
                  className="btn-primary"
                >
                  Publish
                </button>
              )}
            </div>
          </div>
        )}
        {/* Client Actions section removed */}
      </div>
    </div>
  );
};

export default ContentView;
