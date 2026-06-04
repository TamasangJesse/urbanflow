// UrbanFlow — AuthContext.jsx
// Golden Rule #3: Global state is for auth only.
// Stores: user object + JWT token. Nothing else lives here.

import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);   // { id, full_name, email }
  const [token, setToken] = useState(null);

  // Rehydrate from localStorage on first load (page refresh)
  useEffect(() => {
    const storedToken = localStorage.getItem('urbanflow_token');
    const storedUser = localStorage.getItem('urbanflow_user');
    if (storedToken && storedUser) {
      setToken(storedToken);
      try {
        setUser(JSON.parse(storedUser));
      } catch {
        // Corrupted data — clear it
        localStorage.removeItem('urbanflow_token');
        localStorage.removeItem('urbanflow_user');
      }
    }
  }, []);

  /**
   * Called after a successful login or register API response.
   * @param {object} userData - { id, full_name, email }
   * @param {string} jwtToken - the JWT string
   */
  function login(userData, jwtToken) {
    setUser(userData);
    setToken(jwtToken);
    localStorage.setItem('urbanflow_token', jwtToken);
    localStorage.setItem('urbanflow_user', JSON.stringify(userData));
  }

  /**
   * Clears auth state and localStorage.
   * The actual POST /auth/logout API call is made by useAuth before calling this.
   */
  function logout() {
    setUser(null);
    setToken(null);
    localStorage.removeItem('urbanflow_token');
    localStorage.removeItem('urbanflow_user');
  }

  const isAuthenticated = token !== null;

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated }}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook to consume AuthContext.
 * Usage: const { user, token, login, logout, isAuthenticated } = useAuthContext();
 */
export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext must be used inside <AuthProvider>');
  }
  return context;
}
