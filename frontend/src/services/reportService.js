import api from './api';

export const reportService = {
  async listReports(projectId) {
    const res = await api.get(`/projects/${projectId}/reports`);
    return res.data;
  },

  async generateReport(projectId, data) {
    const res = await api.post(`/projects/${projectId}/reports/generate`, data);
    return res.data;
  },

  async getReport(reportId) {
    const res = await api.get(`/reports/${reportId}`);
    return res.data;
  },

  async updateReport(reportId, data) {
    const res = await api.put(`/reports/${reportId}`, data);
    return res.data;
  },

  async deleteReport(reportId) {
    await api.delete(`/reports/${reportId}`);
  },

  getExportUrl(reportId, format = 'pdf') {
    return `/api/v1/reports/${reportId}/export?format=${format}`;
  }
};
