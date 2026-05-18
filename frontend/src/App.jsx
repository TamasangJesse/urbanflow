// UrbanFlow — App.jsx
// Defines all routes. Protected routes are wrapped in ProtectedRoute.
// Public routes redirect to /map if already logged in.

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuthContext } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

// Pages — lazy-imported for better performance
import { lazy, Suspense } from 'react';
import { PageLoader } from './components/LoadingSpinner';

const LandingPage        = lazy(() => import('./features/auth/LandingPage'));
const LoginPage          = lazy(() => import('./features/auth/LoginPage'));
const RegisterPage       = lazy(() => import('./features/auth/RegisterPage'));
const MapPage            = lazy(() => import('./features/map/MapPage'));
const ReportPage         = lazy(() => import('./features/report/ReportPage'));
const NotificationsPage  = lazy(() => import('./features/notifications/NotificationsPage'));
const ProfilePage        = lazy(() => import('./features/profile/ProfilePage'));
import { ChatPanelProvider } from './context/ChatPanelContext'; 

/**
 * PublicOnlyRoute — redirects to /map if already logged in.
 * Used for /, /login, /register.
 */
function PublicOnlyRoute({ children }) {
  const { isAuthenticated } = useAuthContext();
  return isAuthenticated ? <Navigate to="/map" replace /> : children;
}

function AppRoutes() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* Public routes */}
        <Route
          path="/"
          element={<PublicOnlyRoute><LandingPage /></PublicOnlyRoute>}
        />
        <Route
          path="/login"
          element={<PublicOnlyRoute><LoginPage /></PublicOnlyRoute>}
        />
        <Route
          path="/register"
          element={<PublicOnlyRoute><RegisterPage /></PublicOnlyRoute>}
        />

        {/* Protected routes — Golden Rule #5 */}
        <Route
          path="/map"
          element={<ProtectedRoute><MapPage /></ProtectedRoute>}
        />
        <Route
          path="/report"
          element={<ProtectedRoute><ReportPage /></ProtectedRoute>}
        />
        <Route
          path="/notifications"
          element={<ProtectedRoute><NotificationsPage /></ProtectedRoute>}
        />
        <Route
          path="/profile"
          element={<ProtectedRoute><ProfilePage /></ProtectedRoute>}
        />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ChatPanelProvider>
          <AppRoutes />
        </ChatPanelProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
