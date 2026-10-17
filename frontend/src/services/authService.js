import api from './api';

export const authService = {
  async register(email, password, full_name) {
    const res = await api.post('/auth/register', { email, password, full_name });
    if (res.data.access_token) {
      localStorage.setItem('idealens_token', res.data.access_token);
      localStorage.setItem('idealens_user', JSON.stringify(res.data.user));
    }
    return res.data;
  },

  async login(email, password) {
    const res = await api.post('/auth/login', { email, password });
    if (res.data.access_token) {
      localStorage.setItem('idealens_token', res.data.access_token);
      localStorage.setItem('idealens_user', JSON.stringify(res.data.user));
    }
    return res.data;
  },

  async getCurrentUser() {
    const res = await api.get('/auth/me');
    localStorage.setItem('idealens_user', JSON.stringify(res.data));
    return res.data;
  },

  logout() {
    localStorage.removeItem('idealens_token');
    localStorage.removeItem('idealens_user');
  },

  getUser() {
    const stored = localStorage.getItem('idealens_user');
    return stored ? JSON.parse(stored) : null;
  },

  isAuthenticated() {
    return !!localStorage.getItem('idealens_token');
  }
};
