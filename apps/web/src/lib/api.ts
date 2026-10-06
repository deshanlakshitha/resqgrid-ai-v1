import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

// Attach JWT token to every request
apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle 401 responses
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;

// ---- API Functions ----

export const authAPI = {
  login: (email: string, password: string) =>
    apiClient.post('/auth/login', { email, password }),
  register: (data: Record<string, unknown>) =>
    apiClient.post('/auth/register', data),
  getProfile: () => apiClient.get('/auth/me'),
};

export const incidentAPI = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get('/incidents', { params }),
  get: (id: string) => apiClient.get(`/incidents/${id}`),
  create: (data: Record<string, unknown>) =>
    apiClient.post('/incidents', data),
  update: (id: string, data: Record<string, unknown>) =>
    apiClient.patch(`/incidents/${id}`, data),
  runTriage: (id: string) => apiClient.post(`/incidents/${id}/triage`),
  calculatePriority: (id: string) => apiClient.post(`/incidents/${id}/priority`),
  getRecommendations: (id: string) => apiClient.post(`/incidents/${id}/recommendations`),
};

export const resourceAPI = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get('/resources', { params }),
  getAvailable: (params?: Record<string, unknown>) =>
    apiClient.get('/resources/available', { params }),
  get: (id: string) => apiClient.get(`/resources/${id}`),
  create: (data: Record<string, unknown>) =>
    apiClient.post('/resources', data),
};

export const recommendationAPI = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get('/recommendations', { params }),
  approve: (id: string, reason?: string) =>
    apiClient.post(`/recommendations/${id}/approve`, { approved: true, reason }),
  reject: (id: string, reason?: string) =>
    apiClient.post(`/recommendations/${id}/reject`, { approved: false, reason }),
};

export const dashboardAPI = {
  getSummary: () => apiClient.get('/dashboard/summary'),
};

export const hazardAPI = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get('/hazards', { params }),
  create: (data: Record<string, unknown>) =>
    apiClient.post('/hazards', data),
};

export const assistantAPI = {
  query: (question: string) =>
    apiClient.post('/assistant/query', { question }),
};

export const auditAPI = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get('/audit/logs', { params }),
};
