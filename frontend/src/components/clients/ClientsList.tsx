import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom'; 
import clientService, { ClientProfile } from '../../services/clients';
import { Edit, Trash2, Eye } from 'lucide-react'; // Keep Trash2
import { formatDate } from '../../utils/formatters'; 

interface ClientsListProps {
  // Remove onClientSelected prop
  onClientDeleted?: () => void;
}

const ClientsList: React.FC<ClientsListProps> = ({ onClientDeleted }) => {
  const [clients, setClients] = useState<ClientProfile[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Load clients on component mount
  useEffect(() => {
    const fetchClients = async () => {
      try {
        setLoading(true);
        const data = await clientService.getAll();
        setClients(data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch clients:', err);
        setError('Failed to load clients. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchClients();
  }, []);

  // Handle client deletion
  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this client?')) {
      try {
        await clientService.delete(id);
        setClients(clients.filter(client => client.id !== id));
        if (onClientDeleted) {
          onClientDeleted();
        }
      } catch (err) {
        console.error('Failed to delete client:', err);
        setError('Failed to delete client. Please try again later.');
      }
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
        <strong className="font-bold">Error!</strong>
        <span className="block sm:inline"> {error}</span>
      </div>
    );
  }

  if (clients.length === 0) {
    return (
      <div className="text-center p-8">
        <p className="text-gray-500 mb-4">No clients found.</p>
        <Link to="/admin/clients/new" className="btn-primary">
          Create New Client
        </Link>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full bg-white">
        <thead className="bg-gray-100">
          <tr>
            <th className="py-3 px-4 text-left">Company</th>
            <th className="py-3 px-4 text-left">Industry</th>
            <th className="py-3 px-4 text-left">Status</th>
            <th className="py-3 px-4 text-left">Created</th>
            <th className="py-3 px-4 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {clients.map((client) => (
            <tr key={client.id} className="hover:bg-gray-50">
              <td className="py-3 px-4 align-top"> {/* Align top */}
                <div className="font-medium text-brand-foreground">{client.company_name}</div> {/* Use brand color */}
                {client.website && (
                  <div className="text-xs text-gray-500 mt-0.5"> {/* Smaller text */}
                    <a href={client.website} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">
                      {client.website.replace(/^https?:\/\//, '')}
                    </a>
                  </div>
                )}
              </td>
              <td className="py-3 px-4 text-gray-500 align-top">{client.industry}</td>
              <td className="py-3 px-4 align-top"> {/* Align top */}
                {client.is_active ? (
                  <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                    Active
                  </span>
                ) : (
                  <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                    Inactive
                  </span>
                )}
              </td>
              <td className="py-3 px-4 text-gray-500 align-top"> {/* Align top */}
                {formatDate(client.created_at)} {/* Use formatDate */}
              </td>
              <td className="py-3 px-4 text-right text-sm font-medium align-top"> {/* Align top */}
                <div className="flex justify-end space-x-1"> {/* Reduced space */}
                  {/* Changed View to Link */}
                  <Link
                    to={`/admin/clients/${client.id}`}
                    className="btn btn-ghost btn-sm p-1 text-gray-500 hover:text-primary-600" // Smaller icon button
                    title="View Details"
                  >
                     <Eye className="h-4 w-4" />
                  </Link>
                  <Link
                    to={`/admin/clients/${client.id}/edit`}
                    className="btn btn-ghost btn-sm p-1 text-gray-500 hover:text-blue-600" // Smaller icon button
                     title="Edit Client"
                  >
                     <Edit className="h-4 w-4" />
                  </Link>
                  <button
                    onClick={() => handleDelete(client.id)}
                    className="btn btn-ghost btn-sm p-1 text-gray-500 hover:text-red-600" 
                    title="Delete Client"
                  >
                     <Trash2 className="h-4 w-4" /> {/* Use Trash2 icon */}
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ClientsList;
