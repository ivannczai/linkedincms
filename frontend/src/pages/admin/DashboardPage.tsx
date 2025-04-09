import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Content, ContentStatus } from '../../services/contents';
import contentService from '../../services/contents';
import clientService from '../../services/clients';
import { formatDate } from '../../utils/formatters';
import { Users, FileText, CheckCircle, Edit3, Send, Eye } from 'lucide-react'; // Import icons

interface DashboardStats {
  totalClients: number;
  totalContents: number;
  pendingApproval: number;
  needingRevision: number;
  published: number;
}

const AdminDashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats>({
    totalClients: 0,
    totalContents: 0,
    pendingApproval: 0,
    needingRevision: 0,
    published: 0,
  });
  const [recentContents, setRecentContents] = useState<Content[]>([]);
  const [pendingContents, setPendingContents] = useState<Content[]>([]);
  const [revisionContents, setRevisionContents] = useState<Content[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch all clients
        const clients = await clientService.getAll();
        
        // Fetch all contents
        const contents = await contentService.getAll();
        
        // Calculate counts
        const pendingApprovalContents = contents.filter(c => c.status === ContentStatus.PENDING_APPROVAL);
        const revisionRequestedContents = contents.filter(c => c.status === ContentStatus.REVISION_REQUESTED);
        const publishedContents = contents.filter(c => c.status === ContentStatus.PUBLISHED);

        setStats({
          totalClients: clients.length,
          totalContents: contents.length,
          pendingApproval: pendingApprovalContents.length,
          needingRevision: revisionRequestedContents.length,
          published: publishedContents.length,
        });

        // Set recent contents (last 5 created/updated)
        const sortedContents = [...contents].sort(
          (a, b) => new Date(b.updated_at || b.created_at).getTime() - new Date(a.updated_at || a.created_at).getTime()
        );
        setRecentContents(sortedContents.slice(0, 5));
        
        setPendingContents(pendingApprovalContents.slice(0, 5)); // Preview first 5
        setRevisionContents(revisionRequestedContents.slice(0, 5)); // Preview first 5

      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  // Function to get status badge styles (can be moved to utils)
  const getStatusBadgeClass = (status: ContentStatus) => {
    switch (status) {
      case ContentStatus.DRAFT: return 'bg-gray-100 text-gray-600';
      case ContentStatus.PENDING_APPROVAL: return 'bg-yellow-100 text-yellow-700';
      case ContentStatus.REVISION_REQUESTED: return 'bg-red-100 text-red-700';
      case ContentStatus.APPROVED: return 'bg-green-100 text-green-700';
      case ContentStatus.PUBLISHED: return 'bg-blue-100 text-blue-700';
      default: return 'bg-gray-100 text-gray-600';
    }
  };

  // Reusable Stat Card Component
  const StatCard: React.FC<{ title: string; value: number; linkTo?: string; linkText?: string; icon?: React.ElementType; colorClass?: string }> = 
    ({ title, value, linkTo, linkText, icon: Icon, colorClass = 'text-brand-foreground' }) => (
    <div className="card"> {/* Use base card style */}
      <div className="flex justify-between items-start">
        <h3 className="text-gray-500 text-sm font-medium mb-1">{title}</h3>
        {Icon && <Icon className={`h-5 w-5 ${colorClass || 'text-gray-400'}`} />}
      </div>
      <p className={`text-3xl font-bold ${colorClass}`}>{value}</p>
      {linkTo && linkText && (
        <Link to={linkTo} className="text-primary-600 text-sm hover:underline mt-2 inline-block font-medium">
          {linkText}
        </Link>
      )}
    </div>
  );

  // Reusable Content List Item Component
  const ContentListItem: React.FC<{content: Content; actionLink?: string; actionText?: string; actionIcon?: React.ElementType}> = 
    ({content, actionLink, actionText, actionIcon: ActionIcon}) => (
     <div key={content.id} className="px-6 py-4 hover:bg-gray-50">
        <div className="flex justify-between items-start gap-4">
          <div className="flex-1 min-w-0">
            <Link
              to={`/admin/clients/${content.client_id}/contents/${content.id}`}
              className="font-medium text-primary-600 hover:text-primary-800 truncate block"
              title={content.title}
            >
              {content.title}
            </Link>
            <p className="text-sm text-gray-500 mt-1">
              {content.status === ContentStatus.REVISION_REQUESTED ? 'Revision Req:' : 'Updated:'} 
              {formatDate(content.updated_at || content.created_at)}
            </p>
            {content.review_comment && content.status === ContentStatus.REVISION_REQUESTED && (
              <p className="text-sm text-red-600 mt-1 italic truncate" title={content.review_comment}>
                  "{content.review_comment}"
              </p>
            )}
          </div>
          <div className="flex-shrink-0 flex flex-col items-end space-y-1">
             <span
                className={`inline-block px-2.5 py-0.5 text-xs font-medium rounded-full ${getStatusBadgeClass(content.status)}`}
             >
                {content.status.replace('_', ' ')}
             </span>
             {actionLink && actionText && ActionIcon && (
                 <Link
                    to={actionLink}
                    className="text-xs text-primary-600 hover:underline flex items-center"
                 >
                   <ActionIcon className="h-3 w-3 mr-1" /> {actionText}
                 </Link>
             )}
          </div>
        </div>
      </div>
  );


  if (loading) {
    return <div className="flex justify-center p-8"><div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div></div>;
  }

  if (error) {
    return <div className="m-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded">{error}</div>;
  }

  return (
    <div className="container mx-auto"> {/* Removed px-4 py-8, handled by Layout */}
      {/* Removed h1, assuming title comes from Layout/Header */}
      
      {/* Stats Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6 mb-8">
        <StatCard title="Total Clients" value={stats.totalClients} linkTo="/admin/clients" linkText="View Clients" icon={Users} colorClass="text-primary-600"/>
        <StatCard title="Total Content" value={stats.totalContents} linkTo="/admin/content" linkText="View Content" icon={FileText} />
        <StatCard title="Pending Approval" value={stats.pendingApproval} linkTo={`/admin/content?status=${ContentStatus.PENDING_APPROVAL}`} linkText="Review" icon={Send} colorClass="text-yellow-600"/>
        <StatCard title="Needing Revision" value={stats.needingRevision} linkTo={`/admin/content?status=${ContentStatus.REVISION_REQUESTED}`} linkText="Review" icon={Edit3} colorClass="text-red-600"/>
        <StatCard title="Published" value={stats.published} linkTo={`/admin/content?status=${ContentStatus.PUBLISHED}`} linkText="View" icon={CheckCircle} colorClass="text-blue-600"/>
      </div>

      {/* Content Sections Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Recent Content Column */}
        <div className="lg:col-span-1">
           <div className="card overflow-hidden p-0">
             <div className="px-6 py-4 border-b border-gray-200">
               <h2 className="text-lg font-semibold text-gray-800">Recent Activity</h2>
             </div>
             <div className="divide-y divide-gray-200">
               {recentContents.length > 0 ? (
                 recentContents.map((content) => <ContentListItem key={`recent-${content.id}`} content={content} actionLink={`/admin/clients/${content.client_id}`} actionText="View Client" actionIcon={Users}/>)
               ) : (
                 <div className="p-6 text-gray-500 text-center">No recent content activity.</div>
               )}
             </div>
             <div className="bg-gray-50 px-6 py-3 border-t border-gray-200">
               <Link to="/admin/content" className="text-primary-600 hover:text-primary-800 text-sm font-medium">
                 View All Content
               </Link>
             </div>
           </div>
        </div>

        {/* Pending & Revision Column */}
        <div className="lg:col-span-1 space-y-6">
           {/* Pending Approval List */}
           <div className="card overflow-hidden p-0">
             <div className="bg-yellow-50 px-6 py-4 border-b border-yellow-200">
               <h2 className="text-lg font-semibold text-yellow-800">Pending Approval</h2>
             </div>
             <div className="divide-y divide-gray-200">
               {pendingContents.length > 0 ? (
                 pendingContents.map((content) => <ContentListItem key={`pending-${content.id}`} content={content} actionLink={`/admin/clients/${content.client_id}/contents/${content.id}`} actionText="Review" actionIcon={Eye}/>)
               ) : (
                 <div className="p-6 text-gray-500 text-center">No content pending approval.</div>
               )}
             </div>
             {stats.pendingApproval > 0 && (
                <div className="bg-gray-50 px-6 py-3 border-t border-gray-200">
                  <Link to={`/admin/content?status=${ContentStatus.PENDING_APPROVAL}`} className="text-primary-600 hover:text-primary-800 text-sm font-medium">
                    View All Pending ({stats.pendingApproval})
                  </Link>
                </div>
             )}
           </div>

           {/* Needing Revision List */}
           <div className="card overflow-hidden p-0">
             <div className="bg-red-50 px-6 py-4 border-b border-red-200">
               <h2 className="text-lg font-semibold text-red-800">Needing Revision</h2>
             </div>
             <div className="divide-y divide-gray-200">
               {revisionContents.length > 0 ? (
                 revisionContents.map((content) => <ContentListItem key={`revision-${content.id}`} content={content} actionLink={`/admin/clients/${content.client_id}/contents/${content.id}/edit`} actionText="Edit" actionIcon={Edit3}/>)
               ) : (
                 <div className="p-6 text-gray-500 text-center">No content needing revision.</div>
               )}
             </div>
              {stats.needingRevision > 0 && (
                 <div className="bg-gray-50 px-6 py-3 border-t border-gray-200">
                   <Link to={`/admin/content?status=${ContentStatus.REVISION_REQUESTED}`} className="text-primary-600 hover:text-primary-800 text-sm font-medium">
                     View All Needing Revision ({stats.needingRevision})
                   </Link>
                 </div>
              )}
           </div>
        </div>

        {/* Quick Actions Column */}
        <div className="lg:col-span-1">
           <div className="card">
             <h2 className="text-lg font-semibold text-gray-800 mb-4">Quick Actions</h2>
             <div className="space-y-3">
                 <Link
                   to="/admin/content/new" // Link to global content creation
                   className="btn btn-primary w-full block text-center" 
                 >
                   Create New Content
                 </Link>
                 <Link
                   to="/admin/clients/new"
                   className="btn btn-secondary w-full block text-center" 
                 >
                   Add New Client
                 </Link>
                 <Link
                   to="/admin/clients"
                   className="btn btn-ghost w-full block text-center" // Use ghost style
                 >
                   Manage Clients
                 </Link>
               </div>
             </div>
        </div>

      </div>
    </div>
  );
};

export default AdminDashboardPage;
