// UrbanFlow — useNotifications.js
// Layer 2 (Logic): Manages notifications array, unread count, and 30s polling.
// Also used by Navbar to show the unread badge count.
// No JSX. Calls notificationService only.

import { useState, useEffect, useCallback } from 'react';
import { useAuthContext } from '../../context/AuthContext';
import notificationService from './notificationService';
import { NOTIFICATION_POLL_INTERVAL } from '../../lib/constants';

export function useNotifications() {
  const { user, isAuthenticated } = useAuthContext();

  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchNotifications = useCallback(async () => {
    if (!user?.id) return;
    try {
      const data = await notificationService.getNotifications(user.id);
      const list = Array.isArray(data) ? data : (data?.notifications || []);
      setNotifications(list);
      setUnreadCount(list.filter((n) => !n.is_read).length);
    } catch (err) {
      setError(err.message);
    }
  }, [user?.id]);

  // Initial fetch + polling interval
  useEffect(() => {
    if (!isAuthenticated || !user?.id) return;

    setLoading(true);
    fetchNotifications().finally(() => setLoading(false));

    const interval = setInterval(fetchNotifications, NOTIFICATION_POLL_INTERVAL);

    return () => clearInterval(interval); // Cleanup — Golden Rule #10
  }, [isAuthenticated, user?.id, fetchNotifications]);

  async function markAllRead() {
    if (!user?.id) return;
    try {
      await notificationService.markAllRead(user.id);
      // Optimistic update
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      setError(err.message);
    }
  }

  return {
    notifications,
    unreadCount,
    loading,
    error,
    markAllRead,
    refetch: fetchNotifications,
  };
}
