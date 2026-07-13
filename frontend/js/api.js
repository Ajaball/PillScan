/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — API Client
   Fetch wrapper with JWT auth, auto-refresh, and error handling
   ═══════════════════════════════════════════════════════════════════ */

import storage from './storage.js';

// In production the frontend (pillscan-web) and backend (pillscan-api) live on
// different Render subdomains, so we call the backend by its ABSOLUTE URL.
// Using a same-origin proxy caused FastAPI's trailing-slash 307 redirect to
// bounce cross-origin, which made the browser drop the Authorization header
// (→ 403). Talking to the backend directly keeps that redirect same-origin, so
// the auth header survives. CORS on the backend already allows this origin.
// Override at runtime by setting window.PILLSCAN_API_BASE before this loads.
const API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ? 'http://localhost:8005/api/v1'
  : (window.PILLSCAN_API_BASE || 'https://pillscan-api.onrender.com/api/v1');

class ApiClient {
  constructor() {
    this.baseUrl = API_BASE;
    this.isRefreshing = false;
    this.refreshQueue = [];
  }

  /** Build full URL */
  url(path) {
    return `${this.baseUrl}${path}`;
  }

  /** Get auth headers */
  getHeaders(isFormData = false) {
    const headers = {};
    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }
    const token = storage.getAccessToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  /** Core request method */
  async request(method, path, options = {}) {
    const { body, isFormData = false, skipAuth = false, retried = false } = options;

    const headers = skipAuth ? { 'Content-Type': 'application/json' } : this.getHeaders(isFormData);

    const config = {
      method,
      headers,
    };

    if (body) {
      config.body = isFormData ? body : JSON.stringify(body);
    }

    try {
      const response = await fetch(this.url(path), config);

      // Handle 401 — try token refresh
      if (response.status === 401 && !skipAuth && !retried) {
        const refreshed = await this.refreshToken();
        if (refreshed) {
          return this.request(method, path, { ...options, retried: true });
        }
        // Refresh failed — redirect to login
        storage.clearTokens();
        window.dispatchEvent(new CustomEvent('auth:logout'));
        throw new ApiError('Session expired', 401);
      }

      // Parse response
      const data = await this.parseResponse(response);

      if (!response.ok) {
        throw new ApiError(data.detail || data.message || 'Request failed', response.status, data);
      }

      return data;
    } catch (error) {
      if (error instanceof ApiError) throw error;
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new ApiError('No internet connection', 0);
      }
      throw new ApiError(error.message || 'Unknown error', 0);
    }
  }

  /** Parse response body */
  async parseResponse(response) {
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return response.json();
    }
    return response.text();
  }

  /** Refresh access token */
  async refreshToken() {
    if (this.isRefreshing) {
      return new Promise((resolve) => {
        this.refreshQueue.push(resolve);
      });
    }

    this.isRefreshing = true;
    const refreshToken = storage.getRefreshToken();

    if (!refreshToken) {
      this.isRefreshing = false;
      return false;
    }

    try {
      const response = await fetch(this.url('/auth/refresh'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(refreshToken),
      });

      if (!response.ok) {
        this.isRefreshing = false;
        this.refreshQueue.forEach(cb => cb(false));
        this.refreshQueue = [];
        return false;
      }

      const data = await response.json();
      storage.setTokens(data.access_token, data.refresh_token);

      this.isRefreshing = false;
      this.refreshQueue.forEach(cb => cb(true));
      this.refreshQueue = [];
      return true;
    } catch {
      this.isRefreshing = false;
      this.refreshQueue.forEach(cb => cb(false));
      this.refreshQueue = [];
      return false;
    }
  }

  // ── Convenience Methods ───────────────────────────────────────

  get(path, options)  { return this.request('GET', path, options); }
  post(path, body, options = {})   { return this.request('POST', path, { ...options, body }); }
  put(path, body, options = {})    { return this.request('PUT', path, { ...options, body }); }
  delete(path, options) { return this.request('DELETE', path, options); }

  /** Upload file (FormData) */
  upload(path, formData) {
    return this.request('POST', path, { body: formData, isFormData: true });
  }

  // ── Auth Endpoints ────────────────────────────────────────────

  async login(email, password) {
    const data = await this.post('/auth/login', { email, password }, { skipAuth: true });
    storage.setTokens(data.access_token, data.refresh_token);
    return data;
  }

  async register(userData) {
    return this.post('/auth/register', userData, { skipAuth: true });
  }

  async forgotPassword(email) {
    return this.post('/auth/forgot-password', { email }, { skipAuth: true });
  }

  async resetPassword(email, otp, newPassword) {
    return this.post('/auth/reset-password', {
      email, otp, new_password: newPassword
    }, { skipAuth: true });
  }

  async getProfile() {
    const user = await this.get('/users/me');
    storage.setUser(user);
    return user;
  }

  async updateProfile(data) {
    const user = await this.put('/users/me', data);
    storage.setUser(user);
    return user;
  }

  async deleteAccount() {
    return this.delete('/auth/account');
  }

  // ── AI Settings (Leaflet Summarizer API keys) ─────────────────

  /** Get the user's AI settings status (never returns raw keys) */
  getAISettings() {
    return this.get('/users/me/ai-settings');
  }

  /**
   * Update the user's AI settings.
   * @param {{gemini_api_key?: string, gemini_api_key_2?: string, gemini_api_key_3?: string, gemini_api_key_4?: string, gemini_api_key_5?: string}} data
   * Send a key string to set it, "" to clear it, omit to leave unchanged.
   */
  updateAISettings(data) {
    return this.put('/users/me/ai-settings', data);
  }

  // ── Drug Endpoints ────────────────────────────────────────────

  searchDrugs(query = '', filters = {}) {
    const params = new URLSearchParams();
    if (query) params.set('q', query);
    if (filters.shape) params.set('shape', filters.shape);
    if (filters.color) params.set('color', filters.color);
    if (filters.category) params.set('category', filters.category);
    return this.get(`/drugs/search?${params.toString()}`);
  }

  getDrug(drugId) {
    return this.get(`/drugs/${drugId}`);
  }

  // ── Scan Endpoints ────────────────────────────────────────────

  async scanPill(imageFile) {
    const formData = new FormData();
    formData.append('image', imageFile);
    return this.upload('/scan/identify', formData);
  }

  /** Summarize a medication leaflet / prescription photo in Arabic (vision LLM) */
  async summarizeLeaflet(imageFile) {
    const formData = new FormData();
    formData.append('image', imageFile);
    return this.upload('/leaflet/summarize', formData);
  }

  getScanHistory(page = 1) {
    return this.get(`/scan/history?page=${page}`);
  }

  getScanDetails(scanId) {
    return this.get(`/scan/history/${scanId}`);
  }

  deleteScan(scanId) {
    return this.delete(`/scan/history/${scanId}`);
  }

  // ── Medication Endpoints ──────────────────────────────────────

  getMedications(activeOnly = true) {
    return this.get(`/medications?active_only=${activeOnly}`);
  }

  createMedication(data) {
    return this.post('/medications', data);
  }

  updateMedication(id, data) {
    return this.put(`/medications/${id}`, data);
  }

  deleteMedication(id) {
    return this.delete(`/medications/${id}`);
  }

  // ── Reminder Endpoints ────────────────────────────────────────

  getReminders() {
    return this.get('/reminders');
  }

  createReminder(data) {
    return this.post('/reminders', data);
  }

  updateReminder(id, data) {
    return this.put(`/reminders/${id}`, data);
  }

  deleteReminder(id) {
    return this.delete(`/reminders/${id}`);
  }

  snoozeReminder(id) {
    return this.post(`/reminders/${id}/snooze`, {});
  }

  // ── Adherence Endpoints ───────────────────────────────────────

  logAdherence(data) {
    return this.post('/adherence/log', data);
  }

  getAdherenceStats(period = 'week') {
    return this.get(`/adherence/stats?period=${period}`);
  }

  getAdherenceCalendar(month) {
    return this.get(`/adherence/calendar?month=${month}`);
  }

  getStreak() {
    return this.get('/adherence/streak');
  }
}

/** Custom API Error */
class ApiError extends Error {
  constructor(message, status, data = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

// Singleton
const api = new ApiClient();

export default api;
export { ApiError };
