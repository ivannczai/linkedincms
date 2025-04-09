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
  client_id?: number;
  linkedin_id?: string | null; // Add optional linkedin_id field
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
 * Get current user information using the token
 * @returns Promise with user information
 */
export const getCurrentUser = async (): Promise<UserInfo> => {
  // TODO: Update the backend endpoint /api/v1/auth/test-token
  // to return the linkedin_id field as well.
  const response = await api.post<UserInfo>('/api/v1/auth/test-token');
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
