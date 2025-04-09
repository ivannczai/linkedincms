import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import clientService, { ClientProfile, ClientProfileUpdate, ClientProfileCreate } from '../../services/clients'; 
import ClientForm from '../../components/clients/ClientForm';
import { formatDate } from '../../utils/formatters'; 
import ClientStrategyTab from '../../components/clients/ClientStrategyTab';
import ContentsList from '../../components/contents/ContentsList';

const ClientDetailPage: React.FC = () => {
  const { clientId } = useParams<{ clientId: string }>(); 
  const navigate = useNavigate();
  const clientIdNum = parseInt(clientId || '0', 10);
  
  const [client, setClient] = useState<ClientProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'profile' | 'strategy' | 'content'>('profile');
  const [isEditing, setIsEditing] = useState<boolean>(false);

  // Define fetchClient outside useEffect, memoize with useCallback
  const fetchClient = useCallback(async () => {
    if (!clientIdNum) {
       setError('Invalid client ID');
       // setLoading(false); // Let the calling context handle final loading state
       return;
    }
    try {
      // setLoading(true); // Let the calling context handle initial loading state
      const data = await clientService.getById(clientIdNum); 
      setClient(data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch client:', err);
      setError('Failed to load client. Please try again later.');
    } finally {
       // setLoading(false); // Let the calling context handle final loading state
    }
  }, [clientIdNum]); 

  // Load client on component mount and handle loading state
  useEffect(() => {
    setLoading(true);
    fetchClient().finally(() => setLoading(false));
  }, [fetchClient]); 

  // Handle client update
  const handleUpdateClient = async (data: ClientProfileCreate | ClientProfileUpdate) => {
    try {
      const updatedClient = await clientService.update(clientIdNum, data as ClientProfileUpdate);
      setClient(updatedClient); 
      setIsEditing(false); 
    } catch (err) {
      console.error('Failed to update client:', err);
      throw err; 
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
    <div className="container mx-auto"> 
      {/* Page Header */}
      <div className="mb-6">
        <div className="flex justify-between items-center flex-wrap gap-2">
          <h1 className="text-2xl font-bold text-brand-foreground">{client.company_name}</h1> 
          <button
            onClick={() => navigate('/admin/clients')}
            className="btn btn-secondary" 
          >
            Back to Clients
          </button>
        </div>
        <p className="text-gray-500 mt-1">{client.industry}</p> 
      </div>

      {/* Tabs - Refined styling */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-6" aria-label="Tabs"> 
          <button
            onClick={() => setActiveTab('profile')}
            className={`whitespace-nowrap pb-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'profile'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Profile
          </button>
          <button
            onClick={() => setActiveTab('strategy')}
            className={`whitespace-nowrap pb-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'strategy'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Content Strategy
          </button>
          <button
            onClick={() => setActiveTab('content')}
            className={`whitespace-nowrap pb-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'content'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Content Pieces
          </button>
        </nav>
      </div>

      {/* Tab content - Card style applied */}
      <div className="card"> 
        {activeTab === 'profile' && (
          <div> 
            {isEditing ? (
              <>
                <ClientForm
                  client={client}
                  onSubmit={handleUpdateClient}
                  isEdit={true}
                />
              </>
            ) : (
              <>
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold text-brand-foreground">Client Profile</h2> 
                  <button
                    onClick={() => setIsEditing(true)}
                    className="btn btn-secondary" 
                  >
                    Edit Profile
                  </button>
                </div>
                <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                  <div className="sm:col-span-1">
                    <dt className="form-label text-gray-500">Company Name</dt> 
                    <dd className="mt-1 text-sm text-brand-foreground">{client.company_name}</dd> 
                  </div>
                  <div className="sm:col-span-1">
                    <dt className="form-label text-gray-500">Industry</dt>
                    <dd className="mt-1 text-sm text-brand-foreground">{client.industry}</dd>
                  </div>
                  {client.website && (
                    <div className="sm:col-span-1">
                      <dt className="form-label text-gray-500">Website</dt>
                      <dd className="mt-1 text-sm text-brand-foreground">
                        <a href={client.website} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">
                          {client.website}
                        </a>
                      </dd>
                    </div>
                  )}
                  {client.linkedin_url && (
                    <div className="sm:col-span-1">
                      <dt className="form-label text-gray-500">LinkedIn</dt>
                      <dd className="mt-1 text-sm text-brand-foreground">
                        <a href={client.linkedin_url} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">
                          {client.linkedin_url}
                        </a>
                      </dd>
                    </div>
                  )}
                  {client.description && (
                    <div className="sm:col-span-2">
                      <dt className="form-label text-gray-500">Description</dt>
                      <dd className="mt-1 text-sm text-brand-foreground whitespace-pre-wrap">{client.description}</dd>
                    </div>
                  )}
                   {client.logo_url && (
                    <div className="sm:col-span-2">
                      <dt className="form-label text-gray-500">Logo</dt>
                      <dd className="mt-1">
                         <img src={client.logo_url} alt={`${client.company_name} logo`} className="h-16 w-auto rounded border border-gray-200" /> 
                      </dd>
                    </div>
                  )}
                  <div className="sm:col-span-1">
                    <dt className="form-label text-gray-500">Status</dt>
                    <dd className="mt-1 text-sm text-brand-foreground">
                      {client.is_active ? (
                        <span className="px-2.5 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Active</span>
                      ) : (
                        <span className="px-2.5 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">Inactive</span>
                      )}
                    </dd>
                  </div>
                  <div className="sm:col-span-1">
                    <dt className="form-label text-gray-500">Created</dt>
                    <dd className="mt-1 text-sm text-brand-foreground">{formatDate(client.created_at)}</dd>
                  </div>
                </dl>
              </>
            )}
          </div>
        )}

        {/* Render Strategy Tab Content */}
        {activeTab === 'strategy' && (
          <div> 
            <ClientStrategyTab client={client} />
          </div>
        )}

        {/* Render Content Tab Content */}
        {activeTab === 'content' && (
          <div> 
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Content Pieces</h2>
              <button
                onClick={() => navigate(`/admin/clients/${clientIdNum}/contents/new`)}
                className="btn btn-primary" 
              >
                Add New Content
              </button>
            </div>
            {/* Pass fetchClient as the update handler */}
            <ContentsList 
                clientId={clientIdNum} 
                showActions={true} 
                basePath={`/admin/clients/${clientIdNum}`} 
                onContentUpdated={fetchClient} 
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default ClientDetailPage;
