import api from './api';

export interface Strategy {
  id: number;
  client_id: number;
  title: string;
  details: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface StrategyCreate {
  client_id: number;
  title: string;
  details: string;
  is_active?: boolean;
}

export interface StrategyUpdate {
  title?: string;
  details?: string;
  is_active?: boolean;
}

const strategyService = {
  /**
   * Get all strategies
   * @returns Promise with list of strategies
   */
  getAll: async (): Promise<Strategy[]> => {
    const response = await api.get<Strategy[]>('/api/v1/strategies/');
    return response.data;
  },

  /**
   * Get a strategy by ID
   * @param id Strategy ID
   * @returns Promise with strategy
   */
  getById: async (id: number): Promise<Strategy> => {
    const response = await api.get<Strategy>(`/api/v1/strategies/${id}`);
    return response.data;
  },

  /**
   * Get a strategy by client ID
   * @param clientId Client ID
   * @returns Promise with strategy
   */
  getByClientId: async (clientId: number): Promise<Strategy> => {
    const response = await api.get<Strategy>(`/api/v1/strategies/client/${clientId}`);
    return response.data;
  },

  /**
   * Get the current user's client strategy
   * @returns Promise with strategy
   */
  getMyStrategy: async (): Promise<Strategy> => {
    const response = await api.get<Strategy>('/api/v1/strategies/me/');
    return response.data;
  },

  /**
   * Create a new strategy
   * @param data Strategy data
   * @returns Promise with created strategy
   */
  create: async (data: StrategyCreate): Promise<Strategy> => {
    const response = await api.post<Strategy>('/api/v1/strategies/', data);
    return response.data;
  },

  /**
   * Update a strategy
   * @param id Strategy ID
   * @param data Strategy update data
   * @returns Promise with updated strategy
   */
  update: async (id: number, data: StrategyUpdate): Promise<Strategy> => {
    const response = await api.put<Strategy>(`/api/v1/strategies/${id}`, data);
    return response.data;
  },

  /**
   * Delete a strategy
   * @param id Strategy ID
   * @returns Promise with deleted strategy
   */
  delete: async (id: number): Promise<Strategy> => {
    const response = await api.delete<Strategy>(`/api/v1/strategies/${id}`);
    return response.data;
  }
};

export default strategyService;
