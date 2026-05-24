// UrbanFlow — reportService.js
// Layer 3 (Data): Incident report API calls. No useState. Returns raw data.

import apiClient from '../../lib/apiClient';

const reportService = {
  submitIncident: (incidentData) => apiClient.post('/incidents', incidentData),
 
  getUserIncidents: (userId) => apiClient.get(`/incidents?reported_by=${userId}`),

  resolveIncident: (id) => apiClient.put(`/incidents/${id}/resolve`),
   }

export default reportService;