import api, { API_BASE_URL } from './api';

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
    const token = localStorage.getItem('idealens_token');
    return `${API_BASE_URL}/reports/${reportId}/export?format=${format}${token ? `&token=${token}` : ''}`;
  },

  getCsvExportUrl(projectId) {
    const token = localStorage.getItem('idealens_token');
    return `${API_BASE_URL}/projects/${projectId}/export/csv${token ? `?token=${token}` : ''}`;
  },

  async downloadReportExport(reportId, format = 'pdf', title = 'report') {
    const res = await api.get(`/reports/${reportId}/export?format=${format}`, {
      responseType: 'blob',
    });
    const blob = new Blob([res.data]);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const ext = format === 'latex' ? 'tex' : format;
    const cleanTitle = (title || 'report').replace(/[^\w-]/g, '_');
    link.setAttribute('download', `${cleanTitle}.${ext}`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  async downloadCsvExport(projectId, title = 'evaluation_scores') {
    const res = await api.get(`/projects/${projectId}/export/csv`, {
      responseType: 'blob',
    });
    const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const cleanTitle = (title || 'scores').replace(/[^\w-]/g, '_');
    link.setAttribute('download', `${cleanTitle}_evaluation_scores.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  }
};
