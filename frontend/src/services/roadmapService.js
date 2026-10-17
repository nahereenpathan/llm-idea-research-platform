import api from './api';

export const roadmapService = {
  async generateRoadmap(projectId, ideaId) {
    const res = await api.post(`/projects/${projectId}/roadmap/generate`, { idea_id: ideaId });
    return res.data;
  },

  async getRoadmaps(projectId) {
    const res = await api.get(`/projects/${projectId}/roadmap`);
    return res.data;
  },

  async updateTaskStatus(projectId, taskId, status) {
    const res = await api.put(`/projects/${projectId}/roadmap/tasks/${taskId}`, { status });
    return res.data;
  }
};
