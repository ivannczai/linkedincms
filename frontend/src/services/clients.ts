import api from './api';

export interface ClientProfile {
  id: number;
  user_id: number;
  company_name: string;
  industry: string;
  website?: string;
  linkedin_url?: string;
  description?: string;
  logo_url?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

// Interface matching the Pydantic schema + user details for creation request body
export interface ClientProfileCreate {
  // user_id is removed, user details are added
  email: string; 
  password: string;
  full_name?: string;
  company_name: string;
  industry: string;
  website?: string;
  linkedin_url?: string;
  description?: string;
  logo_url?: string;
  is_active?: boolean;
}

export interface ClientProfileUpdate {
  company_name?: string;
  industry?: string;
  website?: string;
  linkedin_url?: string;
  description?: string;
  logo_url?: string;
  is_active?: boolean;
}

const clientService = {
  /**
   * Get all client profiles
   * @returns Promise with list of client profiles
   */
  getAll: async (): Promise<ClientProfile[]> => {
    const response = await api.get<ClientProfile[]>('/api/v1/clients/');
    return response.data;
  },

  /**
   * Get a client profile by ID
   * @param id Client profile ID
   * @returns Promise with client profile
   */
  getById: async (id: number): Promise<ClientProfile> => {
    const response = await api.get<ClientProfile>(`/api/v1/clients/${id}`);
    return response.data;
  },

  /**
   * Get the current user's client profile
   * @returns Promise with client profile
   */
  getMyProfile: async (): Promise<ClientProfile> => {
    const response = await api.get<ClientProfile>('/api/v1/clients/me/');
    return response.data;
  },

  /**
   * Create a new client profile
   * @param data Client profile data
   * @returns Promise with created client profile
   */
  create: async (data: ClientProfileCreate): Promise<ClientProfile> => {
    const response = await api.post<ClientProfile>('/api/v1/clients/', data);
    return response.data;
  },

  /**
   * Update a client profile
   * @param id Client profile ID
   * @param data Client profile update data
   * @returns Promise with updated client profile
   */
  update: async (id: number, data: ClientProfileUpdate): Promise<ClientProfile> => {
    const response = await api.put<ClientProfile>(`/api/v1/clients/${id}`, data);
    return response.data;
  },

  /**
   * Delete a client profile
   * @param id Client profile ID
   * @returns Promise with deleted client profile
   */
  delete: async (id: number): Promise<ClientProfile> => {
    const response = await api.delete<ClientProfile>(`/api/v1/clients/${id}`);
    return response.data;
  }
};

export default clientService;
