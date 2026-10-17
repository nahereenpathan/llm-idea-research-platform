import api from './api';

export const ideaService = {
  async listIdeas(projectId) {
    const res = await api.get(`/projects/${projectId}/ideas`);
    return res.data;
  },

  async submitIdea(projectId, data) {
    const res = await api.post(`/projects/${projectId}/ideas`, data);
    return res.data;
  },

  async updateIdea(ideaId, data) {
    const res = await api.put(`/ideas/${ideaId}`, data);
    return res.data;
  },

  async deleteIdea(ideaId) {
    await api.delete(`/ideas/${ideaId}`);
  },

  async selectIdea(ideaId) {
    const res = await api.post(`/ideas/${ideaId}/select`);
    return res.data;
  }
};
