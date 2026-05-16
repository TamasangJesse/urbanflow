// UrbanFlow — constants.js
// Golden Rule #4: All magic numbers live here. Never hardcode these in components.

// API Gateway base URL — all requests go through this
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Notification polling interval — 30 seconds in milliseconds
export const NOTIFICATION_POLL_INTERVAL = 30000;

// Proximity alert radius for notifications — 5 km in metres
export const INCIDENT_RADIUS_METERS = 5000;

// Route incident detection radius — 300 metres (checked server-side)
export const ROUTE_INCIDENT_RADIUS_METERS = 300;

// Route incident check polling interval — 30 seconds in milliseconds
export const ROUTE_CHECK_INTERVAL = 30000;

// Google Maps API key loaded from .env — never hardcoded
export const MAPS_LOADER_CONFIG = {
  apiKey: import.meta.env.VITE_GOOGLE_MAPS_API_KEY,
  version: 'weekly',
  libraries: ['places', 'geometry', 'routes'],
};
