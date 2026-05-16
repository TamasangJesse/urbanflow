// UrbanFlow — reportService.js
// Layer 3 (Data): Incident report API calls. No useState. Returns raw data.

import apiClient from '../../lib/apiClient';

const reportService = {
  /**
   * POST /incidents
   * @param {{ type, description, latitude, longitude, severity, reported_by }} incidentData
   */
  submitIncident: (incidentData) => apiClient.post('/incidents', incidentData),
};

export default reportService;
