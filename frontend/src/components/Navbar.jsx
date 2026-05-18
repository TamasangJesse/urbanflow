// UrbanFlow — Navbar.jsx
// Shared navbar for all protected pages.
// Features: YouTube-style notification dropdown, active link highlighting, logout.

import { useState, useRef, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuthContext } from '../context/AuthContext';
import { useNotifications } from '../features/notifications/useNotifications';
import apiClient from '../lib/apiClient';
import { useChatPanel } from '../context/ChatPanelContext';

// ─── Notification Dropdown ────────────────────────────────────────────────────

function NotificationDropdown({ notifications, unreadCount, onMarkAllRead, onClose }) {
  const timeAgo = (dateStr) => {
    if (!dateStr) return '';
    const diff = Math.floor((Date.now() - new Date(dateStr)) / 1000);
    if (diff < 60)    return 'Just now';
    if (diff < 3600)  return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  };

  const typeIcon = {
    incident:   '⚠️',
    congestion: '🚦',
    alert:      '🔔',
    system:     '💬',
  };

  return (
    <div
      className="absolute right-0 top-full mt-2 bg-white border border-[#E2E1DB] rounded-2xl overflow-hidden z-50"
      style={{ width: '380px', boxShadow: '0 8px 30px rgba(17,18,16,0.12)' }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-[#E2E1DB]">
        <div>
          <span className="text-[15px] font-semibold text-[#111210]">Notifications</span>
          {unreadCount > 0 && (
            <span className="ml-2 text-[11px] font-medium px-2 py-0.5 bg-[#E6F1FB] text-[#185FA5] rounded-full">
              {unreadCount} new
            </span>
          )}
        </div>
        {unreadCount > 0 && (
          <button
            onClick={onMarkAllRead}
            className="text-[12px] text-[#2563EB] hover:underline font-medium"
          >
            Mark all as read
          </button>
        )}
      </div>

      {/* List */}
      <div className="overflow-y-auto" style={{ maxHeight: '400px' }}>
        {notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 text-center px-5">
            <div className="text-3xl mb-3">🔔</div>
            <p className="text-[13px] font-medium text-[#111210]">You're all caught up!</p>
            <p className="text-[12px] text-[#7A7A72] mt-1">No notifications yet.</p>
          </div>
        ) : (
          notifications.map((n, i) => {
            const type = (n.type || 'system').toLowerCase();
            const icon = typeIcon[type] || typeIcon.system;
            const isRead = n.is_read;
            return (
              <div
                key={n.id || i}
                className={`flex items-start gap-3 px-5 py-4 border-b border-[#F5F5F3] last:border-b-0 transition-colors hover:bg-[#F7F6F2] ${!isRead ? 'bg-[#F0F6FF]' : 'bg-white'}`}
              >
                <div className="w-9 h-9 rounded-full bg-[#F7F6F2] flex items-center justify-center text-lg flex-shrink-0">
                  {icon}
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-[13px] leading-relaxed ${!isRead ? 'font-medium text-[#111210]' : 'text-[#3D3D38]'}`}>
                    {n.message || n.content || 'Notification'}
                  </p>
                  <p className="text-[11px] text-[#7A7A72] mt-1">
                    {timeAgo(n.created_at || n.timestamp)}
                  </p>
                </div>
                {!isRead && (
                  <div className="w-2 h-2 rounded-full bg-[#2563EB] flex-shrink-0 mt-1.5" />
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

// ─── Main Navbar ──────────────────────────────────────────────────────────────

export default function Navbar() {
  const { logout } = useAuthContext();
  const location   = useLocation();
  const navigate   = useNavigate();
  const { notifications, unreadCount, markAllRead } = useNotifications();
  const { toggle } = useChatPanel();
  const [showNotifications, setShowNotifications] = useState(false);
  const notifRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(e) {
      if (notifRef.current && !notifRef.current.contains(e.target)) {
        setShowNotifications(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  async function handleLogout() {
    try { await apiClient.post('/auth/logout', {}); } catch {}
    finally { logout(); navigate('/'); }
  }

  function navLinkClass(path) {
    const isActive = location.pathname === path;
    return `flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[12px] font-medium transition-colors duration-150 ${
      isActive
        ? 'text-[#185FA5] bg-[#E6F1FB]'
        : 'text-[#5F5E5A] hover:text-[#2C2C2A] hover:bg-[#F5F5F3]'
    }`;
  }

  return (
    <nav
      className="flex items-center justify-between bg-white border-b border-[#E8E6DF] relative z-40"
      style={{ height: '56px', paddingLeft: '40px', paddingRight: '40px' }}
    >
      {/* Logo */}
      <Link to="/map" className="flex items-center select-none">
        <span className="text-[17px] font-medium text-[#2C2C2A]">Urban</span>
        <span className="text-[17px] font-medium text-[#378ADD]">Flow</span>
      </Link>

      {/* Nav links */}
      <div className="flex items-center gap-1">
        <Link to="/map" className={navLinkClass('/map')}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/>
          </svg>
          Map
        </Link>

        <Link to="/report" className={navLinkClass('/report')}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          Report incident
        </Link>

        {/* Notification bell — YouTube style */}
        <div className="relative" ref={notifRef}>
          <button
            onClick={() => setShowNotifications((prev) => !prev)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[12px] font-medium transition-colors duration-150 ${
              showNotifications
                ? 'text-[#185FA5] bg-[#E6F1FB]'
                : 'text-[#5F5E5A] hover:text-[#2C2C2A] hover:bg-[#F5F5F3]'
            }`}
          >
            <div className="relative">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                <path d="M13.73 21a2 2 0 01-3.46 0"/>
              </svg>
              {unreadCount > 0 && (
                <span className="absolute -top-1.5 -right-1.5 w-4 h-4 bg-[#D85A30] text-white text-[9px] font-bold rounded-full flex items-center justify-center leading-none">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </div>
            Notifications
          </button>

          {/* Dropdown */}
          {showNotifications && (
            <NotificationDropdown
              notifications={notifications}
              unreadCount={unreadCount}
              onMarkAllRead={() => { markAllRead(); }}
              onClose={() => setShowNotifications(false)}
            />
          )}
        </div>


        {/* AI Chat button */}
  <button
  onClick={toggle}
  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[12px] font-medium text-[#5F5E5A] hover:text-[#2C2C2A] hover:bg-[#F5F5F3] transition-colors duration-150"
>
  <svg width="14" height="14" viewBox="0 0 28 28" fill="none">
    <path d="M14 1C14 1 15.8 9.2 21 14C15.8 18.8 14 27 14 27C14 27 12.2 18.8 7 14C12.2 9.2 14 1 14 1Z" fill="url(#nav_grad)"/>
    <defs>
      <linearGradient id="nav_grad" x1="7" y1="1" x2="21" y2="27" gradientUnits="userSpaceOnUse">
        <stop stopColor="#4285F4"/>
        <stop offset="0.5" stopColor="#9B72CB"/>
        <stop offset="1" stopColor="#D96570"/>
      </linearGradient>
    </defs>
  </svg>
  Ask AI
</button>

        <Link to="/profile" className={navLinkClass('/profile')}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
          </svg>
          Profile
        </Link>

        <button
          onClick={handleLogout}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[12px] font-medium text-[#D85A30] hover:bg-[#FCEBEB] transition-colors duration-150"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/>
            <polyline points="16 17 21 12 16 7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
          Log out
        </button>
      </div>
    </nav>
  );
}