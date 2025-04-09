import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ContentForm from '../../components/contents/ContentForm';
import { Content } from '../../services/contents'; // Keep Content type for handler
import clientService, { ClientProfile } from '../../services/clients';

const CreateGlobalContentPage: React.FC = () => {
  const navigate = useNavigate();
  const [clients, setClients] = useState<ClientProfile[]>([]);
  const [loadingClients, setLoadingClients] = useState<boolean>(true);
  const [errorClients, setErrorClients] = useState<string | null>(null);

  // Load clients on component mount
  useEffect(() => {
    const fetchClients = async () => {
      try {
        setLoadingClients(true);
        const data = await clientService.getAll();
        setClients(data);
        setErrorClients(null);
      } catch (err) {
        console.error('Failed to fetch clients:', err);
        setErrorClients('Failed to load clients for selection.');
      } finally {
        setLoadingClients(false);
      }
    };

    fetchClients();
  }, []);

  const handleContentCreated = (createdContent: Content) => {
    // Navigate to the detail page of the newly created content
    navigate(`/admin/clients/${createdContent.client_id}/contents/${createdContent.id}`);
  };

  const handleCancel = () => {
    // Navigate back to the central content page
    navigate('/admin/content');
  };

  if (loadingClients) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (errorClients) {
    return (
      <div className="container mx-auto"> {/* Removed px-4 py-8 */}
        <div className="m-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded" role="alert">
          <strong className="font-bold">Error!</strong>
          <span className="block sm:inline"> {errorClients}</span>
        </div>
         <button
          onClick={() => navigate('/admin/content')}
          className="btn btn-secondary ml-6" // Use new style
        >
          Back to Content List
        </button>
      </div>
    );
  }

  return (
    <div className="container mx-auto"> {/* Removed px-4 py-8 */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-brand-foreground">Create New Content Piece</h1>
        <p className="text-gray-600 mt-1">Select a client and fill in the details for the new content piece.</p>
      </div>
      {/* Use card style */}
      <div className="card"> 
        <ContentForm 
          clients={clients} // Pass the list of clients
          onSubmit={handleContentCreated} 
          onCancel={handleCancel} 
          // isEdit is false by default
        />
      </div>
    </div>
  );
};

export default CreateGlobalContentPage;
