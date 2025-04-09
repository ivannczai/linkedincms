import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom'; // Removed useNavigate
import ClientForm from '../../components/clients/ClientForm';
import clientService, { ClientProfile, ClientProfileCreate, ClientProfileUpdate } from '../../services/clients';
// Removed user service import

const EditClientPage: React.FC = () => {
  // Removed unused navigate variable
  const { id } = useParams<{ id: string }>();
  const clientId = parseInt(id || '0', 10);
  
  const [client, setClient] = useState<ClientProfile | null>(null);
  // Removed clientUsers state
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Load client data on component mount
  useEffect(() => {
    const fetchClientData = async () => {
      if (!clientId) {
         setError('Invalid client ID');
         setLoading(false);
         return;
      }
      try {
        setLoading(true);
        // Fetch client profile (including user details if backend provides them)
        const clientData = await clientService.getById(clientId); 
        setClient(clientData);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch client data:', err);
        setError('Failed to load client data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchClientData();
    
  }, [clientId]);

  // Handle form submission
  const handleSubmit = async (data: ClientProfileCreate | ClientProfileUpdate) => {
    try {
      // We know this is an update operation
      await clientService.update(clientId, data as ClientProfileUpdate);
      // Navigation is handled within ClientForm now
    } catch (err) {
      console.error('Failed to update client:', err);
      throw err; // Let the form component handle the error
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error || !client) {
    return (
      <div className="m-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded" role="alert">
        <strong className="font-bold">Error!</strong>
        <span className="block sm:inline"> {error || 'Client not found'}</span>
      </div>
    );
  }

  return (
    <div className="container mx-auto"> {/* Removed px-4 py-8 */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Edit Client</h1>
        <p className="text-gray-600 mt-1">
          Editing client profile for <strong>{client.company_name}</strong>
        </p>
      </div>

      <div className="card"> {/* Use card style */}
        <ClientForm
          client={client}
          // No longer pass clientUsers
          onSubmit={handleSubmit}
          isEdit={true}
        />
      </div>
    </div>
  );
};

export default EditClientPage;
