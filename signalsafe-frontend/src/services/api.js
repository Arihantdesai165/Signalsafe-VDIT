/**
 * SignalSafe Campus – Centralized API Service
 * Handles authenticated requests, error handling, session propagation, and endpoint calls.
 */

const rawBase = (import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || '').trim();
const API_BASE_URL = rawBase
  ? (rawBase.endsWith('/api') ? rawBase : `${rawBase.replace(/\/+$/, '')}/api`)
  : '/api';

class ApiService {
  /**
   * Validates uploaded image files for allowed MIME type and max size
   */
  validateImageFile(file) {
    if (!file) throw new Error('No image file selected.');
    const validMimes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!validMimes.includes((file.type || '').toLowerCase())) {
      throw new Error('Invalid file format. Please upload a valid PNG, JPG, or JPEG image.');
    }
    const maxBytes = 15 * 1024 * 1024; // 15MB limit
    if (file.size > maxBytes) {
      throw new Error('File size exceeds 15MB limit. Please choose a smaller image.');
    }
  }

  /**
   * Helper to execute fetch requests with automatic auth headers & error handling
   */
  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    const token = localStorage.getItem('signalsafe_session_token');

    const headers = new Headers(options.headers || {});

    // Attach Bearer token if present
    if (token && !headers.has('Authorization')) {
      headers.set('Authorization', `Bearer ${token}`);
    }

    // Set JSON Content-Type only if body is not FormData
    if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }

    const config = {
      ...options,
      headers,
      credentials: 'include', // Support HTTP-only cookies
    };

    let response;
    try {
      response = await fetch(url, config);
    } catch (networkError) {
      console.error(`Network error requesting ${url}:`, networkError);
      throw new Error('Unable to connect to the SignalSafe security server. Please verify your connection.');
    }

    // Handle 401 Unauthorized (Expired or Invalid Session)
    if (response.status === 401 && !url.includes('/auth/login')) {
      localStorage.removeItem('signalsafe_session_token');
      localStorage.removeItem('signalsafe_user');
      window.dispatchEvent(new CustomEvent('signalsafe:session-expired'));
      throw new Error('Your session has expired. Please sign in again.');
    }

    // Attempt to parse JSON response
    let data;
    try {
      data = await response.json();
    } catch {
      data = null;
    }

    if (!response.ok) {
      const errorDetail = (data && (data.detail || data.message || data.error)) || `Server returned status ${response.status}`;
      const error = new Error(errorDetail);
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  }

  // -------------------------------------------------------------
  // Authentication & Session Endpoints
  // -------------------------------------------------------------
  async login(email, password) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email: email.trim(), password }),
    });
  }

  async verifyDailyOtp(email, otp) {
    return this.request('/auth/verify-daily-otp', {
      method: 'POST',
      body: JSON.stringify({ email: email.trim(), otp: otp.trim() }),
    });
  }

  async resendDailyOtp(email, password = null) {
    return this.request('/auth/resend-daily-otp', {
      method: 'POST',
      body: JSON.stringify({ email: email.trim(), password }),
    });
  }

  async getMe() {
    return this.request('/auth/me', {
      method: 'GET',
    });
  }

  async logout() {
    try {
      return await this.request('/auth/logout', { method: 'POST' });
    } finally {
      localStorage.removeItem('signalsafe_session_token');
      localStorage.removeItem('signalsafe_user');
    }
  }

  // -------------------------------------------------------------
  // Security Feature Engines
  // -------------------------------------------------------------

  /**
   * QR Code Scam Detector
   * Uploads an image file to analyze UPI payment destination
   */
  async analyzeQrCode(file) {
    this.validateImageFile(file);
    const formData = new FormData();
    formData.append('file', file);

    return this.request('/qrcode/analyze', {
      method: 'POST',
      body: formData,
    });
  }

  /**
   * Fraudulent Website Detection
   * Analyzes URLs through phishing models and heuristic algorithms
   */
  async analyzeWebsiteUrl(url) {
    return this.request('/url/phishing/analyze', {
      method: 'POST',
      body: JSON.stringify({ url: url.trim() }),
    });
  }

  /**
   * Malicious Link Checker
   * Validates suspicious link structures, IP hosts, and domain reputation
   */
  async analyzeMaliciousLink(url) {
    return this.request('/url/analyze', {
      method: 'POST',
      body: JSON.stringify({ url: url.trim() }),
    });
  }

  /**
   * Report an Incident / Scam URL
   * Records reported fraudulent URLs and increments persistent report counts
   */
  async reportScamUrl(url) {
    return this.request('/url/report', {
      method: 'POST',
      body: JSON.stringify({ url: url.trim() }),
    });
  }

  /**
   * Screenshot Scam Detector
   * Preserved operational UPI receipt / payment screenshot analyzer
   */
  async analyzeScreenshot(file) {
    this.validateImageFile(file);
    const formData = new FormData();
    formData.append('file', file);

    return this.request('/screenshot/analyze', {
      method: 'POST',
      body: formData,
    });
  }

  /**
   * Health Check
   */
  async checkHealth() {
    return this.request('/health', { method: 'GET' });
  }

  // -------------------------------------------------------------
  // CyberAdmin Incident Management Endpoints
  // -------------------------------------------------------------

  /**
   * Retrieves summary statistics for CyberAdmin dashboard
   */
  async getIncidentStats() {
    return this.request('/incidents/stats', { method: 'GET' });
  }

  /**
   * Lists campus incidents with filtering and pagination
   */
  async listIncidents(params = {}) {
    const query = new URLSearchParams();
    if (params.search) query.set('search', params.search);
    if (params.status && params.status !== 'ALL') query.set('status', params.status);
    if (params.category && params.category !== 'ALL') query.set('category', params.category);
    if (params.page) query.set('page', params.page);
    if (params.pageSize) query.set('page_size', params.pageSize);

    const queryString = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/incidents${queryString}`, { method: 'GET' });
  }

  /**
   * Retrieves a single incident report by ID
   */
  async getIncident(incidentId) {
    return this.request(`/incidents/${encodeURIComponent(incidentId)}`, { method: 'GET' });
  }

  /**
   * Submits a new security incident report
   */
  async createIncident(incidentData) {
    return this.request('/incidents', {
      method: 'POST',
      body: JSON.stringify(incidentData),
    });
  }

  /**
   * Updates an incident status (CyberAdmin exclusive)
   */
  async updateIncidentStatus(incidentId, status, note = null) {
    return this.request(`/incidents/${encodeURIComponent(incidentId)}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status, note }),
    });
  }

  /**
   * Adds an investigation note to an incident (CyberAdmin exclusive)
   */
  async addIncidentNote(incidentId, note) {
    return this.request(`/incidents/${encodeURIComponent(incidentId)}/notes`, {
      method: 'POST',
      body: JSON.stringify({ note }),
    });
  }

  // -------------------------------------------------------------
  // CyberAdmin Screenshot Reference Dataset Management
  // -------------------------------------------------------------

  /**
   * Fetches metadata for the currently active screenshot reference dataset
   */
  async getActiveScreenshotDataset() {
    return this.request('/cyberadmin/screenshot-datasets/active', { method: 'GET' });
  }

  /**
   * Pre-validates a candidate dataset CSV before activation
   */
  async validateScreenshotDataset(file) {
    if (!file) throw new Error('No dataset CSV file selected.');
    const formData = new FormData();
    formData.append('file', file);
    return this.request('/cyberadmin/screenshot-datasets/validate', {
      method: 'POST',
      body: formData,
    });
  }

  /**
   * Uploads, validates, and atomically activates a new reference dataset
   */
  async activateScreenshotDataset(file, datasetName = '') {
    if (!file) throw new Error('No dataset CSV file selected.');
    const formData = new FormData();
    formData.append('file', file);
    if (datasetName) {
      formData.append('dataset_name', datasetName);
    }
    return this.request('/cyberadmin/screenshot-datasets/activate', {
      method: 'POST',
      body: formData,
    });
  }

  /**
   * Retrieves dataset version history for CyberAdmin audit review
   */
  async getScreenshotDatasetHistory() {
    return this.request('/cyberadmin/screenshot-datasets/history', { method: 'GET' });
  }

  /**
   * Deactivates the currently active dataset
   */
  async deactivateScreenshotDataset() {
    return this.request('/cyberadmin/screenshot-datasets/deactivate', { method: 'POST' });
  }

  // -------------------------------------------------------------
  // CyberAdmin Official College Payment QR Registry
  // -------------------------------------------------------------

  /**
   * Retrieves live database counts and statistics for the College QR Registry
   */
  async getCollegeQrStats() {
    return this.request('/cyberadmin/college-qr/stats', { method: 'GET' });
  }

  /**
   * Lists registered college payment QRs with search, filter, and pagination
   */
  async listCollegeQrs(params = {}) {
    const query = new URLSearchParams();
    if (params.search) query.set('search', params.search);
    if (params.payment_purpose && params.payment_purpose !== 'ALL') query.set('payment_purpose', params.payment_purpose);
    if (params.department && params.department !== 'ALL') query.set('department', params.department);
    if (params.approval_status && params.approval_status !== 'ALL') query.set('approval_status', params.approval_status);
    if (params.is_active !== undefined && params.is_active !== null && params.is_active !== '') {
      query.set('is_active', params.is_active);
    }
    if (params.page) query.set('page', params.page);
    if (params.page_size) query.set('page_size', params.page_size);

    const queryString = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/cyberadmin/college-qr${queryString}`, { method: 'GET' });
  }

  /**
   * Decodes a candidate QR image on the backend without saving
   */
  async previewCollegeQrDecode(file) {
    if (!file) throw new Error('No QR code image selected.');
    const formData = new FormData();
    formData.append('file', file);
    return this.request('/cyberadmin/college-qr/decode-preview', {
      method: 'POST',
      body: formData,
    });
  }

  /**
   * Registers a single official college payment QR
   */
  async createCollegeQr(data) {
    const formData = new FormData();
    formData.append('file', data.file);
    formData.append('display_name', data.display_name);
    formData.append('payment_purpose', data.payment_purpose);
    formData.append('official_recipient_name', data.official_recipient_name);
    formData.append('expected_upi_id', data.expected_upi_id);
    if (data.department) formData.append('department', data.department);
    if (data.expected_amount) formData.append('expected_amount', data.expected_amount);
    if (data.description) formData.append('description', data.description);
    if (data.auto_approve) formData.append('auto_approve', 'true');

    return this.request('/cyberadmin/college-qr', {
      method: 'POST',
      body: formData,
    });
  }

  /**
   * Bulk uploads multiple college payment QR images
   */
  async bulkUploadCollegeQrs(files, defaultPurpose = 'Tuition Fees', defaultDepartment = 'Finance & Accounts Office', autoApprove = false) {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    formData.append('default_purpose', defaultPurpose);
    if (defaultDepartment) formData.append('default_department', defaultDepartment);
    if (autoApprove) formData.append('auto_approve', 'true');

    return this.request('/cyberadmin/college-qr/bulk', {
      method: 'POST',
      body: formData,
    });
  }

  /**
   * Retrieves single QR record details
   */
  async getCollegeQr(recordId) {
    return this.request(`/cyberadmin/college-qr/${encodeURIComponent(recordId)}`, { method: 'GET' });
  }

  /**
   * Returns authenticated URL for the stored QR image
   */
  getCollegeQrImageUrl(recordId) {
    return `${API_BASE_URL}/cyberadmin/college-qr/${encodeURIComponent(recordId)}/image`;
  }

  /**
   * Updates metadata for an existing QR record
   */
  async updateCollegeQr(recordId, updateData) {
    return this.request(`/cyberadmin/college-qr/${encodeURIComponent(recordId)}`, {
      method: 'PATCH',
      body: JSON.stringify(updateData),
    });
  }

  /**
   * Replaces the QR image file and re-decodes the payload
   */
  async replaceCollegeQrImage(recordId, file) {
    const formData = new FormData();
    formData.append('file', file);
    return this.request(`/cyberadmin/college-qr/${encodeURIComponent(recordId)}/replace-image`, {
      method: 'POST',
      body: formData,
    });
  }

  /**
   * Approves and activates a QR record
   */
  async approveCollegeQr(recordId) {
    return this.request(`/cyberadmin/college-qr/${encodeURIComponent(recordId)}/approve`, { method: 'POST' });
  }

  /**
   * Deactivates an active QR record
   */
  async deactivateCollegeQr(recordId) {
    return this.request(`/cyberadmin/college-qr/${encodeURIComponent(recordId)}/deactivate`, { method: 'POST' });
  }

  /**
   * Archives a QR record
   */
  async archiveCollegeQr(recordId) {
    return this.request(`/cyberadmin/college-qr/${encodeURIComponent(recordId)}/archive`, { method: 'POST' });
  }
}

export const api = new ApiService();
export default api;
