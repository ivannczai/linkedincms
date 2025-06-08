import api from './api';

interface LinkedInUploadResponse {
  upload_url: string;
  asset: string;
}

const linkedinService = {
  async uploadImage(file: File): Promise<string> {
    // Step 1: Register upload
    const registerResponse = await api.post<LinkedInUploadResponse>('/api/v1/linkedin/assets/register', null, {
      params: {
        file_type: file.type,
        file_size: file.size
      }
    });

    const { upload_url, asset } = registerResponse.data;

    // Step 2: Upload file
    const formData = new FormData();
    formData.append('file', file);

    await api.post(`/api/v1/linkedin/assets/upload/${asset}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });

    return `urn:li:digitalmediaAsset:${asset}`;
  },

  async createPost(content: string, mediaAssets?: string[]) {
    return api.post('/api/v1/linkedin/posts', {
      content,
      media_assets: mediaAssets || []
    });
  }
};

export default linkedinService; 