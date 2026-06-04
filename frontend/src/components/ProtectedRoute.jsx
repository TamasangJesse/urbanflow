// UrbanFlow — ProtectedRoute.jsx
// Golden Rule #5: ProtectedRoute wraps every page that needs login.
// Never manually check the token inside a page component.

import { Navigate, useLocation } from 'react-router-dom';
import { useAuthContext } from '../context/AuthContext';

/**
 * Wraps protected routes.
 * If not authenticated → redirects to /login and saves the original URL
 * so the user lands back on the right page after logging in.
 */
export default function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuthContext();
  const location = useLocation();

  if (!isAuthenticated) {
    // Save where they were trying to go
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}
