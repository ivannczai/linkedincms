import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import strategyService, { Strategy } from '../../services/strategies';
import contentService, { Content, ContentStatus } from '../../services/contents';
import { Link } from 'react-router-dom';
import StrategyViewModal from '../../components/strategies/StrategyViewModal';
// Removed ContentStatusChart import
import { formatDate } from '../../utils/formatters'; // Import formatDate
import { AlertTriangle, CheckCircle, Clock, FileText } from 'lucide-react'; // Removed Send icon

const ClientDashboard: React.FC = () => {
  const { user } = useAuth();

  // State for strategy
  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [loadingStrategy, setLoadingStrategy] = useState<boolean>(true);
  const [errorStrategy, setErrorStrategy] = useState<string | null>(null);

  // State for content (all for counts, previews)
  const [allContents, setAllContents] = useState<Content[]>([]);
  const [loadingContent, setLoadingContent] = useState<boolean>(true);
  const [errorContent, setErrorContent] = useState<string | null>(null);

  const [isStrategyModalOpen, setIsStrategyModalOpen] = useState(false);

  // Load all data on component mount or when user changes
  useEffect(() => {
    const fetchAllData = async () => {
      if (!user || !user.client_id) {
        setLoadingStrategy(false);
        setLoadingContent(false);
        return;
      }

      setLoadingStrategy(true);
      setLoadingContent(true);
      setErrorStrategy(null);
      setErrorContent(null);

      try {
        // Fetch strategy - Handle 404 gracefully
        try {
          const strategyData = await strategyService.getMyStrategy();
          setStrategy(strategyData);
        } catch (err: any) {
          if (err.response && err.response.status === 404) {
            setStrategy(null);
          } else {
            console.error('Failed to fetch strategy:', err);
            setErrorStrategy('Could not load your content strategy.');
          }
        } finally {
          setLoadingStrategy(false);
        }

        // Fetch all content for counts and previews
        try {
          const allClientContentsData = await contentService.getAll(user.client_id);
           // Filter out DRAFT content as clients shouldn't see it
           const clientVisibleContents = allClientContentsData.filter(c => c.status !== ContentStatus.DRAFT);
          setAllContents(clientVisibleContents);
        } catch (err) {
          console.error('Failed to fetch content data:', err);
          setErrorContent('Could not load content data.');
        } finally {
          setLoadingContent(false);
        }
      } catch (globalError) {
         console.error("Error fetching dashboard data:", globalError);
         setErrorStrategy('Error loading dashboard data.');
         setErrorContent('Error loading dashboard data.');
         setLoadingStrategy(false);
         setLoadingContent(false);
      }
    };

    fetchAllData();
  }, [user]);

  // Calculate counts and previews from the fetched content
  const contentCounts = React.useMemo(() => {
    const counts = { pending: 0, revision: 0, approved: 0, published: 0 };
    allContents.forEach(content => {
      if (content.status === ContentStatus.PENDING_APPROVAL) counts.pending++;
      else if (content.status === ContentStatus.REVISION_REQUESTED) counts.revision++;
      else if (content.status === ContentStatus.APPROVED) counts.approved++;
      else if (content.status === ContentStatus.PUBLISHED) counts.published++;
    });
    return counts;
  }, [allContents]);

  const pendingPreview = React.useMemo(() =>
    allContents
      .filter(c => c.status === ContentStatus.PENDING_APPROVAL)
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()) // Sort by creation date desc
      .slice(0, 3), // Take top 3
    [allContents]
  );

  const approvedPreview = React.useMemo(() =>
    allContents
      .filter(c => c.status === ContentStatus.APPROVED)
      .sort((a, b) => new Date(b.updated_at || b.created_at).getTime() - new Date(a.updated_at || a.created_at).getTime()) // Sort by update/creation desc
      .slice(0, 3), // Take top 3
    [allContents]
  );


  // Combined loading state
  const isLoading = loadingStrategy || loadingContent;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Client Dashboard</h1>
        <p className="text-gray-600">Welcome back, {user?.email}!</p>
      </div>

      {isLoading && (
         <div className="flex justify-center items-center p-8">
           <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600"></div>
         </div>
      )}

      {!isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {/* Strategy Card */}
            <div className="card">
                <h3 className="text-lg font-semibold text-gray-700 mb-2 flex items-center gap-2">
                   <FileText className="w-5 h-5 text-gray-500" /> Your Strategy
                </h3>
                {errorStrategy && <p className="text-red-500 text-sm">{errorStrategy}</p>}
                {strategy && !errorStrategy && (
                    <>
                        <p className="text-gray-600 text-sm mb-3 truncate">{strategy.title}</p>
                        <button
                          onClick={() => setIsStrategyModalOpen(true)}
                          className="text-blue-600 hover:underline text-sm font-medium"
                        >
                          View Details
                        </button>
                    </>
                )}
                {!strategy && !errorStrategy && (
                    <p className="text-gray-500 text-sm">No strategy defined yet.</p>
                )}
            </div>

            {/* Pending Approval Card - Highlighted */}
            <div className="card bg-yellow-50 border-yellow-300 shadow-lg">
                <h3 className="text-lg font-semibold text-yellow-800 mb-2 flex items-center gap-2">
                   <Clock className="w-5 h-5 text-yellow-600" /> Pending Your Approval
                </h3>
                {errorContent && <p className="text-red-500 text-sm">{errorContent}</p>}
                {!errorContent && (
                   <>
                      <p className="text-4xl font-bold text-yellow-700 mb-3">{contentCounts.pending}</p>
                      {pendingPreview.length > 0 && (
                          <ul className="space-y-1.5 text-sm mb-3">
                              {pendingPreview.map(content => (
                                  <li key={content.id} className="flex justify-between items-center">
                                      <Link to={`/client/contents/${content.id}`} className="text-blue-700 hover:underline truncate flex-1 mr-2">
                                          {content.title}
                                      </Link>
                                      {content.due_date && (
                                         <span className="text-xs text-gray-500 whitespace-nowrap">
                                            Due: {formatDate(content.due_date)}
                                         </span>
                                      )}
                                  </li>
                              ))}
                          </ul>
                      )}
                    {contentCounts.pending > 0 ? (
                        <Link to={`/client/library?status=${ContentStatus.PENDING_APPROVAL}`} className="text-blue-600 hover:underline text-sm font-medium">View All Pending</Link>
                    ) : (
                         <p className="text-gray-500 text-sm">Nothing pending approval.</p>
                      )}
                   </>
                )}
            </div>

            {/* Approved - Ready to Post Card - New */}
            <div className="card bg-green-50 border-green-300">
                <h3 className="text-lg font-semibold text-green-800 mb-2 flex items-center gap-2">
                   <CheckCircle className="w-5 h-5 text-green-600" /> Approved - Ready to Post
                </h3>
                {errorContent && <p className="text-red-500 text-sm">{errorContent}</p>}
                {!errorContent && (
                   <>
                      <p className="text-4xl font-bold text-green-700 mb-3">{contentCounts.approved}</p>
                      {approvedPreview.length > 0 && (
                          <ul className="space-y-1.5 text-sm mb-3">
                              {approvedPreview.map(content => (
                                  <li key={content.id}>
                                      <Link to={`/client/contents/${content.id}`} className="text-blue-700 hover:underline truncate block">
                                          {content.title}
                                      </Link>
                                  </li>
                              ))}
                          </ul>
                      )}
                    {contentCounts.approved > 0 ? (
                        <Link to={`/client/library?status=${ContentStatus.APPROVED}`} className="text-blue-600 hover:underline text-sm font-medium">View All Approved</Link>
                    ) : (
                         <p className="text-gray-500 text-sm">No content ready to post.</p>
                      )}
                   </>
                )}
            </div>

            {/* Content Status Overview Card - Simplified */}
             <div className="card md:col-span-3 lg:col-span-3"> {/* Span full width */}
                <h3 className="text-lg font-semibold text-gray-700 mb-3">Content Overview</h3>
                 {errorContent && <p className="text-red-500 text-sm">{errorContent}</p>}
                 {!errorContent && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <Link to={`/client/library?status=${ContentStatus.PENDING_APPROVAL}`} className="text-center p-3 bg-yellow-100 rounded-md hover:bg-yellow-200 transition-colors">
                           <div className="font-bold text-xl text-yellow-800">{contentCounts.pending}</div>
                           <div className="text-yellow-700">Pending Approval</div>
                        </Link>
                         <Link to={`/client/library?status=${ContentStatus.REVISION_REQUESTED}`} className="text-center p-3 bg-red-100 rounded-md hover:bg-red-200 transition-colors">
                           <div className="font-bold text-xl text-red-800 flex items-center justify-center gap-1">
                              {contentCounts.revision > 0 && <AlertTriangle className="w-4 h-4 text-red-600" />}
                              {contentCounts.revision}
                           </div>
                           <div className="text-red-700">Revision Requested</div>
                        </Link>
                         <Link to={`/client/library?status=${ContentStatus.APPROVED}`} className="text-center p-3 bg-green-100 rounded-md hover:bg-green-200 transition-colors">
                           <div className="font-bold text-xl text-green-800">{contentCounts.approved}</div>
                           <div className="text-green-700">Approved</div>
                        </Link>
                         <Link to={`/client/library?status=${ContentStatus.PUBLISHED}`} className="text-center p-3 bg-blue-100 rounded-md hover:bg-blue-200 transition-colors">
                           <div className="font-bold text-xl text-blue-800">{contentCounts.published}</div>
                           <div className="text-blue-700">Published</div>
                        </Link>
                    </div>
                 )}
             </div>
        </div>
      )}

      {/* Strategy Modal */}
      <StrategyViewModal
        strategy={strategy}
        isOpen={isStrategyModalOpen}
        onClose={() => setIsStrategyModalOpen(false)}
      />
    </div>
  );
};

export default ClientDashboard;
