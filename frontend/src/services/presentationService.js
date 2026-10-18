import api, { API_BASE_URL } from './api';

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
    const token = localStorage.getItem('idealens_token');
    return `${API_BASE_URL}/presentations/${presentationId}/export?format=${format}${token ? `&token=${token}` : ''}`;
  },

  async downloadPptxExport(presentationId, title = 'presentation') {
    const res = await api.get(`/presentations/${presentationId}/export?format=pptx`, {
      responseType: 'blob',
    });
    const blob = new Blob([res.data], {
      type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const cleanTitle = (title || 'presentation').replace(/[^\w-]/g, '_');
    link.setAttribute('download', `${cleanTitle}.pptx`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  }
};
