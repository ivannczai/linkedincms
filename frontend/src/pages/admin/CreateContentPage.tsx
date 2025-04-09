import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ContentForm from '../../components/contents/ContentForm';
import { Content } from '../../services/contents';

const CreateContentPage: React.FC = () => {
  const { clientId } = useParams<{ clientId: string }>();
  const navigate = useNavigate();
  const numericClientId = parseInt(clientId || '0', 10);

  const handleContentCreated = (createdContent: Content) => {
    // Navigate to the detail page of the newly created content
    navigate(`/admin/clients/${numericClientId}/contents/${createdContent.id}`);
  };

  const handleCancel = () => {
    navigate(`/admin/clients/${numericClientId}`);
  };

  if (!numericClientId) {
    return <div className="p-8 text-red-500">Invalid Client ID.</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Create New Content Piece</h1>
        <p className="text-gray-600">Fill in the details for the new content piece.</p>
      </div>
      <ContentForm 
        clientId={numericClientId} 
        onSubmit={handleContentCreated} 
        onCancel={handleCancel} 
      />
    </div>
  );
};

export default CreateContentPage;
