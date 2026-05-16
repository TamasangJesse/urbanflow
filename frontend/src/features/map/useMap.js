// UrbanFlow — useMap.js
// Layer 2 (Logic): Route inputs, prediction results, incidents, rerouting state.
// No JSX. Calls mapService only.

import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuthContext } from '../../context/AuthContext';
import mapService from './mapService';
import { ROUTE_CHECK_INTERVAL } from '../../lib/constants';

// ─── Helpers ──────────────────────────────────────────────────────────────────

/**
 * Convert "Now" / "8:00 AM" to a numeric hour (0–23).
 */
function parseHour(timeStr) {
  if (!timeStr || timeStr === 'Now') {
    return new Date().getHours();
  }
  const [time, period] = timeStr.split(' ');
  let [hours] = time.split(':').map(Number);
  if (period === 'PM' && hours !== 12) hours += 12;
  if (period === 'AM' && hours === 12) hours = 0;
  return hours;
}

/**
 * Convert "Today" / "Monday" to a day-of-week string the backend expects.
 */
function parseDay(dayStr) {
  if (!dayStr || dayStr === 'Today') {
    return new Date().toLocaleDateString('en-US', { weekday: 'long' });
  }
  return dayStr;
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useMap() {
  const { user } = useAuthContext();

  // Route planner inputs
  const [origin, setOrigin]           = useState('');
  const [destination, setDestination] = useState('');
  const [selectedTime, setSelectedTime] = useState('Now');
  const [selectedDay, setSelectedDay]   = useState('Today');

  // Prediction + incidents
  const [predictionResult, setPredictionResult] = useState(null);
  const [incidents, setIncidents]               = useState([]);
  const [predictLoading, setPredictLoading]     = useState(false);
  const [predictError, setPredictError]         = useState(null);
  const [savingRoute, setSavingRoute]           = useState(false);

  // Google Maps directions result
  const [directionsResult, setDirectionsResult] = useState(null);

  // Rerouting state
  const [activeRoutePoints, setActiveRoutePoints]     = useState(null);
  const [currentUserLocation, setCurrentUserLocation] = useState(null);
  const [originalDestination, setOriginalDestination] = useState(null);
  const [detectedIncident, setDetectedIncident]       = useState(null);
  const [showRerouteBanner, setShowRerouteBanner]     = useState(false);

  // Refs for cleanup — Golden Rule #10
  const routeCheckIntervalRef = useRef(null);
  const geoWatchIdRef         = useRef(null);

  // ── Send GPS location on mount for geofencing ────────────────────────────

  useEffect(() => {
    if (!user?.id) return;

    if (navigator.geolocation) {
      geoWatchIdRef.current = navigator.geolocation.watchPosition(
        (pos) => {
          const coords = { lat: pos.coords.latitude, lng: pos.coords.longitude };
          setCurrentUserLocation(coords);
          mapService.updateLocation(user.id, coords.lat, coords.lng).catch(() => {});
        },
        () => {},
        { enableHighAccuracy: true }
      );
    }

    fetchIncidents();

    return () => {
      if (geoWatchIdRef.current !== null) {
        navigator.geolocation.clearWatch(geoWatchIdRef.current);
      }
    };
  }, [user?.id]);

  async function fetchIncidents(area = 'current') {
    try {
      const data = await mapService.getIncidents(area);
      setIncidents(Array.isArray(data) ? data : (data?.incidents || []));
    } catch {
      // Non-critical
    }
  }

  // ── Route incident polling ────────────────────────────────────────────────

  const checkRouteForIncidents = useCallback(async (points) => {
    if (!points || points.length === 0) return;
    try {
      const data = await mapService.checkRoute(points);
      if (data?.incident_detected && data?.incident) {
        setDetectedIncident(data.incident);
        setShowRerouteBanner(true);
      }
    } catch {
      // Non-critical
    }
  }, []);

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
      if (routeCheckIntervalRef.current) {
        clearInterval(routeCheckIntervalRef.current);
      }
    };
  }, [activeRoutePoints, checkRouteForIncidents]);

  // ── Prediction — uses destination as location_name ───────────────────────

  async function predictCongestion() {
    if (!origin || !destination) return;
    setPredictLoading(true);
    setPredictError(null);
    try {
      const hour      = parseHour(selectedTime);
      const dayOfWeek = parseDay(selectedDay);

      // Use current GPS coords if available, otherwise use Yaoundé center
      const lat = currentUserLocation?.lat ?? 3.848;
      const lng = currentUserLocation?.lng ?? 11.5021;

      const data = await mapService.predictLocation(
        destination,  // location_name — predict congestion at the destination
        hour,
        dayOfWeek,
        lat,
        lng
      );
      setPredictionResult(data);
    } catch (err) {
      setPredictError(err.message || 'Prediction failed. Please try again.');
    } finally {
      setPredictLoading(false);
    }
  }

  // ── Called by MapPage when Google Maps draws the route ────────────────────

  function onRouteDrawn(result, destinationInput) {
    setDirectionsResult(result);
    setOriginalDestination(destinationInput);
    const points = result.routes[0].overview_path.map((point) => [
      point.lat(),
      point.lng(),
    ]);
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
  }

  function dismissRerouteBanner() {
    setShowRerouteBanner(false);
  }

  function updateRouteAfterReroute(newResult) {
    setDirectionsResult(newResult);
    setShowRerouteBanner(false);
    const newPoints = newResult.routes[0].overview_path.map((point) => [
      point.lat(),
      point.lng(),
    ]);
    setActiveRoutePoints(newPoints);
  }

  async function saveCurrentRoute() {
    if (!predictionResult || !user?.id) return;
    setSavingRoute(true);
    try {
      await mapService.saveRoute(user.id, {
        origin,
        destination,
        prediction: predictionResult,
      });
    } catch {
      // Non-critical
    } finally {
      setSavingRoute(false);
    }
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
    currentUserLocation,
    originalDestination,
    detectedIncident,
    showRerouteBanner,
    dismissRerouteBanner,
    updateRouteAfterReroute,
  };
}