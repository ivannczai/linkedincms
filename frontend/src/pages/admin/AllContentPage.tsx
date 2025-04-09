import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ContentsList from '../../components/contents/ContentsList';
import clientService, { ClientProfile } from '../../services/clients'; 
import { ContentStatus } from '../../services/contents'; 

interface Filters {
  clientId?: number | ''; 
  status?: ContentStatus | ''; 
}

const AllContentPage: React.FC = () => {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<Filters>({ clientId: '', status: '' });
  const [clients, setClients] = useState<ClientProfile[]>([]);
  const [loadingClients, setLoadingClients] = useState<boolean>(true);

  // Fetch clients for the filter dropdown
  useEffect(() => {
    const fetchClients = async () => {
      try {
        setLoadingClients(true);
        const data = await clientService.getAll();
        setClients(data);
      } catch (err) {
        console.error('Failed to fetch clients for filter:', err);
        // Handle error appropriately
      } finally {
        setLoadingClients(false);
      }
    };
    fetchClients();
  }, []);

  const handleFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFilters(prev => ({ 
      ...prev, 
      [name]: value === '' ? '' : parseInt(value, 10) // Keep clientId as number or ''
    }));
  };

  const handleStatusFilterClick = (statusValue: ContentStatus | '') => {
     setFilters(prev => ({ ...prev, status: statusValue }));
  };

  return (
    <div className="container mx-auto"> 
      <div className="flex justify-between items-center mb-6 flex-wrap gap-2">
        <h1 className="text-2xl font-bold text-brand-foreground">All Content Pieces</h1>
        <button
          onClick={() => navigate('/admin/content/new')}
          className="btn btn-primary" 
        >
          Create New Content
        </button>
      </div>

      {/* Filters Section - Apply card style */}
      <div className="card mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
           {/* Client Filter */}
           <div>
             <label htmlFor="clientId" className="form-label"> 
               Filter by Client:
             </label>
             <select
               id="clientId"
               name="clientId"
               value={filters.clientId}
               onChange={handleFilterChange}
               disabled={loadingClients}
               className="form-select mt-1 block w-full" // Use new style
             >
               <option value="">All Clients</option>
               {clients.map((client) => (
                 <option key={client.id} value={client.id}>
                   {client.company_name}
                 </option>
               ))}
             </select>
           </div>

           {/* Status Filter */}
           <div className="md:col-span-2">
              <label className="form-label mb-1"> 
                Filter by Status:
              </label>
              <div className="flex flex-wrap gap-2">
                 <button 
                    onClick={() => handleStatusFilterClick('')}
                    // Use correct variable 'filters.status' for comparison
                    className={`btn btn-sm px-3 py-1 ${filters.status === '' ? 'btn-primary' : 'btn-secondary'}`} 
                 >
                    All
                 </button>
                 {Object.values(ContentStatus).map(statusValue => (
                    <button 
                       key={statusValue}
                       onClick={() => handleStatusFilterClick(statusValue)}
                       // Use correct variable 'filters.status' for comparison
                       className={`btn btn-sm px-3 py-1 ${filters.status === statusValue ? 'btn-primary' : 'btn-secondary'}`} 
                    >
                       {statusValue.replace('_', ' ')}
                    </button>
                 ))}
              </div>
           </div>
           {/* TODO: Add Search Input */}
           {/* <div className="md:col-span-1">
              <label htmlFor="search" className="form-label">Search:</label>
              <input type="search" id="search" name="search" className="form-input mt-1" placeholder="Search title, idea..." />
           </div> */}
        </div>
      </div>

      <div className="card overflow-hidden p-0"> {/* Use card style, remove padding */}
        {/* Pass filters to ContentsList */}
        <ContentsList 
          clientId={filters.clientId === '' ? undefined : filters.clientId} 
          status={filters.status === '' ? undefined : filters.status} 
          showActions={true} 
          basePath="/admin/clients" 
        />
      </div>
    </div>
  );
};

export default AllContentPage;
