
// UrbanFlow — MapPage.jsx
// Layer 1 (UI): Map layout, route planner panel, prediction results, reroute banner.
// No fetch(). No API calls. All logic lives in useMap.js (Layer 2).
// Note: DirectionsRenderer is not in @vis.gl/react-google-maps — we use
// useMapsLibrary to access the native Google Maps DirectionsRenderer directly.

import { useState, useRef, useEffect } from 'react';
import { APIProvider, Map, Marker, AdvancedMarker, useMap as useGoogleMap, useMapsLibrary } from '@vis.gl/react-google-maps';
import Navbar from '../../components/Navbar';
import Button from '../../components/Button';
import CongestionPill from '../../components/CongestionPill';
import { useMap } from './useMap';
import { MAPS_LOADER_CONFIG } from '../../lib/constants';
import { Toast } from '../../components/Toast';
import ChatPanel from '../rag/ChatPanel';

// ─── Constants ────────────────────────────────────────────────────────────────

const YAOUNDE_CENTER = { lat: 3.848, lng: 11.5021 };
const TIME_OPTIONS   = ['Now','6:00 AM','7:00 AM','8:00 AM','9:00 AM','12:00 PM','3:00 PM','5:00 PM','6:00 PM','8:00 PM'];
const DAY_OPTIONS    = ['Today','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];

// ─── Small shared pieces ──────────────────────────────────────────────────────

function PanelSection({ title, children }) {
  return (
    <div className="border-b border-[#E2E1DB] last:border-b-0 px-5 py-4">
      {title && (
        <div className="text-[11px] font-semibold tracking-widest uppercase text-[#7A7A72] mb-3">
          {title}
        </div>
      )}
      {children}
    </div>
  );
}

function RouteInput({ label, placeholder, value, onChange, disabled, showLocationBtn, onUseLocation }) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center justify-between">
        <label className="text-[11px] font-medium text-[#3D3D38] uppercase tracking-wide">{label}</label>
        {showLocationBtn && (
          <button
            type="button"
            onClick={onUseLocation}
            disabled={disabled}
            className="flex items-center gap-1 text-[11px] text-[#2563EB] font-medium hover:underline disabled:opacity-50"
          >
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>
            </svg>
            Use my location
          </button>
        )}
      </div>
      <input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="w-full px-3 py-2 text-[13px] text-[#111210] bg-white border border-[#E2E1DB] rounded-lg outline-none placeholder:text-[#7A7A72] focus:border-[#2563EB] focus:ring-1 focus:ring-[#2563EB] transition-colors disabled:opacity-60"
      />
    </div>
  );
}

function SelectField({ label, value, onChange, options }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[11px] font-medium text-[#3D3D38] uppercase tracking-wide">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 text-[13px] text-[#111210] bg-white border border-[#E2E1DB] rounded-lg outline-none focus:border-[#2563EB] focus:ring-1 focus:ring-[#2563EB] transition-colors"
      >
        {options.map((opt) => <option key={opt} value={opt}>{opt}</option>)}
      </select>
    </div>
  );
}

// ─── Directions layer (native Google Maps API inside the Map context) ─────────
// This component lives INSIDE <Map> so it has access to the map instance.

function DirectionsLayer({ directionsResult }) {
  const map        = useGoogleMap();
  const routesLib  = useMapsLibrary('routes');
  const rendererRef = useRef(null);

  useEffect(() => {
    if (!routesLib || !map) return;

    // Create renderer once
    if (!rendererRef.current) {
      rendererRef.current = new routesLib.DirectionsRenderer({
        suppressMarkers: false,
        polylineOptions: {
          strokeColor: '#2563EB',
          strokeWeight: 5,
          strokeOpacity: 0.85,
        },
      });
    }
    rendererRef.current.setMap(map);

    return () => {
      if (rendererRef.current) rendererRef.current.setMap(null);
    };
  }, [routesLib, map]);

  useEffect(() => {
    if (!rendererRef.current) return;
    if (directionsResult) {
      rendererRef.current.setDirections(directionsResult);
    } else {
      rendererRef.current.setDirections({ routes: [] });
    }
  }, [directionsResult]);

  return null;
}

// ─── Directions Service hook (lives inside APIProvider context) ───────────────

function useDirectionsService() {
  const routesLib = useMapsLibrary('routes');
  const serviceRef = useRef(null);

  useEffect(() => {
    if (!routesLib) return;
    serviceRef.current = new routesLib.DirectionsService();
  }, [routesLib]);

  return serviceRef;
}

// ─── Reroute Banner ───────────────────────────────────────────────────────────

function RerouteBanner({ incident, onDismiss, onReroute, rerouteLoading, rerouted }) {
  return (
    <div
      className={`absolute top-4 left-1/2 -translate-x-1/2 z-20 flex items-center gap-3 rounded-2xl px-5 py-3.5 bg-white ${rerouted ? 'border border-[#B8D98A]' : 'border border-[#F5C0B8]'}`}
      style={{ width: '420px', boxShadow: '0 8px 24px rgba(17,18,16,0.12)' }}
    >
      <div className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 ${rerouted ? 'bg-[#EAF3DE]' : 'bg-[#FCEBEB]'}`}>
        {rerouted ? (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#3A6B10" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
        ) : (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#D85A30" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className={`text-[13px] font-semibold ${rerouted ? 'text-[#3A6B10]' : 'text-[#111210]'}`}>
          {rerouted ? 'Route updated — incident avoided!' : 'Incident on your route'}
        </div>
        <div className="text-[12px] text-[#7A7A72] truncate">
          {rerouted ? 'A safer route has been calculated.' : `${incident?.type || 'Incident'} — ${incident?.description || 'Detected within 300m of your route.'}`}
        </div>
      </div>
      {!rerouted && (
        <div className="flex items-center gap-2 flex-shrink-0">
          <Button variant="ghost-red" size="sm" loading={rerouteLoading} onClick={onReroute}>Reroute</Button>
          <button onClick={onDismiss} className="w-6 h-6 flex items-center justify-center rounded-full text-[#7A7A72] hover:bg-[#F5F5F3] transition-colors">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}

// ─── Prediction Results ───────────────────────────────────────────────────────

function PredictionResults({ result, onSave, saving, onClear }) {
  if (!result) return null;
  return (
    <PanelSection title="Prediction result">
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <span className="text-[13px] text-[#3D3D38]">Congestion level</span>
          <CongestionPill level={result.congestion_level || result.predicted_congestion || 'Low'} />
        </div>
        {result.estimated_travel_time && (
          <div className="flex items-center justify-between">
            <span className="text-[13px] text-[#3D3D38]">Estimated travel time</span>
            <span className="text-[13px] font-semibold text-[#111210]">{result.estimated_travel_time}</span>
          </div>
        )}
        {result.best_departure_time && (
          <div className="flex items-center justify-between">
            <span className="text-[13px] text-[#3D3D38]">Best departure</span>
            <span className="text-[13px] font-semibold text-[#2563EB]">{result.best_departure_time}</span>
          </div>
        )}
        {result.recommendation && (
          <div className="bg-[#F7F6F2] border border-[#E2E1DB] rounded-lg px-3 py-2.5 text-[12.5px] text-[#3D3D38] leading-relaxed">
            {result.recommendation}
          </div>
        )}
        <div className="flex gap-2 pt-1">
          <Button variant="primary" size="sm" loading={saving} onClick={onSave} className="flex-1 !bg-[#111210] !rounded-lg">Save route</Button>
          <Button variant="outline" size="sm" onClick={onClear} className="flex-1 !rounded-lg">Clear</Button>
        </div>
      </div>
    </PanelSection>
  );
}

// ─── Incidents list ───────────────────────────────────────────────────────────

function IncidentsList({ incidents }) {
  const severityColor = {
    low:    { bg: '#EAF3DE', text: '#639922' },
    medium: { bg: '#FAEEDA', text: '#BA7517' },
    high:   { bg: '#FCEBEB', text: '#D85A30' },
  };

  return (
    <PanelSection title={`Nearby incidents${incidents.length ? ` (${incidents.length})` : ''}`}>
      {incidents.length === 0 ? (
        <p className="text-[12.5px] text-[#7A7A72]">No incidents reported in this area.</p>
      ) : (
        <div className="flex flex-col gap-2 max-h-48 overflow-y-auto pr-1">
          {incidents.map((inc, i) => {
            const colors = severityColor[(inc.severity || 'low').toLowerCase()] || severityColor.low;
            return (
              <div key={inc.id || i} className="flex items-start gap-2.5 p-2.5 bg-[#F7F6F2] rounded-lg border border-[#E2E1DB]">
                <div className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0 mt-0.5" style={{ backgroundColor: colors.bg, color: colors.text }}>!</div>
                <div className="flex-1 min-w-0">
                  <div className="text-[12.5px] font-medium text-[#111210]">{inc.type || 'Incident'}</div>
                  <div className="text-[11.5px] text-[#7A7A72] truncate">{inc.description || 'No description'}</div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </PanelSection>
  );
}

// ─── Inner map page (inside APIProvider) ─────────────────────────────────────
// Separated so hooks that need APIProvider context work correctly.

function MapPageInner() {
  const {
    origin, setOrigin,
    destination, setDestination,
    selectedTime, setSelectedTime,
    selectedDay, setSelectedDay,
    predictionResult,
    incidents,
    setIncidents,        // ← added
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
    toast,
    clearToast,
    updateRouteAfterReroute,
  } = useMap();

  const [rerouteLoading, setRerouteLoading] = useState(false);
  const [rerouted, setRerouted] = useState(false);
  const directionsServiceRef = useDirectionsService();
  const [chatOpen, setChatOpen] = useState(false);

  
  // ── everything below stays exactly the same as before ────────────────────

  async function handleGetDirections() {
    if (!origin || !destination) return;
    await predictCongestion();
    if (!directionsServiceRef.current) return;
    directionsServiceRef.current.route(
      { origin, destination, travelMode: 'DRIVING' },
      (result, status) => {
        if (status === 'OK') onRouteDrawn(result, destination);
      }
    );
  }

  async function handleReroute() {
    if (!currentUserLocation || !originalDestination || !directionsServiceRef.current) return;
    setRerouteLoading(true);
    try {
      const routeRequest = {
        origin:                   currentUserLocation,
        destination:              originalDestination,
        travelMode:               'DRIVING',
        provideRouteAlternatives: true,
      };
      if (detectedIncident?.latitude && detectedIncident?.longitude) {
        routeRequest.waypoints = [];
        routeRequest.avoidHighways = false;
      }
      directionsServiceRef.current.route(routeRequest, (result, status) => {
        if (status === 'OK') {
          const alt = result.routes.length > 1
            ? { ...result, routes: [result.routes[1], result.routes[0]] }
            : result;
          updateRouteAfterReroute(alt);
          setRerouted(true);
          setTimeout(() => {
            setRerouted(false);
            dismissRerouteBanner();
          }, 3000);
        }
      });
    } finally {
      setRerouteLoading(false);
    }
  }

  return (
    <div className="flex flex-1 overflow-hidden">
      {/* ── Sidebar ── */}
      <aside className="flex flex-col bg-white border-r border-[#E2E1DB] overflow-y-auto flex-shrink-0" style={{ width: '320px' }}>
        <PanelSection title="Plan your route">
          <div className="flex flex-col gap-3">
            <RouteInput
              label="From"
              placeholder="e.g. Bastos, Yaoundé"
              value={origin}
              onChange={setOrigin}
              disabled={predictLoading}
              showLocationBtn={true}
              onUseLocation={() => {
                if (currentUserLocation) {
                  const geocoder = new window.google.maps.Geocoder();
                  geocoder.geocode({ location: currentUserLocation }, (results, status) => {
                    if (status === 'OK' && results[0]) {
                      setOrigin(results[0].formatted_address);
                    } else {
                      setOrigin(`${currentUserLocation.lat.toFixed(5)}, ${currentUserLocation.lng.toFixed(5)}`);
                    }
                  });
                }
              }}
            />
            <RouteInput label="To" placeholder="e.g. Melen, Yaoundé" value={destination} onChange={setDestination} disabled={predictLoading} />
            <div className="grid grid-cols-2 gap-2">
              <SelectField label="Time" value={selectedTime} onChange={setSelectedTime} options={TIME_OPTIONS} />
              <SelectField label="Day"  value={selectedDay}  onChange={setSelectedDay}  options={DAY_OPTIONS}  />
            </div>
            {predictError && (
              <div className="flex items-center gap-2 px-3 py-2 bg-[#FCEBEB] border border-[#F5C0B8] rounded-lg text-[12px] text-[#A32D2D]">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                {predictError}
              </div>
            )}
            <Button variant="primary" size="md" loading={predictLoading} onClick={handleGetDirections} className="w-full !bg-[#111210] !rounded-lg !text-[13px] !font-semibold mt-1">
              {predictLoading ? 'Predicting…' : 'Get route & prediction'}
            </Button>
          </div>
        </PanelSection>

        <PredictionResults result={predictionResult} onSave={saveCurrentRoute} saving={savingRoute} onClear={clearRoute} />
        <IncidentsList incidents={incidents} />
      </aside>

      {/* ── Map ── */}
      <div className="flex-1 relative">
        <Map
          defaultCenter={YAOUNDE_CENTER}
          defaultZoom={13}
          gestureHandling="greedy"
          mapId="urbanflow_map"
          style={{ width: '100%', height: '100%' }}
        >
          {currentUserLocation && (
            <Marker position={currentUserLocation} title="Your location" />
          )}
          {incidents.filter((i) => i.latitude && i.longitude).map((inc, i) => (
            <Marker key={inc.id || i} position={{ lat: inc.latitude, lng: inc.longitude }} title={inc.type} />
          ))}
          {detectedIncident?.latitude && detectedIncident?.longitude && (
            <AdvancedMarker
              position={{ lat: detectedIncident.latitude, lng: detectedIncident.longitude }}
              title={`⚠️ ${detectedIncident.type}: ${detectedIncident.description}`}
            >
              <div style={{
                width: '36px', height: '36px', borderRadius: '50%',
                backgroundColor: '#EF4444', border: '3px solid white',
                boxShadow: '0 4px 12px rgba(239,68,68,0.5)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '18px', animation: 'pulse 1.5s infinite',
              }}>
                ⚠️
              </div>
            </AdvancedMarker>
          )}
          <DirectionsLayer directionsResult={directionsResult} />
        </Map>

        {showRerouteBanner && detectedIncident && (
          <RerouteBanner
            incident={detectedIncident}
            onDismiss={dismissRerouteBanner}
            onReroute={handleReroute}
            rerouteLoading={rerouteLoading}
            rerouted={rerouted}
          />
        )}
      </div>

      {/* ─── CHAT PANEL HUD ELEMENT ─── */}
      <ChatPanel open={chatOpen} onClose={() => setChatOpen(false)} />
      {toast && <Toast message={toast} onDismiss={clearToast} />}
    </div>
  );
}
// ─── Main export ──────────────────────────────────────────────────────────────

export default function MapPage() {
  return (
    <APIProvider apiKey={MAPS_LOADER_CONFIG.apiKey} libraries={MAPS_LOADER_CONFIG.libraries}>
      <div className="flex flex-col h-screen bg-[#F7F6F2] overflow-hidden">
        <Navbar />
        <MapPageInner />
      </div>
    </APIProvider>
  );
}