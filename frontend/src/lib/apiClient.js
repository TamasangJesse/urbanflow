// UrbanFlow — apiClient.js
// Golden Rule #2: JWT is attached in ONE place only — here.
// Golden Rule: No service file ever calls fetch() directly — they always call apiClient.

import { API_BASE_URL } from './constants';

/**
 * Core request function.
 * Automatically reads JWT from localStorage and attaches it as Authorization header.
 * @param {string} endpoint - e.g. '/auth/login'
 * @param {object} options  - fetch options: method, body, etc.
 */
async function request(endpoint, options = {}) {
  const token = localStorage.getItem('urbanflow_token');

  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const config = {
    ...options,
    headers,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

  // For 204 No Content responses
  if (response.status === 204) {
    return null;
  }

  const data = await response.json();

  if (!response.ok) {
    // Throw an error object containing the server message when available
    const error = new Error(data?.detail || data?.message || 'An error occurred');
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

const apiClient = {
  get: (endpoint, options = {}) =>
    request(endpoint, { ...options, method: 'GET' }),

  post: (endpoint, body, options = {}) =>
    request(endpoint, { ...options, method: 'POST', body: JSON.stringify(body) }),

  put: (endpoint, body, options = {}) =>
    request(endpoint, { ...options, method: 'PUT', body: JSON.stringify(body) }),

  delete: (endpoint, options = {}) =>
    request(endpoint, { ...options, method: 'DELETE' }),
};

export default apiClient;
