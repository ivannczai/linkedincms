import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
// Removed import for '../types/linkedin'
import { format } from 'date-fns'; // For date formatting

// Define the type locally for now
interface ScheduledLinkedInPostRead {
  id: number;
  user_id: number;
  content_text: string;
  scheduled_at: string; // ISO string format from backend
  status: 'pending' | 'published' | 'failed';
  linkedin_post_id?: string | null;
  error_message?: string | null; // Error message from backend
  created_at: string;
  updated_at: string;
  retry_count?: number; // Include retry_count if needed for display
}

const LinkedInSchedulerPage: React.FC = () => {
  const { user } = useAuth();
  const [contentText, setContentText] = useState('');
  const [scheduledAt, setScheduledAt] = useState(''); // Store as string for input type="datetime-local"
  const [scheduledPosts, setScheduledPosts] = useState<ScheduledLinkedInPostRead[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetchingPosts, setIsFetchingPosts] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fetchScheduledPosts = useCallback(async () => {
    setIsFetchingPosts(true);
    // Clear previous errors when fetching
    setError(null);
    try {
      // Corrected path to include /api/v1 prefix
      const response = await api.get('/api/v1/linkedin/scheduled'); // Adjust limit/skip if needed
      setScheduledPosts(response.data);
    } catch (err: any) {
      console.error('Error fetching scheduled posts:', err);
      setError(err.response?.data?.detail || 'Failed to load scheduled posts.');
    } finally {
      setIsFetchingPosts(false);
    }
  }, []);

  useEffect(() => {
    fetchScheduledPosts();
  }, [fetchScheduledPosts]);

  const handleSchedulePost = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccessMessage(null);

    if (!user) {
      setError('User not found.');
      setIsLoading(false);
      return;
    }

    // Convert local datetime string to UTC ISO string for backend
    let scheduledAtUTC: string | null = null;
    try {
        if (scheduledAt) {
            // Input type="datetime-local" gives string like "YYYY-MM-DDTHH:mm"
            // We need to parse it assuming it's local time and convert to UTC ISO string
            const localDate = new Date(scheduledAt);
            if (isNaN(localDate.getTime())) {
                throw new Error("Invalid date format");
            }
            // Basic check: Ensure the selected local time is in the future
            if (localDate <= new Date()) {
                throw new Error("Scheduled time must be in the future.");
            }
            scheduledAtUTC = localDate.toISOString();
        } else {
             throw new Error("Scheduled date and time are required.");
        }
    } catch (dateError: any) {
         setError(`Invalid date/time: ${dateError.message}`);
         setIsLoading(false);
         return;
    }


    try {
      const payload = {
        content_text: contentText,
        scheduled_at: scheduledAtUTC,
      };
      // The backend endpoint expects user_id in the payload based on ScheduledLinkedInPostCreate
      // Let's add it back, but the backend should still verify it.
      const finalPayload = { ...payload, user_id: user.id };

      // Corrected path to include /api/v1 prefix
      await api.post('/api/v1/linkedin/schedule', finalPayload);
      setSuccessMessage('Post scheduled successfully!');
      setContentText('');
      setScheduledAt('');
      // Refresh the list of posts
      fetchScheduledPosts();
    } catch (err: any) {
      console.error('Error scheduling post:', err);
      setError(err.response?.data?.detail || 'Failed to schedule post.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeletePost = async (postId: number) => {
    if (!window.confirm('Are you sure you want to cancel this scheduled post?')) {
      return;
    }
    setError(null); // Clear previous errors
    setSuccessMessage(null); // Clear previous success messages
    try {
      // Corrected path to include /api/v1 prefix
      await api.delete(`/api/v1/linkedin/schedule/${postId}`);
      setSuccessMessage('Scheduled post cancelled successfully!');
      // Refresh the list
      fetchScheduledPosts();
    } catch (err: any) {
      console.error('Error deleting scheduled post:', err);
      setError(err.response?.data?.detail || 'Failed to cancel scheduled post.');
    }
  };

  // Helper to format date string for display
  const formatDisplayDate = (dateString: string) => {
    try {
      // Display in a more readable local format
      return format(new Date(dateString), "Pp"); // e.g., 09/04/2025, 6:24 PM
    } catch {
      return "Invalid Date";
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-6">Schedule LinkedIn Post</h1>

      {error && <div className="mb-4 p-3 rounded bg-red-100 text-red-800">{error}</div>}
      {successMessage && <div className="mb-4 p-3 rounded bg-green-100 text-green-800">{successMessage}</div>}

      <form onSubmit={handleSchedulePost} className="bg-white p-4 rounded shadow mb-6">
        <div className="mb-4">
          <label htmlFor="contentText" className="block text-sm font-medium text-gray-700 mb-1">
            Post Content
          </label>
          <textarea
            id="contentText"
            rows={5}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            value={contentText}
            onChange={(e) => setContentText(e.target.value)}
            required
            placeholder="Compose your LinkedIn post..."
          />
        </div>
        <div className="mb-4">
          <label htmlFor="scheduledAt" className="block text-sm font-medium text-gray-700 mb-1">
            Schedule Date and Time (Your Local Time)
          </label>
          <input
            type="datetime-local"
            id="scheduledAt"
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            value={scheduledAt}
            onChange={(e) => setScheduledAt(e.target.value)}
            required
            // Set min attribute dynamically to current local time
            min={new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 16)}
          />
           <p className="text-xs text-gray-500 mt-1">The post will be published at this time.</p>
        </div>
        <button
          type="submit"
          disabled={isLoading || !contentText || !scheduledAt}
          className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Scheduling...' : 'Schedule Post'}
        </button>
      </form>

      <h2 className="text-xl font-semibold mb-4">Scheduled Posts</h2>
      {isFetchingPosts ? (
        <p>Loading scheduled posts...</p>
      ) : scheduledPosts.length === 0 ? (
        <p>No posts scheduled yet.</p>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul role="list" className="divide-y divide-gray-200">
            {scheduledPosts.map((post) => (
              <li key={post.id} className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <p className="truncate text-sm font-medium text-gray-800 flex-1 min-w-0">{post.content_text.substring(0, 150)}{post.content_text.length > 150 ? '...' : ''}</p>
                  <div className="flex-shrink-0">
                     <span
                      className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        post.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                        post.status === 'published' ? 'bg-green-100 text-green-800' :
                        'bg-red-100 text-red-800'
                      }`}
                    >
                      {post.status}
                    </span>
                  </div>
                </div>
                <div className="mt-2 sm:flex sm:justify-between">
                  <div className="sm:flex">
                    <p className="flex items-center text-sm text-gray-500">
                      <svg className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                        <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                      </svg>
                      Scheduled for: {formatDisplayDate(post.scheduled_at)}
                    </p>
                  </div>
                  <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                    {post.status === 'pending' && (
                      <button
                        onClick={() => handleDeletePost(post.id)}
                        className="ml-4 text-red-600 hover:text-red-800 font-medium"
                      >
                        Cancel
                      </button>
                    )}
                     {post.status === 'published' && post.linkedin_post_id && (
                        <span className="ml-4 text-xs text-gray-400" title={`LinkedIn Post ID: ${post.linkedin_post_id}`}>Published</span>
                     )}
                     {/* Display error message if status is failed */}
                     {post.status === 'failed' && (
                        <p className="ml-4 text-xs text-red-500" title={post.error_message || 'Unknown error'}>
                          Error: {(post.error_message || 'Unknown error').substring(0, 50)}
                          {(post.error_message || '').length > 50 ? '...' : ''}
                        </p>
                     )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default LinkedInSchedulerPage;
