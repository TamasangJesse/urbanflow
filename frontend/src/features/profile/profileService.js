// UrbanFlow — profileService.js
// Layer 3 (Data): User profile API calls. No useState. Returns raw data.

import apiClient from '../../lib/apiClient';

const profileService = {
  /** GET /users/{id} */
  getUser: (userId) => apiClient.get(`/users/${userId}`),

  /** PUT /users/{id} — update profile info or password */
  updateUser: (userId, data) => apiClient.put(`/users/${userId}`, data),

  /** DELETE /users/{id} — permanently delete account */
  deleteUser: (userId) => apiClient.delete(`/users/${userId}`),

  /** GET /users/{id}/routes — get saved routes */
  getSavedRoutes: (userId) => apiClient.get(`/users/${userId}/routes`),
};

export default profileService;
