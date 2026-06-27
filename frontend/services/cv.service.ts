import api from './api';

export const cvService = {
  upload: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/api/cv/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getStatus: async (taskId: string) => {
    const response = await api.get(`/api/cv/status/${taskId}`);
    return response.data;
  },
};
