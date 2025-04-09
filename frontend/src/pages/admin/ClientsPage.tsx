import React from 'react'; // Removed useState
import { Link } from 'react-router-dom';
import ClientsList from '../../components/clients/ClientsList';
// Removed ClientProfile import as it's handled by ClientsList

const ClientsPage: React.FC = () => {
  // Removed state related to selectedClient and modal

  // Handlers are no longer needed here as details are on a separate page
  // const handleClientSelected = (client: ClientProfile) => { ... };
  // const handleClientDeleted = () => { ... };

  return (
    <div className="container mx-auto"> {/* Removed px-4 py-8 */}
      <div className="flex justify-between items-center mb-6 flex-wrap gap-2">
        <h1 className="text-2xl font-bold text-brand-foreground">Client Management</h1>
        <Link
          to="/admin/clients/new"
          className="btn btn-primary" // Use new style
        >
          Add New Client
        </Link>
      </div>

      {/* TODO: Add Search/Filter controls */}
      <div className="mb-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
         <p className="text-gray-500 italic">(Search/Filter placeholder)</p>
      </div>


      <div className="card overflow-hidden p-0"> {/* Use card style, remove padding for table */}
        {/* Client list - Removed handlers */}
        <ClientsList /> 
      </div>

      {/* Modal removed - Details are now on ClientDetailPage */}
      
    </div>
  );
};

export default ClientsPage;
