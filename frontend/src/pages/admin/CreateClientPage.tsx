import React from 'react'; // Removed useState, useEffect
// Removed unused useNavigate import
import ClientForm from '../../components/clients/ClientForm';
import clientService, { ClientProfileCreate, ClientProfileUpdate } from '../../services/clients';
// Removed user service import

const CreateClientPage: React.FC = () => {
  // Removed unused navigate variable
  // Removed state for clientUsers, loading, error as they are no longer needed here

  // Handle form submission
  const handleSubmit = async (data: ClientProfileCreate | ClientProfileUpdate) => {
    // The backend now handles user creation within the client creation endpoint
    try {
      // We expect ClientProfileCreate type here
      await clientService.create(data as ClientProfileCreate); 
      // Navigation is handled within ClientForm now
    } catch (err) {
      console.error('Failed to create client:', err);
      // Error handling is now primarily within ClientForm, but re-throwing allows
      // potential parent component error handling if needed in the future.
      throw err; 
    }
  };

  return (
    <div className="container mx-auto"> {/* Removed px-4 py-8, handled by Layout */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Create New Client</h1>
        <p className="text-gray-600 mt-1">Create a new client profile and associated user account.</p>
      </div>

      {/* Use card style for the form container */}
      <div className="card"> 
        <ClientForm
          // No longer pass clientUsers
          onSubmit={handleSubmit}
          // isEdit is false by default
        />
      </div>
    </div>
  );
};

export default CreateClientPage;
