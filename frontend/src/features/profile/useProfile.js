// UrbanFlow — useProfile.js
// Layer 2 (Logic): User data, saved routes, update, delete. No JSX.

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthContext } from '../../context/AuthContext';
import profileService from './profileService';

export function useProfile() {
  const { user, logout } = useAuthContext();
  const navigate = useNavigate();

  const [profile, setProfile] = useState(null);
  const [savedRoutes, setSavedRoutes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  useEffect(() => {
    if (!user?.id) return;
    setLoading(true);
    Promise.all([
      profileService.getUser(user.id),
      profileService.getSavedRoutes(user.id),
    ])
      .then(([userData, routesData]) => {
        setProfile(userData);
        setSavedRoutes(Array.isArray(routesData) ? routesData : (routesData?.routes || []));
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [user?.id]);

  async function updateProfile(data) {
    setSaving(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const updated = await profileService.updateUser(user.id, data);
      setProfile(updated);
      setSuccessMessage('Changes saved successfully.');
    } catch (err) {
      setError(err.message || 'Failed to save changes.');
    } finally {
      setSaving(false);
    }
  }

  async function deleteUser() {
    try {
      await profileService.deleteUser(user.id);
      logout();
      navigate('/', { replace: true });
    } catch (err) {
      setError(err.message || 'Failed to delete account.');
    }
  }

  async function deleteRoute(routeId) {
    // Optimistic UI update — remove immediately, then sync with backend
    setSavedRoutes((prev) => prev.filter((r) => r.id !== routeId));
    try {
      await profileService.updateUser(user.id, { delete_route_id: routeId });
    } catch (err) {
      setError(err.message);
      // Re-fetch to restore correct state if delete failed
      const routesData = await profileService.getSavedRoutes(user.id);
      setSavedRoutes(Array.isArray(routesData) ? routesData : (routesData?.routes || []));
    }
  }

  return {
    profile,
    savedRoutes,
    loading,
    saving,
    error,
    successMessage,
    updateProfile,
    deleteUser,
    deleteRoute,
  };
}
