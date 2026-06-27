import api from './api';

export const jobService = {
  search: async (keywords: string[]) => {
    const response = await api.post('/api/jobs/search-by-keywords', { keywords });
    return response.data;
  },

  getAll: async () => {
    const response = await api.get('/api/jobs');
    return response.data;
  },

  getById: async (id: number) => {
    const response = await api.get(`/api/jobs/${id}`);
    return response.data;
  },

  findCandidates: async (jobId: number) => {
    const response = await api.post('/api/jobs/find-candidates', { job_id: jobId });
    return response.data;
  },
};
