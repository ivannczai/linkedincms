import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import contentService, { Content } from '../../services/contents'; // Remove unused type imports
import ContentForm from '../../components/contents/ContentForm';

const EditContentPage: React.FC = () => {
  const { clientId, contentId } = useParams<{ clientId: string; contentId: string }>();
  const navigate = useNavigate();
  const numericClientId = parseInt(clientId || '0', 10);
  const numericContentId = parseInt(contentId || '0', 10);

  const [content, setContent] = useState<Content | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchContent = async () => {
      if (!numericContentId) {
        setError('Invalid Content ID');
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        const data = await contentService.getById(numericContentId);
        setContent(data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch content:', err);
        setError('Failed to load content piece for editing.');
      } finally {
        setLoading(false);
      }
    };

    fetchContent();
  }, [numericContentId]);

  // Remove unused 'data' parameter from handler signature
  const handleContentUpdated = () => { 
    // Navigate back to the content view page after successful update
    // We need the ID from the original content object
    if (content) {
      navigate(`/admin/clients/${content.client_id}/contents/${content.id}`);
    } else {
       navigate(`/admin/clients/${numericClientId}`); // Fallback
    }
  };

  const handleCancel = () => {
    // Navigate back to the content view page or client detail page
    if (content) {
       navigate(`/admin/clients/${content.client_id}/contents/${content.id}`);
    } else {
       navigate(`/admin/clients/${numericClientId}`); // Fallback
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
      <div className="container mx-auto"> {/* Removed px-4 py-8 */}
        <div className="m-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded" role="alert">
          <strong className="font-bold">Error!</strong>
          <span className="block sm:inline"> {error || 'Content not found'}</span>
        </div>
        <button
          onClick={() => navigate(`/admin/clients/${numericClientId}`)}
          className="btn btn-secondary ml-6" // Use new style
        >
          Back to Client
        </button>
      </div>
    );
  }

  return (
    <div className="container mx-auto"> {/* Removed px-4 py-8 */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-brand-foreground">Edit Content Piece</h1>
        <p className="text-gray-600 mt-1">Update the details for "{content.title}".</p>
      </div>
      {/* Use card style */}
      <div className="card"> 
        <ContentForm 
          content={content} 
          isEdit={true} 
          onSubmit={handleContentUpdated} 
          onCancel={handleCancel} 
          // Pass clients prop as empty array or undefined if not needed for edit form logic
          clients={[]} 
        />
      </div>
    </div>
  );
};

export default EditContentPage;
