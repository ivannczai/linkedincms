import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext'; // Assuming useAuth provides user info
import api from '../services/api'; // Corrected: Use default import

const SettingsPage: React.FC = () => {
  const { user, refetchUser } = useAuth(); // Get user info and refetch function
  const location = useLocation();
  const [isLoading, setIsLoading] = useState(false);
  // Initialize based on user data if available, otherwise checking
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'not_connected' | 'checking'>(
    user ? (user.linkedin_id ? 'connected' : 'not_connected') : 'checking'
  );
  const [feedbackMessage, setFeedbackMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Update status based on user data from context
  useEffect(() => {
    if (user) {
      setConnectionStatus(user.linkedin_id ? 'connected' : 'not_connected');
    } else {
      // If user becomes null (e.g., logout), set to not connected
      setConnectionStatus('not_connected');
    }
  }, [user]); // Rerun when user object changes

  // Check for callback status from URL query parameters
  useEffect(() => {
    const queryParams = new URLSearchParams(location.search);
    const status = queryParams.get('linkedin_status');
    const detail = queryParams.get('detail');

    if (status === 'success') {
      setFeedbackMessage({ type: 'success', text: 'LinkedIn account connected successfully!' });
      // Trigger user refetch to get updated linkedin_id
      refetchUser().then(() => {
         // Status will update via the other useEffect watching the user object
         console.log("User refetched after LinkedIn connect.");
      });
      // Optionally clear query params from URL
      window.history.replaceState({}, document.title, location.pathname);
    } else if (status === 'error') {
      setFeedbackMessage({ type: 'error', text: `Failed to connect LinkedIn account: ${detail || 'Unknown error'}` });
      setConnectionStatus('not_connected'); // Ensure status reflects failure
      // Optionally clear query params from URL
      window.history.replaceState({}, document.title, location.pathname);
    }
    // Only run this effect when location.search changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.search, refetchUser]); // Add refetchUser to dependency array

  const handleConnectLinkedIn = async () => {
    setIsLoading(true);
    setFeedbackMessage(null);
    try {
      // Call the backend endpoint to get the authorization URL
      // Corrected path to include /api/v1 prefix
      const response = await api.get('/api/v1/linkedin/connect');
      const authUrl = response.data.authorization_url;

      if (authUrl) {
        // Redirect the user to the LinkedIn authorization page
        window.location.href = authUrl;
      } else {
        throw new Error('Authorization URL not received from backend.');
      }
      // No need to setIsLoading(false) here as the page will redirect
    } catch (error: any) {
      console.error('Error initiating LinkedIn connection:', error);
      setFeedbackMessage({ type: 'error', text: `Error initiating connection: ${error.response?.data?.detail || error.message}` });
      setIsLoading(false);
    }
  };

  // TODO: Implement disconnect functionality
  // const handleDisconnectLinkedIn = async () => { ... }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-6">Settings</h1>

      {feedbackMessage && (
        <div
          className={`mb-4 p-3 rounded ${
            feedbackMessage.type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}
        >
          {feedbackMessage.text}
        </div>
      )}

      <div className="bg-white p-4 rounded shadow mb-6">
        <h2 className="text-xl font-medium mb-4">Integrations</h2>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg">LinkedIn Account</h3>
            {connectionStatus === 'checking' && <p className="text-gray-500">Checking status...</p>}
            {connectionStatus === 'connected' && <p className="text-green-600">Connected</p>}
            {connectionStatus === 'not_connected' && <p className="text-red-600">Not Connected</p>}
          </div>
          {connectionStatus === 'not_connected' && (
            <button
              onClick={handleConnectLinkedIn}
              disabled={isLoading}
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50"
            >
              {isLoading ? 'Connecting...' : 'Connect LinkedIn Account'}
            </button>
          )}
           {connectionStatus === 'connected' && (
            <button
              // onClick={handleDisconnectLinkedIn} // TODO: Implement disconnect
              disabled={true} // TODO: Enable when disconnect is implemented
              className="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50"
            >
              Disconnect (Not Implemented)
            </button>
          )}
        </div>
      </div>

      {/* Other settings sections can be added here */}
    </div>
  );
};

export default SettingsPage;
