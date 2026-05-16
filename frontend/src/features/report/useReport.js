// UrbanFlow — useReport.js
// Layer 2 (Logic): Form state, GPS auto-detect, submit and reset for incident report.
// No JSX. Calls reportService only.

import { useState, useEffect } from 'react';
import { useAuthContext } from '../../context/AuthContext';
import reportService from './reportService';

const INITIAL_FORM = {
  type: '',
  description: '',
  severity: '',
  latitude: null,
  longitude: null,
  address: '',
};

export function useReport() {
  const { user } = useAuthContext();
  const [form, setForm] = useState(INITIAL_FORM);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  // Auto-detect GPS location on mount
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setForm((prev) => ({
            ...prev,
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
          }));
        },
        () => {
          // GPS denied — user can still click the map to pick a location
        }
      );
    }
  }, []);

  function setField(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function setLocation({ lat, lng, address }) {
    setForm((prev) => ({ ...prev, latitude: lat, longitude: lng, address }));
  }

  async function submitReport() {
    setLoading(true);
    setError(null);
    setSuccess(false);
    try {
      await reportService.submitIncident({
        type: form.type,
        description: form.description,
        latitude: form.latitude,
        longitude: form.longitude,
        severity: form.severity,
        reported_by: user?.id,
      });
      setSuccess(true);
      setForm(INITIAL_FORM);
    } catch (err) {
      setError(err.message || 'Failed to submit report. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return {
    form,
    setField,
    setLocation,
    submitReport,
    loading,
    success,
    error,
  };
}
