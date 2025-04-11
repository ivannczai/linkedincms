import api from './api';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface UserInfo {
  id: number;
  email: string;
  role: 'admin' | 'client';
  client_id?: number; // client_id IS defined here as optional
  linkedin_id?: string | null; // Add optional linkedin_id field
  // Add other fields from UserRead if needed by the frontend context
  full_name: string;
  is_active: boolean;
}

/**
 * Login user with email and password
 * @param credentials User credentials
 * @returns Promise with login response containing access token
 */
export const login = async (credentials: LoginCredentials): Promise<LoginResponse> => {
  // Convert credentials to form data format for OAuth2 compatibility
  const formData = new FormData();
  formData.append('username', credentials.username);
  formData.append('password', credentials.password);

  const response = await api.post<LoginResponse>('/api/v1/auth/token', formData);
  return response.data;
};

/**
 * Get current user information using the token by calling the /users/me endpoint.
 * @returns Promise with user information (including client_id if applicable).
 */
export const getCurrentUser = async (): Promise<UserInfo> => {
  // Call the correct endpoint that returns the UserRead schema
  const response = await api.get<UserInfo>('/api/v1/users/me');
  // The backend now explicitly adds client_id to the response for client users
  return response.data;
};

/**
 * Store authentication token in local storage
 * @param token JWT token
 */
export const setToken = (token: string): void => {
  localStorage.setItem('token', token);
};

/**
 * Get authentication token from local storage
 * @returns JWT token or null if not found
 */
export const getToken = (): string | null => {
  return localStorage.getItem('token');
};

/**
 * Remove authentication token from local storage
 */
export const removeToken = (): void => {
  localStorage.removeItem('token');
};

/**
 * Check if user is authenticated (has token)
 * @returns True if user is authenticated
 */
export const isAuthenticated = (): boolean => {
  return !!getToken();
};
