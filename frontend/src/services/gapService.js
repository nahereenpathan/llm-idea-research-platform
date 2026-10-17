import api from './api';

export const gapService = {
  async generateGapAnalysis(projectId, ideaId) {
    const res = await api.post(`/projects/${projectId}/gaps/generate`, { idea_id: ideaId });
    return res.data;
  },

  async getGapAnalyses(projectId) {
    const res = await api.get(`/projects/${projectId}/gaps`);
    return res.data;
  }
};
