// UrbanFlow — useAuth.js
// Layer 2 (Logic): State, side effects, form handling for auth.
// No JSX. Calls authService only. Never calls fetch() directly.

import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthContext } from '../../context/AuthContext';
import authService from './authService';

export function useAuth() {
  const { login: contextLogin } = useAuthContext();
  const navigate  = useNavigate();
  const location  = useLocation();

  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  const from = location.state?.from?.pathname || '/map';

  async function login(credentials) {
    setLoading(true);
    setError(null);
    try {
      const data = await authService.login(credentials);

      // Backend returns: { access_token, token_type, user_id }
      const token = data.access_token;
      const user  = {
        id:        data.user_id,
        email:     credentials.email,
        full_name: data.full_name || credentials.email,
      };

      contextLogin(user, token);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.message || 'Invalid email or password');
    } finally {
      setLoading(false);
    }
  }

  async function register(data) {
    setLoading(true);
    setError(null);
    try {
      const response = await authService.register(data);

      // Backend returns: { access_token, token_type, user_id }
      const token = response.access_token;
      const user  = {
        id:        response.user_id,
        email:     data.email,
        full_name: data.full_name,
      };

      contextLogin(user, token);
      navigate('/map', { replace: true });
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return { login, register, loading, error };
}