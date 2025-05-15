import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom'; 
import contentService, { Content, ContentStatus } from '../../services/contents';
import { formatDate } from '../../utils/formatters';
import { Edit, Trash2, Eye, Send } from 'lucide-react'; 
import CustomStarRating from '../common/CustomStarRating'; // Import CustomStarRating

interface ContentsListProps {
  clientId?: number;
  status?: ContentStatus;
  showActions?: boolean; 
  onContentUpdated?: () => void;
  basePath?: string; 
}

const ContentsList: React.FC<ContentsListProps> = ({
  clientId,
  status,
  showActions = true,
  onContentUpdated,
  basePath = '/admin/clients', 
}) => {
  const [contents, setContents] = useState<Content[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchContents = async () => {
    try {
      setLoading(true);
      const data = await contentService.getAll(clientId, status);
      setContents(data);
      setError(null);
    } catch (err) {
      setError('Failed to load content pieces');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContents();
  }, [clientId, status]);

  const handleStatusChange = async (contentId: number, action: 'submit' | 'publish') => {
    try {
      setLoading(true); 
      if (action === 'submit') {
        await contentService.submitForApproval(contentId);
      } else if (action === 'publish') {
        await contentService.publish(contentId);
      }
      
      await fetchContents(); 
      if (onContentUpdated) {
        onContentUpdated();
      }
    } catch (err) {
      setError(`Failed to ${action} content`);
      console.error(err);
    } finally {
       setLoading(false);
    }
  };
  
  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this content piece?')) {
      try {
        setLoading(true);
        await contentService.delete(id);
        await fetchContents(); 
        if (onContentUpdated) {
          onContentUpdated(); 
        }
      } catch (err) {
        console.error('Failed to delete content:', err);
        setError('Failed to delete content. Please try again later.');
      } finally {
         setLoading(false);
      }
    }
  };


  const getStatusBadgeClass = (status: ContentStatus) => {
    switch (status) {
      case ContentStatus.DRAFT: return 'bg-gray-100 text-gray-600';
      case ContentStatus.PENDING_APPROVAL: return 'bg-yellow-100 text-yellow-700';
      case ContentStatus.REVISION_REQUESTED: return 'bg-red-100 text-red-700';
      case ContentStatus.APPROVED: return 'bg-green-100 text-green-700';
      case ContentStatus.PUBLISHED: return 'bg-blue-100 text-blue-700';
      default: return 'bg-gray-100 text-gray-600';
    }
  };

  if (loading && contents.length === 0) { 
    return <div className="flex justify-center p-4"><div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-600"></div></div>;
  }

  if (error) {
    return <div className="text-red-500 p-4">{error}</div>;
  }

  if (contents.length === 0) {
    return <div className="text-gray-500 p-4 text-center">No content pieces found matching the criteria.</div>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full bg-white text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="py-2 px-4 text-left font-medium text-gray-500 uppercase tracking-wider">Title</th>
            <th className="py-2 px-4 text-left font-medium text-gray-500 uppercase tracking-wider">Status</th>
            <th className="py-2 px-4 text-left font-medium text-gray-500 uppercase tracking-wider">Rating</th> 
            <th className="py-2 px-4 text-left font-medium text-gray-500 uppercase tracking-wider">Due Date</th>
            <th className="py-2 px-4 text-left font-medium text-gray-500 uppercase tracking-wider">Published</th> 
            {showActions && <th className="py-2 px-4 text-right font-medium text-gray-500 uppercase tracking-wider">Actions</th>}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {contents.map((content) => (
            <tr key={content.id} className="hover:bg-gray-50">
              <td className="py-3 px-4">
                <Link
                  to={`/admin/clients/${content.client_id}/contents/${content.id}`}
                  className="font-medium text-primary-600 hover:underline"
                >
                  {content.title}
                </Link>
                {content.review_comment && (
                  <div className="text-xs text-red-600 mt-1 italic" title={content.review_comment}>
                    Revision: "{content.review_comment.substring(0, 50)}{content.review_comment.length > 50 ? '...' : ''}"
                  </div>
                )}
              </td>
              <td className="py-3 px-4">
                <span
                  className={`inline-block px-2.5 py-0.5 text-xs font-semibold rounded-full ${getStatusBadgeClass(
                    content.status
                  )}`}
                >
                  {content.status.replace('_', ' ')}
                </span>
              </td>
               <td className="py-3 px-4">
                 {/* Display Rating - Use CustomStarRating and ensure flex alignment */}
                 {content.client_rating !== null && content.client_rating !== undefined ? (
                    <div className="flex items-center"> {/* Ensure flex and alignment */}
                       <CustomStarRating rating={content.client_rating} readOnly={true} size={16} />
                    </div>
                 ) : (
                    <span className="text-gray-400">-</span>
                 )}
               </td>
              <td className="py-3 px-4 text-gray-500">
                {content.due_date ? formatDate(content.due_date) : '-'}
              </td>
              <td className="py-3 px-4 text-gray-500"> 
                {content.published_at ? formatDate(content.published_at) : '-'}
              </td>
              {showActions && (
                <td className="py-3 px-4 text-right">
                  <div className="flex justify-end space-x-1">
                     <Link
                       to={`${basePath}/${content.client_id}/contents/${content.id}`}
                       className="btn btn-ghost btn-sm p-1 text-gray-500 hover:text-primary-600" 
                       title="View Details"
                     >
                        <Eye className="h-4 w-4" />
                     </Link>
                    {/* Edit link - Assuming only admins edit */}
                    <Link
                      to={`/admin/clients/${content.client_id}/contents/${content.id}/edit`}
                      className="btn btn-ghost btn-sm p-1 text-gray-500 hover:text-blue-600"
                      title="Edit Content"
                    >
                      <Edit className="h-4 w-4" />
                    </Link>
                    
                    {(content.status === ContentStatus.DRAFT || content.status === ContentStatus.REVISION_REQUESTED) && (
                      <button
                        onClick={() => handleStatusChange(content.id, 'submit')}
                        disabled={loading}
                        className="btn btn-ghost btn-sm p-1 text-gray-500 hover:text-green-600"
                        title="Submit for Approval"
                      >
                        <Send className="h-4 w-4" />
                      </button>
                    )}
                    
                    {content.status === ContentStatus.APPROVED && (
                      <button
                        onClick={() => handleStatusChange(content.id, 'publish')}
                        disabled={loading}
                        className="btn btn-ghost btn-sm p-1 text-gray-500 hover:text-blue-600"
                        title="Publish"
                      >
                         {/* Placeholder for Publish icon if needed */}
                         Publish 
                      </button>
                    )}
                     <button
                       onClick={() => handleDelete(content.id)}
                       disabled={loading}
                       className="btn btn-ghost btn-sm p-1 text-gray-500 hover:text-red-600"
                       title="Delete Content"
                     >
                       <Trash2 className="h-4 w-4" />
                     </button>
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ContentsList;
