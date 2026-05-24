// UrbanFlow — useNotifications.js
// Layer 2 (Logic): Real-time notifications via WebSocket.
// Replaces polling entirely — server pushes notifications instantly.
// Falls back to REST fetch on initial load to get existing notifications.
// Fix: reconnect uses ref callback to avoid stale closure issues.

import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuthContext } from '../../context/AuthContext';
import notificationService from './notificationService';

export function useNotifications() {
  const { user, token, isAuthenticated } = useAuthContext();

  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount]     = useState(0);
  const [loading, setLoading]             = useState(false);
  const [error, setError]                 = useState(null);

  const wsRef               = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const isAuthRef           = useRef(isAuthenticated);
  const userIdRef           = useRef(user?.id);
  const tokenRef            = useRef(token);

  // Keep refs in sync with latest values — avoids stale closures in callbacks
  useEffect(() => { isAuthRef.current = isAuthenticated; }, [isAuthenticated]);
  useEffect(() => { userIdRef.current = user?.id;        }, [user?.id]);
  useEffect(() => { tokenRef.current  = token;           }, [token]);

  // ── Fetch existing notifications (REST) ───────────────────────────────────
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

  // ── Open WebSocket ─────────────────────────────────────────────────────────
  const openWebSocket = useCallback(() => {
    const uid = userIdRef.current;
    const tok = tokenRef.current;
    if (!uid || !tok) return;

    // Close existing connection cleanly first
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.close();
      wsRef.current = null;
    }

    const ws = new WebSocket(`wss://urbanflow.duckdns.org/ws/${uid}?token=${tok}`);

    ws.onopen = () => {
      console.log('[WS] Connected');
      setError(null);
    };

    ws.onmessage = (event) => {
      try {
        const notification = JSON.parse(event.data);

        // Real-time incident resolved — remove from map instantly
        if (notification.type === 'incident_resolved') {
           window.dispatchEvent(new CustomEvent('URBANFLOW_INCIDENT_RESOLVED', {
             detail: {
             incident_id:   notification.incident_id,
             incident_type: notification.incident_type,
             address:       notification.address,
             }
            }));

         setNotifications((prev) => [{
           id:         notification.incident_id,
           message:    `Incident resolved: ${notification.address || notification.incident_type || 'An incident near you'}`,
          is_read:    false,
          created_at: new Date().toISOString(),
          type:       'resolved',   
          }, ...prev]);
           setUnreadCount((prev) => prev + 1);


          return;
        }

        // Normal notification — add to bell and update map
        setNotifications((prev) => [notification, ...prev]);
        setUnreadCount((prev) => prev + 1);
        window.dispatchEvent(new CustomEvent('URBANFLOW_NEW_INCIDENT'));
      } catch {}
    };

    ws.onerror = () => {
      setError('Notification connection lost. Reconnecting…');
    };

    ws.onclose = () => {
      console.log('[WS] Closed — will reconnect in 5s if still authenticated');
      if (isAuthRef.current && userIdRef.current && tokenRef.current) {
        reconnectTimeoutRef.current = setTimeout(openWebSocket, 5000);
      }
    };

    wsRef.current = ws;
  }, []);

  // ── Start on login, clean up on logout ────────────────────────────────────
  useEffect(() => {
    if (!isAuthenticated || !user?.id || !token) return;

    setLoading(true);
    fetchNotifications().finally(() => setLoading(false));
    openWebSocket();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [isAuthenticated, user?.id, token]);

  // ── Mark all read ──────────────────────────────────────────────────────────
  async function markAllRead() {
    if (!user?.id) return;
    try {
      await notificationService.markAllRead(user.id);
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