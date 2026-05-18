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
  const [form, setForm]           = useState(INITIAL_FORM);
  const [loading, setLoading]     = useState(false);
  const [success, setSuccess]     = useState(false);
  const [error, setError]         = useState(null);
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

  // Load user's past incidents
  useEffect(() => {
    if (!user?.id) return;
    setLoadingIncidents(true);
    
    reportService.getUserIncidents(user.id)
      .then((res) => {
        // Axios wraps the response body in res.data
        const responseData = res?.data || res;
        
        console.log("Extracted payload inside hook:", responseData);

        // Your backend returns an object containing an "incidents" array
        if (responseData && Array.isArray(responseData.incidents)) {
          setMyIncidents(responseData.incidents);
        } else if (Array.isArray(responseData)) {
          setMyIncidents(responseData);
        } else {
          setMyIncidents([]);
        }
      })
      .catch((err) => {
        console.error("Fetch block caught error:", err);
      })
      .finally(() => setLoadingIncidents(false));
  }, [user?.id]);

  function setField(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function setLocation({ lat, lng, address }) {
    setForm((prev) => ({ ...prev, latitude: lat, longitude: lng, address: address || '' }));
  }

  async function submitReport() {
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
      
      // Safe refresh reload matching the backend dictionary structure
      const res = await reportService.getUserIncidents(user.id);
      const responseData = res?.data || res;

      if (responseData && Array.isArray(responseData.incidents)) {
        setMyIncidents(responseData.incidents);
      } else if (Array.isArray(responseData)) {
        setMyIncidents(responseData);
      }
    } catch (err) {
      setError(err.message || 'Failed to submit report. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return {
    form, setField, setLocation,
    submitReport, loading, success, error,
    myIncidents, loadingIncidents,
  };
}