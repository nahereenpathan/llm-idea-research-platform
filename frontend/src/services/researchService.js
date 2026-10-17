import api from './api';

export const researchService = {
  // --- Academic Papers ---
  async getPaperSources() {
    const res = await api.get('/research/papers/sources');
    return res.data;
  },

  async searchPapers(query, source = 'openalex', yearFrom = null, yearTo = null, searchType = 'keyword', page = 1, limit = 10) {
    const params = {
      query,
      source,
      search_type: searchType,
      page,
      limit
    };
    if (yearFrom) params.year_from = yearFrom;
    if (yearTo) params.year_to = yearTo;
    const res = await api.get('/research/papers/search', { params });
    return res.data;
  },

  async getPaperDetails(paperId) {
    const res = await api.get(`/research/papers/${paperId}`);
    return res.data;
  },

  async savePaper(projectId, paperData) {
    const res = await api.post(`/research/projects/${projectId}/papers/save`, paperData);
    return res.data;
  },

  async getSavedPapers(projectId) {
    const res = await api.get(`/research/projects/${projectId}/papers`);
    return res.data;
  },

  async updatePaper(paperId, data) {
    const res = await api.put(`/research/papers/${paperId}`, data);
    return res.data;
  },

  async deletePaper(paperId) {
    await api.delete(`/research/papers/${paperId}`);
  },

  async summarizePaper(paperId) {
    const res = await api.post(`/research/papers/${paperId}/summarize`);
    return res.data;
  },

  // --- Patents ---
  async getPatentSources() {
    const res = await api.get('/research/patents/sources');
    return res.data;
  },

  async searchPatents(query, source = 'uspto', searchType = 'keyword', page = 1, limit = 10) {
    const params = {
      query,
      source,
      search_type: searchType,
      page,
      limit
    };
    const res = await api.get('/research/patents/search', { params });
    return res.data;
  },

  async getPatentDetails(patentId) {
    const res = await api.get(`/research/patents/${patentId}`);
    return res.data;
  },

  async savePatent(projectId, patentData) {
    const res = await api.post(`/research/projects/${projectId}/patents/save`, patentData);
    return res.data;
  },

  async getSavedPatents(projectId) {
    const res = await api.get(`/research/projects/${projectId}/patents`);
    return res.data;
  },

  async deletePatent(patentId) {
    await api.delete(`/research/patents/${patentId}`);
  }
};
