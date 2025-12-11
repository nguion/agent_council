/**
 * API client for Agent Council backend
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const agentCouncilAPI = {
  // Session management
  async createSession(question, files = []) {
    const formData = new FormData();
    formData.append('question', question);
    
    files.forEach(file => {
      formData.append('files', file);
    });
    
    const response = await api.post('/api/sessions', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async listSessions() {
    const response = await api.get('/api/sessions');
    return response.data;
  },

  async getStatus(sessionId) {
    const response = await api.get(`/api/sessions/${sessionId}/status`);
    return response.data;
  },

  async getSummary(sessionId) {
    const response = await api.get(`/api/sessions/${sessionId}/summary`);
    return response.data;
  },

  // Council building
  async buildCouncil(sessionId) {
    const response = await api.post(`/api/sessions/${sessionId}/build_council`);
    return response.data;
  },

  async updateCouncil(sessionId, councilConfig) {
    const response = await api.put(`/api/sessions/${sessionId}/council`, councilConfig);
    return response.data;
  },

  // Execution
  async executeCouncil(sessionId) {
    const response = await api.post(`/api/sessions/${sessionId}/execute`);
    return response.data;
  },

  async getResults(sessionId) {
    const response = await api.get(`/api/sessions/${sessionId}/results`);
    return response.data;
  },

  // Peer review
  async startPeerReview(sessionId) {
    const response = await api.post(`/api/sessions/${sessionId}/peer_review`);
    return response.data;
  },

  async getReviews(sessionId) {
    const response = await api.get(`/api/sessions/${sessionId}/reviews`);
    return response.data;
  },

  // Chairman synthesis
  async synthesize(sessionId) {
    const response = await api.post(`/api/sessions/${sessionId}/synthesize`);
    return response.data;
  },

  // Session management
  async deleteSession(sessionId, hard = false) {
    const response = await api.delete(`/api/sessions/${sessionId}`, {
      params: { hard }
    });
    return response.data;
  },
};

export default api;
