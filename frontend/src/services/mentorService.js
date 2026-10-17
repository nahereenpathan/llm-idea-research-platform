import api from './api';

export const mentorService = {
  async listConversations() {
    const res = await api.get('/mentor/conversations');
    return res.data;
  },

  async createConversation(data) {
    const res = await api.post('/mentor/conversations', data);
    return res.data;
  },

  async getConversation(id) {
    const res = await api.get(`/mentor/conversations/${id}`);
    return res.data;
  },

  async sendMessage(conversationId, content) {
    const res = await api.post(`/mentor/conversations/${conversationId}/messages`, { content });
    return res.data;
  },

  async deleteConversation(id) {
    await api.delete(`/mentor/conversations/${id}`);
  }
};
