// UrbanFlow — mapService.js
// Layer 3 (Data): All map/traffic API calls. No useState. Returns raw data.

import apiClient from '../../lib/apiClient';

const mapService = {
  /**
   * GET /predict
   * Matches exactly what the backend expects:
   * ?location_name=Bastos&hour=8&day_of_week=Monday&latitude=3.8830&longitude=11.5150
   */
  predictLocation: (locationName, hour, dayOfWeek, latitude, longitude) => {
    const params = new URLSearchParams({
      location_name: locationName,
      hour:          hour,
      day_of_week:   dayOfWeek,
      latitude:      latitude,
      longitude:     longitude,
    });
    return apiClient.get(`/predict?${params.toString()}`);
  },

  /** GET /incidents?area=X — incident pins for the map */
  getIncidents: (area) =>
    apiClient.get(`/incidents?area=${encodeURIComponent(area)}`),

  /** GET /incidents/near — radius-based incident query */
  getIncidentsNear: (lat, lng, radius) =>
    apiClient.get(`/incidents/near?lat=${lat}&lng=${lng}&radius=${radius}`),

  /** PUT /users/{id}/location — send GPS coords for geofencing */
  updateLocation: (userId, lat, lng) =>
    apiClient.put(`/users/${userId}/location`, { latitude: lat, longitude: lng }),

  /** PUT /users/{id}/location — send GPS coords + active route for geofencing */
updateLocation: (userId, lat, lng, routePoints = null) =>
  apiClient.put(`/users/${userId}/location`, { 
    latitude: lat, 
    longitude: lng,
    route_points: routePoints 
  }),

  /** POST /incidents/check-route — check if any incident is within 300m of route */
  checkRoute: (routePoints) =>
    apiClient.post('/incidents/check-route', { route_points: routePoints }),

  /** Save a route to user profile */
  saveRoute: (userId, routeData) =>
    apiClient.put(`/users/${userId}`, { saved_route: routeData }),
};

export default mapService;