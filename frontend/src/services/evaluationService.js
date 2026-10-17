import api from './api';

export const evaluationService = {
  async evaluateProject(projectId, payload = {}) {
    const res = await api.post(`/projects/${projectId}/evaluate`, payload);
    return res.data;
  },

  async getEvaluation(projectId) {
    const res = await api.get(`/projects/${projectId}/evaluation`);
    return res.data;
  },

  async recalculateWeights(projectId, weights) {
    const res = await api.post(`/projects/${projectId}/recommendation`, { weights });
    return res.data;
  }
};
