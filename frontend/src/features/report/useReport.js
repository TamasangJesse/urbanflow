// UrbanFlow — useReport.js
// Layer 2 (Logic): Form state, GPS, submit, and user's past incidents.

import { useState, useEffect } from 'react';
import { useAuthContext } from '../../context/AuthContext';
import reportService from './reportService';

const INITIAL_FORM = {
  type: '', description: '', severity: '',
  latitude: null, longitude: null, address: '',
};

export function useReport() {
  const { user } = useAuthContext();
  console.log("Full user object:", user);
  const [form, setForm]               = useState(INITIAL_FORM);
  const [loading, setLoading]         = useState(false);
  const [success, setSuccess]         = useState(false);
  const [error, setError]             = useState(null);
  const [myIncidents, setMyIncidents] = useState([]);
  const [loadingIncidents, setLoadingIncidents] = useState(false);

  // Auto-detect GPS
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setForm((prev) => ({
          ...prev,
          latitude:  pos.coords.latitude,
          longitude: pos.coords.longitude,
        })),
        () => {}
      );
    }
  }, []);

  // ── Shared helper: fetch and normalise the user's incidents list ──────────
  async function refreshMyIncidents() {
    try {
      const res = await reportService.getUserIncidents(user.id);
      const responseData = res?.data || res;
      console.log("Extracted payload inside hook:", responseData);

      if (responseData && Array.isArray(responseData.incidents)) {
        setMyIncidents(responseData.incidents);
      } else if (Array.isArray(responseData)) {
        setMyIncidents(responseData);
      } else {
        setMyIncidents([]);
      }
    } catch (err) {
      console.error("Fetch block caught error:", err);
    }
  }

  // Load user's past incidents on mount
  useEffect(() => {
    if (!user?.id) return;
    setLoadingIncidents(true);
    refreshMyIncidents()
      .finally(() => setLoadingIncidents(false));
  }, [user?.id]);

  function setField(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function setLocation({ lat, lng, address }) {
    setForm((prev) => ({ ...prev, latitude: lat, longitude: lng, address: address || '' }));
  }

  async function submitReport() {
    // Validate before submitting
  if (!form.type) {
    setError('Please select an incident type.');
    return;
  }
  if (!form.severity) {
    setError('Please select a severity level.');
    return;
  }
  if (!form.latitude || !form.longitude) {
    setError('Please enter your location.');
    return;
  }



    setLoading(true);
    setError(null);
    setSuccess(false);
    try {
      await reportService.submitIncident({
        type:        form.type,
        description: form.description,
        latitude:    form.latitude,
        longitude:   form.longitude,
        severity:    form.severity,
        reported_by: user?.id,
      });
      setSuccess(true);
      setForm(INITIAL_FORM);
      await refreshMyIncidents(); // Clean, single-line reuse
    } catch (err) {
      setError(err.message || 'Failed to submit report. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  // ── Resolve an incident and drop it from the local list ───────────────────
  async function resolveIncident(id) {
    try {
      await reportService.resolveIncident(id);
      await refreshMyIncidents(); // Automatically updates the list so it disappears
    } catch (err) {
      console.error('Failed to resolve incident:', err);
    }
  }

  return {
    form, setField, setLocation,
    submitReport, loading, success, error,
    myIncidents, loadingIncidents,
    resolveIncident, // Properly exported now!
  };
}