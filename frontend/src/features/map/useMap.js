// UrbanFlow — useMap.js
// Layer 2 (Logic): Route inputs, prediction results, incidents, rerouting state.
// Fix: Cleaned up geolocation callbacks and integrated instant WebSocket event bindings.

import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuthContext } from '../../context/AuthContext';
import mapService from './mapService';
import { ROUTE_CHECK_INTERVAL } from '../../lib/constants';

function parseHour(timeStr) {
  if (!timeStr || timeStr === 'Now') return new Date().getHours();
  const [time, period] = timeStr.split(' ');
  let [hours] = time.split(':').map(Number);
  if (period === 'PM' && hours !== 12) hours += 12;
  if (period === 'AM' && hours === 12) hours = 0;
  return hours;
}

function parseDay(dayStr) {
  if (!dayStr || dayStr === 'Today')
    return new Date().toLocaleDateString('en-US', { weekday: 'long' });
  return dayStr;
}

const STORAGE_KEY = 'urbanflow_map_state';

function loadMapState() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : null;
  } catch { return null; }
}

function saveMapState(state) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch {}
}

function clearMapState() {
  localStorage.removeItem(STORAGE_KEY);
}

export function useMap() {
  const { user } = useAuthContext();
  const saved = loadMapState();

  const [origin, setOrigin]             = useState(saved?.origin || '');
  const [destination, setDestination]   = useState(saved?.destination || '');
  const [selectedTime, setSelectedTime] = useState(saved?.selectedTime || 'Now');
  const [selectedDay, setSelectedDay]   = useState(saved?.selectedDay || 'Today');
  const [predictionResult, setPredictionResult] = useState(saved?.predictionResult || null);

  const [incidents, setIncidents]           = useState([]);
  const [predictLoading, setPredictLoading] = useState(false);
  const [predictError, setPredictError]     = useState(null);
  const [savingRoute, setSavingRoute]       = useState(false);
  const [directionsResult, setDirectionsResult] = useState(null);

  const [activeRoutePoints, setActiveRoutePoints]     = useState(null);
  const [currentUserLocation, setCurrentUserLocation] = useState(null);
  const [originalDestination, setOriginalDestination] = useState(saved?.destination || null);
  const [detectedIncident, setDetectedIncident]       = useState(null);
  const [showRerouteBanner, setShowRerouteBanner]     = useState(false);

  const routeCheckIntervalRef = useRef(null);
  const geoWatchIdRef         = useRef(null);


  const [toast, setToast] = useState(null);

  // Persist to localStorage on every change
  useEffect(() => {
    saveMapState({ origin, destination, selectedTime, selectedDay, predictionResult });
  }, [origin, destination, selectedTime, selectedDay, predictionResult]);

  // Geolocation watch lifecycle
  useEffect(() => {
    if (!user?.id) return;
    if (navigator.geolocation) {
      geoWatchIdRef.current = navigator.geolocation.watchPosition(
        (pos) => {
          const coords = { lat: pos.coords.latitude, lng: pos.coords.longitude };
          setCurrentUserLocation(coords);
          mapService.updateLocation(user.id, coords.lat, coords.lng, activeRoutePoints).catch(() => {});
        },
        () => {}, 
        { enableHighAccuracy: true }
      );
    }
    fetchIncidents();
    return () => {
      if (geoWatchIdRef.current !== null)
        navigator.geolocation.clearWatch(geoWatchIdRef.current);
    };
  }, [user?.id, activeRoutePoints]);

  async function fetchIncidents(area = 'current') {
    try {
      const data = await mapService.getIncidents(area);
      setIncidents(Array.isArray(data) ? data : (data?.incidents || []));
    } catch {}
  }

  const checkRouteForIncidents = useCallback(async (points) => {
    if (!points || points.length === 0) return;
    try {
      const data = await mapService.checkRoute(points);
      if (data?.incident_detected && data?.incident) {
        setDetectedIncident(data.incident);
        setShowRerouteBanner(true);
      }
    } catch {}
  }, []);

  // Standard interval polling fallback loop
  useEffect(() => {
    if (routeCheckIntervalRef.current) {
      clearInterval(routeCheckIntervalRef.current);
      routeCheckIntervalRef.current = null;
    }
    if (!activeRoutePoints) return;
    checkRouteForIncidents(activeRoutePoints);
    routeCheckIntervalRef.current = setInterval(() => {
      checkRouteForIncidents(activeRoutePoints);
    }, ROUTE_CHECK_INTERVAL);
    return () => {
      if (routeCheckIntervalRef.current) clearInterval(routeCheckIntervalRef.current);
    };
  }, [activeRoutePoints, checkRouteForIncidents]);

  // Instant real-time listener triggered by Step 1 event broadcast
  useEffect(() => {
    const handleInstantIncidentCheck = () => {
      if (activeRoutePoints) {
        fetchIncidents();
        checkRouteForIncidents(activeRoutePoints);
      }
    };

    window.addEventListener('URBANFLOW_NEW_INCIDENT', handleInstantIncidentCheck);
    return () => {
      window.removeEventListener('URBANFLOW_NEW_INCIDENT', handleInstantIncidentCheck);
    };
  }, [activeRoutePoints, checkRouteForIncidents]);




  useEffect(() => {
   function handleIncidentResolved(e) {
    const { incident_id, address } = e.detail || {};
    if (!incident_id) return;

    setIncidents((prev) =>
      prev.filter((inc) => (inc._id ?? inc.id) !== incident_id)
    );

    if (detectedIncident?._id === incident_id || detectedIncident?.id === incident_id) {
      setShowRerouteBanner(false);
      setDetectedIncident(null);
    }

    const message = address
      ? `Incident resolved: ${address}`
      : 'An incident near you has been resolved.';

    setToast(message);
  }

  window.addEventListener('URBANFLOW_INCIDENT_RESOLVED', handleIncidentResolved);
  return () => window.removeEventListener('URBANFLOW_INCIDENT_RESOLVED', handleIncidentResolved);
}, [detectedIncident]);

  async function predictCongestion() {
    if (!origin || !destination) return;
    setPredictLoading(true);
    setPredictError(null);
    try {
      const hour      = parseHour(selectedTime);
      const dayOfWeek = parseDay(selectedDay);
      const lat = currentUserLocation?.lat ?? 3.848;
      const lng = currentUserLocation?.lng ?? 11.5021;
      const data = await mapService.predictLocation(destination, hour, dayOfWeek, lat, lng);
      setPredictionResult(data);
    } catch (err) {
      setPredictError(err.message || 'Prediction failed. Please try again.');
    } finally {
      setPredictLoading(false);
    }
  }

  function onRouteDrawn(result, destinationInput) {
    setDirectionsResult(result);
    setOriginalDestination(destinationInput);
    const points = result.routes[0].overview_path.map((p) => [p.lat(), p.lng()]);
    setActiveRoutePoints(points);
    setShowRerouteBanner(false);
    setDetectedIncident(null);
  }

  function clearRoute() {
    setDirectionsResult(null);
    setActiveRoutePoints(null);
    setPredictionResult(null);
    setShowRerouteBanner(false);
    setDetectedIncident(null);
    setOriginalDestination(null);
    setOrigin('');
    setDestination('');
    clearMapState();
  }

  function dismissRerouteBanner() { setShowRerouteBanner(false); }

  function updateRouteAfterReroute(newResult) {
    setDirectionsResult(newResult);
    setShowRerouteBanner(false);
    const newPoints = newResult.routes[0].overview_path.map((p) => [p.lat(), p.lng()]);
    setActiveRoutePoints(newPoints);
  }

  async function saveCurrentRoute() {
    if (!predictionResult || !user?.id) return;
    setSavingRoute(true);
    try {
      await mapService.saveRoute(user.id, { origin, destination, prediction: predictionResult });
    } catch {} finally { setSavingRoute(false); }
  }

  return {
    origin, setOrigin,
    destination, setDestination,
    selectedTime, setSelectedTime,
    selectedDay, setSelectedDay,
    predictionResult,
    incidents,
    directionsResult,
    predictLoading,
    predictError,
    savingRoute,
    predictCongestion,
    onRouteDrawn,
    clearRoute,
    saveCurrentRoute,
    setIncidents, 
    currentUserLocation,
    originalDestination,
    detectedIncident,
    showRerouteBanner,
    dismissRerouteBanner,
    updateRouteAfterReroute,
    toast,
    clearToast: () => setToast(null),
  };
}