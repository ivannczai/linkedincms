import React, { useState, useEffect, useCallback } from 'react'; // Import useCallback
import { useParams, useNavigate, Link } from 'react-router-dom';
import contentService, { Content } from '../../services/contents';
import ContentView from '../../components/contents/ContentView';
import { ArrowLeft, Edit } from 'lucide-react'; // Import icons

const ContentViewPage: React.FC = () => {
  const { clientId, contentId } = useParams<{ clientId: string; contentId: string }>();
  const navigate = useNavigate();
  const numericClientId = parseInt(clientId || '0', 10);
  const numericContentId = parseInt(contentId || '0', 10);

  const [content, setContent] = useState<Content | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Define fetchContent using useCallback to ensure stable reference
  const fetchContent = useCallback(async () => {
    if (!numericContentId) {
      setError('Invalid Content ID');
      setLoading(false);
      return;
    }
    // Keep loading true while refetching after an update
    setLoading(true); 
    try {
      const data = await contentService.getById(numericContentId);
      // Add check if content actually belongs to clientId if needed,
      // though admin should have access anyway.
      if (data.client_id !== numericClientId) {
         console.warn(`Content ${numericContentId} does not belong to client ${numericClientId}`);
         // Decide how to handle this - show error or allow viewing? For now, allow.
      }
      setContent(data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch content:', err);
      setError('Failed to load content piece. Please try again later.');
      setContent(null); // Clear content on error
    } finally {
      setLoading(false);
    }
  }, [numericContentId, numericClientId]); // Dependencies for useCallback

  useEffect(() => {
    fetchContent();
  }, [fetchContent]); // Run fetchContent when the component mounts or fetchContent changes

  // Define the callback function to refetch content
  const handleContentUpdate = () => {
    console.log("handleContentUpdate called, refetching content..."); // Add log
    fetchContent(); // Call the memoized fetch function
  };

  if (loading && !content) { // Show loading spinner only on initial load
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
           <ArrowLeft className="mr-2 h-4 w-4" /> Back to Client
        </button>
      </div>
    );
  }

  // Show loading indicator overlay if loading state is true during refetch
  const isLoadingOverlayVisible = loading && content;

  return (
    <div className="container mx-auto relative"> {/* Add relative positioning */}
      {/* Loading Overlay */}
      {isLoadingOverlayVisible && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex justify-center items-center z-10">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
        </div>
      )}

      <div className="mb-6 flex justify-between items-center flex-wrap gap-2">
        {/* Title is now inside ContentView */}
        <div> {/* Empty div for spacing */} </div>
        <div className="flex gap-2">
          <Link
            to={`/admin/clients/${numericClientId}/contents/${numericContentId}/edit`}
            className="btn btn-primary" // Use new style
          >
             <Edit className="mr-2 h-4 w-4" /> Edit Content
          </Link>
          <button
            onClick={() => navigate(`/admin/clients/${numericClientId}`)} // Navigate back to client detail
            className="btn btn-secondary" // Use new style
          >
             <ArrowLeft className="mr-2 h-4 w-4" /> Back to Client
          </button>
        </div>
      </div>
      {/* Use card style for the content view */}
      <div className="card p-0 overflow-hidden"> {/* Remove padding, let ContentView handle it */}
         {/* Pass the handleContentUpdate function as the onContentUpdated prop */}
         <ContentView content={content} onContentUpdated={handleContentUpdate} />
      </div>
    </div>
  );
};

export default ContentViewPage;
