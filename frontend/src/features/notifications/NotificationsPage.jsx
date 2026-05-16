// UrbanFlow — NotificationsPage.jsx
// Layer 1 (UI): Notifications list. No fetch(). No API calls.
// All logic lives in useNotifications.js (Layer 2).

import { useNotifications } from './useNotifications';
import Navbar from '../../components/Navbar';
import Button from '../../components/Button';
import { PageLoader } from '../../components/LoadingSpinner';

function NotificationCard({ notification }) {
  const isRead = notification.is_read;

  const typeStyles = {
    incident:    { bg: '#FCEBEB', color: '#D85A30', icon: '⚠️' },
    congestion:  { bg: '#FAEEDA', color: '#BA7517', icon: '🚦' },
    alert:       { bg: '#E6F1FB', color: '#185FA5', icon: '🔔' },
    system:      { bg: '#F7F6F2', color: '#7A7A72', icon: '💬' },
  };

  const type = (notification.type || 'system').toLowerCase();
  const style = typeStyles[type] || typeStyles.system;

  // Format timestamp
  const timeAgo = (dateStr) => {
    if (!dateStr) return '';
    const diff = Math.floor((Date.now() - new Date(dateStr)) / 1000);
    if (diff < 60)   return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  };

  return (
    <div
      className={`flex items-start gap-4 p-5 rounded-xl border transition-colors ${
        isRead
          ? 'bg-white border-[#E2E1DB]'
          : 'bg-[#F0F6FF] border-[#C5D9F5]'
      }`}
    >
      {/* Icon */}
      <div
        className="w-10 h-10 rounded-full flex items-center justify-center text-lg flex-shrink-0"
        style={{ backgroundColor: style.bg }}
      >
        {style.icon}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p className={`text-[14px] leading-relaxed ${isRead ? 'text-[#3D3D38]' : 'text-[#111210] font-medium'}`}>
            {notification.message || notification.content || 'No message'}
          </p>
          {!isRead && (
            <span className="w-2 h-2 rounded-full bg-[#2563EB] flex-shrink-0 mt-1.5" />
          )}
        </div>
        <div className="flex items-center gap-2 mt-1.5">
          <span
            className="text-[11px] font-medium px-2 py-0.5 rounded-full"
            style={{ backgroundColor: style.bg, color: style.color }}
          >
            {notification.type || 'Notification'}
          </span>
          <span className="text-[11px] text-[#7A7A72]">
            {timeAgo(notification.created_at || notification.timestamp)}
          </span>
        </div>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="w-16 h-16 rounded-full bg-[#F7F6F2] border border-[#E2E1DB] flex items-center justify-center text-3xl mb-4">
        🔔
      </div>
      <h3 className="text-[16px] font-semibold text-[#111210] mb-1">
        You're all caught up
      </h3>
      <p className="text-[13px] text-[#7A7A72] max-w-xs">
        No notifications yet. We'll alert you when incidents are reported near your location.
      </p>
    </div>
  );
}

export default function NotificationsPage() {
  const {
    notifications,
    unreadCount,
    loading,
    error,
    markAllRead,
  } = useNotifications();

  return (
    <div className="min-h-screen flex flex-col bg-[#F7F6F2]">
      <Navbar />

      <main className="flex-1 flex justify-center py-12 px-4">
        <div className="w-full max-w-2xl">

          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1
                className="text-[28px] font-bold text-[#111210] mb-1"
                style={{ fontFamily: 'Georgia, serif', letterSpacing: '-0.5px' }}
              >
                Notifications
              </h1>
              <p className="text-[14px] text-[#7A7A72]">
                {unreadCount > 0
                  ? `You have ${unreadCount} unread notification${unreadCount > 1 ? 's' : ''}`
                  : 'All notifications read'}
              </p>
            </div>

            {unreadCount > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={markAllRead}
                className="!rounded-lg !text-[13px]"
              >
                Mark all as read
              </Button>
            )}
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-center gap-3 px-4 py-3 bg-[#FCEBEB] border border-[#F5C0B8] rounded-xl text-[13px] text-[#A32D2D] mb-6">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              {error}
            </div>
          )}

          {/* Content */}
          {loading ? (
            <PageLoader />
          ) : notifications.length === 0 ? (
            <EmptyState />
          ) : (
            <div className="flex flex-col gap-3">
              {/* Unread section */}
              {notifications.filter((n) => !n.is_read).length > 0 && (
                <>
                  <div className="text-[11px] font-semibold tracking-widest uppercase text-[#7A7A72] px-1 mb-1">
                    Unread
                  </div>
                  {notifications
                    .filter((n) => !n.is_read)
                    .map((n, i) => <NotificationCard key={n.id || i} notification={n} />)
                  }
                  {notifications.filter((n) => n.is_read).length > 0 && (
                    <div className="text-[11px] font-semibold tracking-widest uppercase text-[#7A7A72] px-1 mt-4 mb-1">
                      Earlier
                    </div>
                  )}
                </>
              )}

              {/* Read section */}
              {notifications
                .filter((n) => n.is_read)
                .map((n, i) => <NotificationCard key={n.id || i} notification={n} />)
              }
            </div>
          )}

        </div>
      </main>
    </div>
  );
}