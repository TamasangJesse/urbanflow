// UrbanFlow — Navbar.jsx
// Shared navbar for all protected pages.
// Shows: logo, nav links (with active state), notification badge, logout.
// Reads unread count from useNotifications hook.

import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuthContext } from '../context/AuthContext';
import { useNotifications } from '../features/notifications/useNotifications';
import Badge from './Badge';
import apiClient from '../lib/apiClient';

export default function Navbar() {
  const { logout } = useAuthContext();
  const location = useLocation();
  const navigate = useNavigate();
  const { unreadCount } = useNotifications();

  async function handleLogout() {
    try {
      await apiClient.post('/auth/logout', {});
    } catch {
      // Even if logout API fails, we clear local state
    } finally {
      logout();
      navigate('/');
    }
  }

  function navLinkClass(path) {
    const isActive = location.pathname === path;
    return `
      flex items-center gap-1.5 px-3 py-1.5 rounded-full
      text-[12px] font-medium transition-colors duration-150
      ${isActive
        ? 'text-[#185FA5] bg-[#E6F1FB]'
        : 'text-[#5F5E5A] hover:text-[#2C2C2A] hover:bg-[#F5F5F3]'
      }
    `;
  }

  return (
    <nav
      className="flex items-center justify-between bg-white border-b border-[#E8E6DF]"
      style={{ height: '56px', paddingLeft: '40px', paddingRight: '40px' }}
    >
      {/* Logo */}
      <Link to="/map" className="flex items-center">
        <span className="text-[17px] font-medium text-[#2C2C2A] select-none">
          Urban
        </span>
        <span className="text-[17px] font-medium text-[#378ADD] select-none">
          Flow
        </span>
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

        <Link to="/notifications" className={navLinkClass('/notifications')}>
          <span className="flex items-center gap-1.5">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/>
              <path d="M13.73 21a2 2 0 01-3.46 0"/>
            </svg>
            Notifications
            <Badge count={unreadCount} />
          </span>
        </Link>

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
