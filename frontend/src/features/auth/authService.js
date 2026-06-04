// UrbanFlow — authService.js
// Layer 3 (Data): All auth API calls. No useState. Returns raw API data.
// Never called from a .jsx file directly — only from useAuth.js.

import apiClient from '../../lib/apiClient';

const authService = {
  /**
   * POST /auth/login
   * @param {{ email: string, password: string }} credentials
   * @returns {{ user: object, token: string }}
   */
  login: (credentials) => apiClient.post('/auth/login', credentials),

  /**
   * POST /auth/register
   * @param {{ full_name: string, email: string, password: string }} data
   * @returns {{ user: object, token: string }}
   */
  register: (data) => apiClient.post('/auth/register', data),

  /**
   * POST /auth/logout
   */
  logout: () => apiClient.post('/auth/logout', {}),
};

export default authService;
