import api from './api';

export const candidateService = {
  getAll: async () => {
    const response = await api.get('/api/candidates');
    return response.data;
  },

  getById: async (id: number) => {
    const response = await api.get(`/api/candidates/${id}`);
    return response.data;
  },

  getMatches: async (id: number) => {
    const response = await api.get(`/api/candidates/${id}/matches`);
    return response.data;
  },
};
