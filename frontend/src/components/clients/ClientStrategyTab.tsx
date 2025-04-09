import React, { useState, useEffect } from 'react';
import { ClientProfile } from '../../services/clients';
import strategyService, { Strategy, StrategyCreate, StrategyUpdate } from '../../services/strategies'; // Use correct types
import StrategyForm from '../strategies/StrategyForm';
import StrategyView from '../strategies/StrategyView';
import { Edit } from 'lucide-react'; 

interface ClientStrategyTabProps {
  client: ClientProfile;
}

const ClientStrategyTab: React.FC<ClientStrategyTabProps> = ({ client }) => {
  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState<boolean>(false);

  // Load client's strategy on component mount or when client changes
  useEffect(() => {
    const fetchStrategy = async () => {
      try {
        setLoading(true);
        setError(null); 
        const data = await strategyService.getByClientId(client.id);
        setStrategy(data);
      } catch (err: any) {
        console.error('Failed to fetch strategy:', err);
        if (err.response && err.response.status === 404) {
          setStrategy(null); 
        } else {
          setError('Failed to load content strategy. Please try again later.');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchStrategy();
  }, [client.id]);

  // Handle strategy creation/update submission from StrategyForm
  const handleSubmitStrategy = async (data: StrategyCreate | StrategyUpdate) => { // Use correct types
    try {
      let updatedOrNewStrategy: Strategy;
      if (strategy && isEditing) {
        // Update existing strategy
        updatedOrNewStrategy = await strategyService.update(strategy.id, data as StrategyUpdate); // Use correct type
      } else {
        // Create new strategy
        updatedOrNewStrategy = await strategyService.create({
          ...data, 
          client_id: client.id, 
        } as StrategyCreate); // Use correct type
      }
      setStrategy(updatedOrNewStrategy);
      setIsEditing(false); 
    } catch (err) {
      console.error('Failed to save strategy:', err);
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

  if (error) {
    return (
      <div className="p-4 mb-4 text-sm text-red-700 bg-red-100 rounded-lg border border-red-300" role="alert">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header section with Edit/Create button */}
      {!isEditing && (
         <div className="flex justify-between items-center">
           <h2 className="text-xl font-semibold text-brand-foreground">Content Strategy</h2>
           <button
             onClick={() => setIsEditing(true)}
             className={`btn ${strategy ? 'btn-secondary' : 'btn-primary'} btn-sm`} 
           >
             {strategy ? <><Edit className="mr-1.5 h-4 w-4" /> Edit Strategy</> : 'Create Strategy'}
           </button>
         </div>
      )}

      {/* Display Area */}
      {isEditing ? (
        // Show Form when editing or creating
        <div className="card"> 
          <StrategyForm
            strategy={strategy || undefined} 
            clientId={client.id} 
            onSubmit={handleSubmitStrategy}
            isEdit={!!strategy} 
            onCancel={() => setIsEditing(false)} // Pass cancel handler
          />
        </div>
      ) : strategy ? (
        // Show View component if strategy exists and not editing
        <StrategyView 
          strategy={strategy} 
          isAdmin={true} 
        />
      ) : (
        // Show message if no strategy and not editing
        <div className="card text-center py-8">
          <p className="text-gray-500">
            No content strategy has been created for this client yet.
          </p>
        </div>
      )}
    </div>
  );
};

export default ClientStrategyTab;
