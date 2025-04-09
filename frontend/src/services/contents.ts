import { AxiosResponse } from 'axios';
import api from './api';

export interface Content {
  id: number;
  client_id: number;
  title: string;
  idea: string;
  angle: string;
  content_body: string; // This will now be HTML
  status: ContentStatus;
  due_date: string | null;
  is_active: boolean;
  review_comment: string | null;
  published_at: string | null;
  client_rating?: number | null; // Add client_rating
  created_at: string;
  updated_at: string | null;
}

export enum ContentStatus {
  DRAFT = 'DRAFT',
  PENDING_APPROVAL = 'PENDING_APPROVAL',
  REVISION_REQUESTED = 'REVISION_REQUESTED',
  APPROVED = 'APPROVED',
  PUBLISHED = 'PUBLISHED',
}

export interface ContentCreateInput {
  client_id: number;
  title: string;
  idea: string;
  angle: string;
  content_body: string; // Send HTML
  due_date?: string;
  is_active?: boolean;
}

export interface ContentUpdateInput {
  title?: string;
  idea?: string;
  angle?: string;
  content_body?: string; // Send HTML
  status?: ContentStatus;
  due_date?: string | null;
  is_active?: boolean;
}

// Define allowed sort fields for type safety
export type ContentSortField = 'created_at' | 'updated_at' | 'due_date' | 'title' | 'status';
export type SortOrder = 'asc' | 'desc';

const contentService = {
  /**
   * Get all content pieces
   * @param clientId Optional client ID to filter by
   * @param status Optional status to filter by
   * @param sortBy Optional field to sort by
   * @param sortOrder Optional sort order ('asc' or 'desc')
   * @returns Promise with content pieces
   */
  getAll: async (
    clientId?: number,
    status?: ContentStatus,
    sortBy?: ContentSortField, // Add sortBy parameter
    sortOrder?: SortOrder // Add sortOrder parameter
  ): Promise<Content[]> => {
    let url = '/api/v1/contents/';
    // Use URLSearchParams for cleaner parameter handling
    const params = new URLSearchParams();

    if (clientId) {
      params.append('client_id', clientId.toString());
    }
    if (status) {
      params.append('status', status);
    }
    if (sortBy) {
      params.append('sort_by', sortBy);
    }
    if (sortOrder) {
      params.append('sort_order', sortOrder);
    }
    // Add skip/limit if needed later, for now fetch all relevant for client dashboard/library
    // params.append('limit', '200'); // Example: Fetch more if needed

    const response: AxiosResponse<Content[]> = await api.get(url, { params });
    return response.data;
  },

  /**
   * Get a content piece by ID
   * @param id Content piece ID
   * @returns Promise with content piece
   */
  getById: async (id: number): Promise<Content> => {
    const response: AxiosResponse<Content> = await api.get(`/api/v1/contents/${id}`);
    return response.data;
  },

  /**
   * Create a new content piece
   * @param data Content piece data
   * @returns Promise with created content piece
   */
  create: async (data: ContentCreateInput): Promise<Content> => {
    const response: AxiosResponse<Content> = await api.post('/api/v1/contents/', data);
    return response.data;
  },

  /**
   * Update a content piece
   * @param id Content piece ID
   * @param data Content piece data to update
   * @returns Promise with updated content piece
   */
  update: async (id: number, data: ContentUpdateInput): Promise<Content> => {
    const response: AxiosResponse<Content> = await api.put(
      `/api/v1/contents/${id}`,
      data
    );
    return response.data;
  },

  /**
   * Delete a content piece
   * @param id Content piece ID
   * @returns Promise with deleted content piece
   */
  delete: async (id: number): Promise<Content> => {
    const response: AxiosResponse<Content> = await api.delete(
      `/api/v1/contents/${id}`
    );
    return response.data;
  },

  /**
   * Submit a content piece for approval
   * @param id Content piece ID
   * @returns Promise with updated content piece
   */
  submitForApproval: async (id: number): Promise<Content> => {
    const response: AxiosResponse<Content> = await api.post(
      `/api/v1/contents/${id}/submit`
    );
    return response.data;
  },

  /**
   * Approve a content piece
   * @param id Content piece ID
   * @returns Promise with updated content piece
   */
  approve: async (id: number): Promise<Content> => {
    const response: AxiosResponse<Content> = await api.post(
      `/api/v1/contents/${id}/approve`
    );
    return response.data;
  },

  /**
   * Request revision for a content piece
   * @param id Content piece ID
   * @param reviewComment Review comment
   * @returns Promise with updated content piece
   */
  requestRevision: async (
    id: number,
    reviewComment: string
  ): Promise<Content> => {
    // Send comment in the request body, matching the backend expectation
    const response: AxiosResponse<Content> = await api.post(
      `/api/v1/contents/${id}/request-revision`,
      { review_comment: reviewComment } // Send as JSON body
      // Removed the params option
    );
    return response.data;
  },

  /**
   * Publish a content piece
   * @param id Content piece ID
   * @returns Promise with updated content piece
   */
  publish: async (id: number): Promise<Content> => {
    const response: AxiosResponse<Content> = await api.post(
      `/api/v1/contents/${id}/publish`
    );
    return response.data;
  },

  /**
   * Get content pieces for a client that are pending approval
   * @param clientId Client ID
   * @returns Promise with content pieces
   */
  getPendingApproval: async (clientId: number): Promise<Content[]> => {
    // Add default sorting if needed, e.g., by due date ascending
    return contentService.getAll(clientId, ContentStatus.PENDING_APPROVAL, 'due_date', 'asc');
  },

  /**
   * Get content pieces for a client that need revision
   * @param clientId Client ID
   * @returns Promise with content pieces
   */
  getNeedingRevision: async (clientId: number): Promise<Content[]> => {
     // Add default sorting if needed, e.g., by updated date descending
    return contentService.getAll(clientId, ContentStatus.REVISION_REQUESTED, 'updated_at', 'desc');
  },

  /**
   * Mark a content piece as posted (changes status to PUBLISHED)
   * @param id Content piece ID
   * @returns Promise with updated content piece
   */
  markAsPosted: async (id: number): Promise<Content> => {
    const response: AxiosResponse<Content> = await api.post(
      `/api/v1/contents/${id}/mark-as-posted`
    );
    return response.data;
  },

  /**
   * Rate a content piece
   * @param id Content piece ID
   * @param rating Rating value (0-5)
   * @returns Promise with updated content piece
   */
  rate: async (id: number, rating: number): Promise<Content> => {
    const response: AxiosResponse<Content> = await api.post(
      `/api/v1/contents/${id}/rate`,
      { rating } // Send rating in the request body
    );
    return response.data;
  },
};

export default contentService;
