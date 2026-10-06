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

// Handle 401 responses: clear session and reload (auth context will show login)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        // Only hard-reload if we are not already on the login page
        if (!window.location.pathname.startsWith('/login')) {
          window.location.href = '/login';
        }
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

export interface Incident {
  id: string;
  title: string;
  description: string;
  incident_type: string;
  severity: string;
  status: string;
  latitude: number;
  longitude: number;
  address?: string | null;
  people_at_risk?: number | null;
  vulnerable_people?: number | null;
  injuries_reported?: number | null;
  medical_need: boolean;
  triage_data?: Record<string, unknown> | null;
  triage_confidence?: number | null;
  priority_score?: number | null;
  priority_components?: Record<string, number> | null;
  immediate_needs?: string[] | null;
  reporter_name?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Resource {
  id: string;
  name: string;
  resource_type: string;
  status: string;
  latitude: number;
  longitude: number;
  base_address?: string | null;
  capacity?: number | null;
  capabilities?: string[] | null;
  organization?: string | null;
  max_range_km?: number | null;
}

export interface Recommendation {
  id: string;
  incident_id: string;
  resource_id: string;
  status: string;
  confidence: number;
  estimated_eta_minutes?: number | null;
  compatibility_reasons?: string[] | null;
  reasoning?: string | null;
  human_approval_required: boolean;
  created_at: string;
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

export interface Evidence {
  id: string;
  incident_id: string;
  file_url: string;
  file_name: string;
  evidence_type: string;
  mime_type: string;
  file_size_bytes?: number;
  ai_analysis?: Record<string, unknown> | null;
  created_at: string;
}

export const evidenceAPI = {
  listForIncident: (incidentId: string) =>
    apiClient.get(`/evidence/incident/${incidentId}`),
  upload: (incidentId: string, file: File, analyze: boolean = true) => {
    const form = new FormData();
    form.append('file', file);
    return apiClient.post(`/evidence?incident_id=${incidentId}&analyze=${analyze}`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  analyze: (evidenceId: string) =>
    apiClient.post(`/evidence/${evidenceId}/analyze`),
};

export const auditAPI = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get('/audit/logs', { params }),
};
