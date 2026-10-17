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

  async updateConversation(id, data) {
    const res = await api.put(`/mentor/conversations/${id}`, data);
    return res.data;
  },

  async sendMessage(conversationId, content) {
    const res = await api.post(`/mentor/conversations/${conversationId}/messages`, { content });
    return res.data;
  },

  async sendMessageStream(conversationId, content, onChunk, onComplete, onError) {
    try {
      const token = localStorage.getItem('idealens_token');
      const response = await fetch(`/api/v1/mentor/conversations/${conversationId}/messages/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ content })
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || `Stream failed with status ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let completedMessage = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // keep partial line in buffer

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data:')) {
            const dataStr = trimmed.slice(5).trim();
            if (dataStr) {
              try {
                const parsed = JSON.parse(dataStr);
                if (parsed.chunk && onChunk) {
                  onChunk(parsed.chunk);
                }
                if (parsed.message) {
                  completedMessage = parsed.message;
                }
              } catch (e) {
                // If not JSON, ignore or log
              }
            }
          }
        }
      }

      if (onComplete) {
        onComplete(completedMessage);
      }
      return completedMessage;
    } catch (err) {
      if (onError) {
        onError(err);
      } else {
        throw err;
      }
    }
  },

  async deleteConversation(id) {
    await api.delete(`/mentor/conversations/${id}`);
  }
};
