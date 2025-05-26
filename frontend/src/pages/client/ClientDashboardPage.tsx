import React, { useState, useEffect } from 'react';
import ContentCard from '../../components/contents/ContentCard';
import { Content, ContentStatus } from '../../services/contents';
import contentService from '../../services/contents';

interface ClientDashboardPageProps {
  clientId: number;
}

const ClientDashboardPage: React.FC<ClientDashboardPageProps> = ({ clientId }) => {
  const [approvedContents, setApprovedContents] = useState<Content[]>([]);
  const [scheduledContents, setScheduledContents] = useState<Content[]>([]);

  const handleMarkAsPosted = async (contentId: number) => {
    try {
      await contentService.markAsPosted(contentId);
      // Refresh content lists
      fetchContents();
    } catch (error) {
      console.error('Failed to mark content as posted:', error);
    }
  };

  const fetchContents = async () => {
    try {
      const [approved, scheduled] = await Promise.all([
        contentService.getAll(clientId, ContentStatus.APPROVED),
        contentService.getAll(clientId, ContentStatus.SCHEDULED)
      ]);
      setApprovedContents(approved);
      setScheduledContents(scheduled);
    } catch (error) {
      console.error('Failed to fetch contents:', error);
    }
  };

  useEffect(() => {
    fetchContents();
  }, [clientId]);

  return (
    <div className="space-y-6">
      {/* Approved Content Card */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Approved Content</h3>
        <div className="space-y-4">
          {approvedContents.map((content) => (
            <ContentCard
              key={content.id}
              content={content}
              basePath="/client"
              onMarkAsPosted={handleMarkAsPosted}
            />
          ))}
        </div>
      </div>

      {/* Scheduled Content Card */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Scheduled Content</h3>
        <div className="space-y-4">
          {scheduledContents.map((content) => (
            <ContentCard
              key={content.id}
              content={content}
              basePath="/client"
              onMarkAsPosted={handleMarkAsPosted}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default ClientDashboardPage; 