import React, { useState, useEffect } from 'react';
import { Strategy } from '../../services/strategies';
import strategyService from '../../services/strategies';
// Removed renderMarkdown function and MarkdownPreview import

interface StrategyViewProps {
  strategy?: Strategy;
  clientId?: number;
  onEdit?: () => void;
  isAdmin?: boolean;
}

const StrategyView: React.FC<StrategyViewProps> = ({
  strategy: propStrategy,
  clientId,
  onEdit,
  isAdmin = false
}) => {
  const [strategy, setStrategy] = useState<Strategy | null>(propStrategy || null);
  const [loading, setLoading] = useState<boolean>(!propStrategy && !!clientId);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStrategy = async () => {
      if (propStrategy) {
        setStrategy(propStrategy);
        setLoading(false); // Ensure loading is false if strategy is passed via prop
        return;
      }

      if (!clientId) {
        setError('No strategy or client ID provided');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const fetchedStrategy = await strategyService.getByClientId(clientId);
        setStrategy(fetchedStrategy);
        setError(null); // Clear error on success
      } catch (err) {
        console.error('Error fetching strategy:', err);
        setError('Failed to load strategy. Please try again.');
        setStrategy(null); // Clear strategy on error
      } finally {
        setLoading(false);
      }
    };

    fetchStrategy();
  }, [propStrategy, clientId]);

  if (loading) {
    return <div className="p-4 text-center">Loading strategy...</div>;
  }

  if (error || !strategy) {
    // Provide a button to create if admin and no strategy found
    if (isAdmin && !error && !strategy && onEdit) {
       return (
         <div className="p-6 text-center border border-dashed border-gray-300 rounded-md">
           <p className="text-gray-500 mb-4">No strategy found for this client.</p>
           <button onClick={onEdit} className="btn btn-primary">
             Create Strategy
           </button>
         </div>
       );
    }
    // Otherwise show error or 'not found'
    return <div className="p-4 text-center text-red-500">{error || 'Strategy not found'}</div>;
  }

  return (
    <div className="bg-white shadow overflow-hidden sm:rounded-lg">
      <div className="px-4 py-5 sm:px-6 flex justify-between items-center flex-wrap gap-2">
        <div>
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            {strategy.title}
          </h3>
          <p className="mt-1 max-w-2xl text-sm text-gray-500">
            Last updated: {new Date(strategy.updated_at || strategy.created_at).toLocaleDateString()}
          </p>
        </div>
        {isAdmin && onEdit && (
          <button
            onClick={onEdit}
            className="btn btn-primary" // Use consistent button style
          >
            Edit Strategy
          </button>
        )}
      </div>
      <div className="border-t border-gray-200">
        <div className="px-4 py-5 sm:p-6">
          {/* Render HTML details directly */}
          {/* WARNING: Ensure strategy.details is sanitized on the BACKEND before saving */}
          <div
            className="prose prose-sm sm:prose lg:prose-lg xl:prose-xl max-w-none"
            dangerouslySetInnerHTML={{ __html: strategy.details || '' }}
          />
        </div>
      </div>
      {!strategy.is_active && (
        <div className="px-4 py-3 bg-yellow-50 border-t border-yellow-200">
          <div className="flex">
            <div className="flex-shrink-0">
              {/* Using a simple icon placeholder or install lucide-react if needed */}
              <span className="text-yellow-400">⚠️</span>
            </div>
            <div className="ml-3">
              <p className="text-sm text-yellow-700">
                This strategy is currently inactive.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StrategyView;
