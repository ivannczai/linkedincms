import api from './api';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'admin' | 'client';
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface UserCreate {
  email: string;
  full_name: string;
  password: string;
  role: 'admin' | 'client';
  is_active?: boolean;
}

export interface UserUpdate {
  email?: string;
  full_name?: string;
  password?: string;
  is_active?: boolean;
}

/**
 * Get all users
 * @returns Promise with list of users
 */
export const getUsers = async (): Promise<User[]> => {
  const response = await api.get<User[]>('/api/v1/users/');
  return response.data;
};

/**
 * Get a user by ID
 * @param id User ID
 * @returns Promise with user
 */
export const getUser = async (id: number): Promise<User> => {
  const response = await api.get<User>(`/api/v1/users/${id}`);
  return response.data;
};

/**
 * Create a new user
 * @param data User data
 * @returns Promise with created user
 */
export const createUser = async (data: UserCreate): Promise<User> => {
  const response = await api.post<User>('/api/v1/users/', data);
  return response.data;
};

/**
 * Update a user
 * @param id User ID
 * @param data User update data
 * @returns Promise with updated user
 */
export const updateUser = async (id: number, data: UserUpdate): Promise<User> => {
  const response = await api.put<User>(`/api/v1/users/${id}`, data);
  return response.data;
};

/**
 * Get client users
 * @returns Promise with list of client users
 */
export const getClientUsers = async (): Promise<User[]> => {
  const users = await getUsers();
  return users.filter(user => user.role === 'client');
};
