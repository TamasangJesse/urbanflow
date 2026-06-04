// UrbanFlow — notificationService.js
// Layer 3 (Data): Notification API calls only. No useState. Returns raw data.

import apiClient from '../../lib/apiClient';

const notificationService = {
  /**
   * GET /notifications/{user_id}
   * Returns the list of notifications for the user.
   */
  getNotifications: (userId) => apiClient.get(`/notifications/${userId}`),

  /**
   * PUT /notifications/{user_id}/read
   * Marks all notifications as read.
   */
  markAllRead: (userId) => apiClient.put(`/notifications/${userId}/read`, {}),
};

export default notificationService;
