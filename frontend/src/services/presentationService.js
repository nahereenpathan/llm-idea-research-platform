import api from './api';

export const presentationService = {
  async listPresentations(projectId) {
    const res = await api.get(`/projects/${projectId}/presentations`);
    return res.data;
  },

  async generatePresentation(projectId, data) {
    const res = await api.post(`/projects/${projectId}/presentations/generate`, data);
    return res.data;
  },

  async getPresentation(presentationId) {
    const res = await api.get(`/presentations/${presentationId}`);
    return res.data;
  },

  async updatePresentation(presentationId, data) {
    const res = await api.put(`/presentations/${presentationId}`, data);
    return res.data;
  },

  async deletePresentation(presentationId) {
    await api.delete(`/presentations/${presentationId}`);
  },

  async addSlide(presentationId, data) {
    const res = await api.post(`/presentations/${presentationId}/slides`, data);
    return res.data;
  },

  async updateSlide(slideId, data) {
    const res = await api.put(`/slides/${slideId}`, data);
    return res.data;
  },

  async deleteSlide(slideId) {
    await api.delete(`/slides/${slideId}`);
  },

  getExportUrl(presentationId, format = 'pptx') {
    return `/api/v1/presentations/${presentationId}/export?format=${format}`;
  }
};
