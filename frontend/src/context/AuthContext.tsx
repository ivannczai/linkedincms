import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react'; // Import useCallback
// Remove unused getToken import
import { getCurrentUser, isAuthenticated, login, LoginCredentials, removeToken, setToken, UserInfo } from '../services/auth';

// Export the type
export interface AuthContextType {
  user: UserInfo | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  error: string | null;
  refetchUser: () => Promise<void>; // Add refetchUser function type
}

// Export the context
export const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Function to fetch user data
  const fetchUser = useCallback(async () => {
    if (isAuthenticated()) {
      try {
        const userData = await getCurrentUser();
        setUser(userData);
        setError(null); // Clear error on successful fetch
      } catch (err) {
        console.error('Failed to get user data:', err);
        setError('Failed to fetch user data.'); // Set error state
        // If token is invalid, remove it
        removeToken();
        setUser(null); // Clear user state
      }
    }
    setIsLoading(false); // Set loading false after attempt
  }, []);


  // Check if user is authenticated on mount
  useEffect(() => {
    setIsLoading(true); // Set loading true before check
    fetchUser();
  }, [fetchUser]);

  const handleLogin = async (credentials: LoginCredentials) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await login(credentials);
      setToken(response.access_token);
      // Fetch user data after successful login
      await fetchUser();
    } catch (err) {
      console.error('Login failed:', err);
      setError('Login failed. Please check your credentials and try again.');
      removeToken();
      setUser(null); // Ensure user is null on failed login
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    removeToken();
    setUser(null);
    setError(null); // Clear error on logout
  };

  // Expose refetchUser function
  const handleRefetchUser = useCallback(async () => {
    setIsLoading(true); // Indicate loading during refetch
    await fetchUser();
  }, [fetchUser]);


  const value = {
    user,
    isLoading,
    isAuthenticated: !!user && !isLoading, // Consider loading state for isAuthenticated
    login: handleLogin,
    logout: handleLogout,
    error,
    refetchUser: handleRefetchUser, // Add refetchUser to context value
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
