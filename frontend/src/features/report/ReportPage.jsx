// UrbanFlow — ReportPage.jsx
// Layer 1 (UI): Incident report form. No fetch(). No API calls.
// All logic lives in useReport.js (Layer 2).
// Location: GPS auto-detect + manual search fallback via Google Maps Geocoding.

import { useRef } from 'react';
import { useReport } from './useReport';
import Navbar from '../../components/Navbar';
import Button from '../../components/Button';
import { MAPS_LOADER_CONFIG } from '../../lib/constants';
import { APIProvider } from '@vis.gl/react-google-maps';

const INCIDENT_TYPES  = ['Accident','Flooding','Roadblock','Pothole','Police Checkpoint','Construction','Broken Traffic Light','Other'];
const SEVERITY_LEVELS = ['Low', 'Medium', 'High'];

// ─── Severity config ──────────────────────────────────────────────────────────

const SEVERITY_STYLES = {
  Low:    { active: 'bg-[#EAF3DE] border-[#B8D98A] text-[#3A6B10]',   dot: 'bg-[#639922]', badge: 'bg-[#EAF3DE] text-[#3A6B10]' },
  Medium: { active: 'bg-[#FAEEDA] border-[#E8C97A] text-[#7A4F10]',   dot: 'bg-[#BA7517]', badge: 'bg-[#FAEEDA] text-[#7A4F10]' },
  High:   { active: 'bg-[#FCEBEB] border-[#F5C0B8] text-[#A32D2D]',   dot: 'bg-[#D85A30]', badge: 'bg-[#FCEBEB] text-[#A32D2D]' },
};

// ─── Location search ──────────────────────────────────────────────────────────

function LocationSearch({ onLocationFound, disabled }) {
  const inputRef = useRef(null);

  function handleSearch() {
    const query = inputRef.current?.value?.trim();
    if (!query) return;
    const geocoder = new window.google.maps.Geocoder();
    geocoder.geocode(
      { address: `${query}, Yaoundé, Cameroon` },
      (results, status) => {
        if (status === 'OK' && results[0]) {
          const location = results[0].geometry.location;
          onLocationFound({
            lat:     location.lat(),
            lng:     location.lng(),
            address: results[0].formatted_address,
          });
        }
      }
    );
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter') handleSearch();
  }

  return (
    <div className="flex gap-2">
      <input
        ref={inputRef}
        type="text"
        placeholder="e.g. Carrefour Nlongkak, Bastos..."
        disabled={disabled}
        onKeyDown={handleKeyDown}
        className="flex-1 px-3 py-2 text-[13px] text-[#111210] bg-white border border-[#E2E1DB] rounded-lg outline-none placeholder:text-[#7A7A72] focus:border-[#2563EB] focus:ring-1 focus:ring-[#2563EB] transition-colors disabled:opacity-60"
      />
      <button
        type="button"
        onClick={handleSearch}
        disabled={disabled}
        className="px-4 py-2 bg-[#111210] text-white text-[13px] font-medium rounded-lg hover:bg-[#3D3D38] transition-colors disabled:opacity-60 flex-shrink-0"
      >
        Search
      </button>
    </div>
  );
}

// ─── Incident card (past reports) ─────────────────────────────────────────────

function IncidentCard({ incident, onResolve }) {
  const sev = incident.severity || 'Low';
  const styles = SEVERITY_STYLES[sev] || SEVERITY_STYLES.Low;

  return (
    <div className="group p-4 bg-white border border-[#E2E1DB] rounded-xl transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2 min-w-0">
          <div className={`w-2 h-2 rounded-full flex-shrink-0 ${styles.dot}`} />
          <span className="text-[13px] font-semibold text-[#111210] truncate">{incident.type}</span>
        </div>
        <span className={`text-[11px] px-2 py-0.5 rounded-full font-medium flex-shrink-0 ${styles.badge}`}>
          {sev}
        </span>
      </div>

      <p className="text-[12.5px] text-[#5F5E5A] leading-relaxed mb-3 line-clamp-2">
        {incident.description}
      </p>

      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 text-[11px] text-[#7A7A72] min-w-0">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="flex-shrink-0">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/>
          </svg>
          <span className="truncate">
            {incident.address || `${incident.latitude?.toFixed(4)}, ${incident.longitude?.toFixed(4)}`}
          </span>
        </div>
        {incident.is_active && (
          <button
            type="button"
            onClick={() => onResolve(incident._id || incident.id)}
            className="flex-shrink-0 text-[11px] font-medium text-[#2563EB] hover:underline transition-colors"
          >
            Mark resolved
          </button>
        )}
      </div>
    </div>
  );
}

// ─── Field label ──────────────────────────────────────────────────────────────

function FieldLabel({ children }) {
  return (
    <label className="text-[11px] font-semibold tracking-widest uppercase text-[#7A7A72]">
      {children}
    </label>
  );
}

// ─── Inner form ───────────────────────────────────────────────────────────────

function ReportForm() {
  const {
    form,
    setField,
    setLocation,
    submitReport,
    loading,
    success,
    error,
    myIncidents,
    loadingIncidents,
    resolveIncident,
  } = useReport();

  return (
    <div className="w-full max-w-5xl mx-auto px-4 py-8 md:py-12">

      {/* ── Page header ── */}
      <div className="mb-8">
        <div className="flex items-center gap-2.5 mb-3">
          <div className="w-8 h-8 rounded-full bg-[#FCEBEB] flex items-center justify-center">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#D85A30" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
          </div>
          <span className="text-[11px] font-semibold tracking-widest uppercase text-[#7A7A72]">Incident reporting</span>
        </div>
        <h1 className="text-[26px] md:text-[32px] font-bold text-[#111210] leading-tight" style={{ fontFamily: 'Georgia, serif', letterSpacing: '-0.5px' }}>
          Report what you see
        </h1>
        <p className="text-[14px] text-[#7A7A72] mt-1.5">
          Help other drivers navigate Yaoundé safely.
        </p>
      </div>

      {/* ── Two-column layout ── */}
      <div className="flex flex-col lg:flex-row gap-6 items-start">

        {/* ── LEFT: Form card ── */}
        <div className="w-full lg:max-w-[480px] lg:flex-shrink-0">

          {/* Banners */}
          {success && (
            <div className="flex items-center gap-3 px-4 py-3 bg-[#EAF3DE] border border-[#B8D98A] rounded-xl text-[13px] text-[#3A6B10] mb-5">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="flex-shrink-0">
                <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              Incident reported — thank you for keeping Yaoundé safe!
            </div>
          )}
          {error && (
            <div className="flex items-center gap-3 px-4 py-3 bg-[#FCEBEB] border border-[#F5C0B8] rounded-xl text-[13px] text-[#A32D2D] mb-5">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="flex-shrink-0">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              {error}
            </div>
          )}

          <div className="bg-white border border-[#E2E1DB] rounded-2xl overflow-hidden" style={{ boxShadow: '0 1px 4px rgba(17,18,16,0.07)' }}>

            {/* Form top accent strip */}
            <div className="h-1 w-full bg-gradient-to-r from-[#D85A30] via-[#E8C97A] to-[#2563EB]" />

            <div className="p-6 flex flex-col gap-5">

              {/* Incident type */}
              <div className="flex flex-col gap-1.5">
                <FieldLabel>Incident type</FieldLabel>
                <select
                  value={form.type}
                  onChange={(e) => setField('type', e.target.value)}
                  disabled={loading}
                  className="w-full px-3 py-2.5 text-[13px] text-[#111210] bg-white border border-[#E2E1DB] rounded-lg outline-none focus:border-[#2563EB] focus:ring-1 focus:ring-[#2563EB] transition-colors disabled:opacity-60"
                >
                  <option value="">Select incident type…</option>
                  {INCIDENT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>

              {/* Severity */}
              <div className="flex flex-col gap-1.5">
                <FieldLabel>Severity</FieldLabel>
                <div className="grid grid-cols-3 gap-2">
                  {SEVERITY_LEVELS.map((level) => {
                    const isActive = form.severity === level;
                    const s = SEVERITY_STYLES[level];
                    return (
                      <button
                        key={level}
                        type="button"
                        onClick={() => setField('severity', level)}
                        disabled={loading}
                        className={`
                          py-2.5 rounded-lg border text-[13px] font-medium transition-all
                          flex items-center justify-center gap-1.5
                          ${isActive
                            ? s.active
                            : error === 'Please select a severity level.'
                              ? 'bg-white border-[#F5C0B8] text-[#A32D2D]'
                              : 'bg-white border-[#E2E1DB] text-[#7A7A72] hover:border-[#C8C7C1]'
                          }
                        `}
                      >
                        <div className={`w-1.5 h-1.5 rounded-full ${isActive ? s.dot : 'bg-[#C8C7C1]'}`} />
                        {level}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Description */}
              <div className="flex flex-col gap-1.5">
                <FieldLabel>Description</FieldLabel>
                <textarea
                  placeholder="Describe what you see — e.g. 'Two cars collided near Carrefour Nlongkak, blocking the right lane.'"
                  value={form.description}
                  onChange={(e) => setField('description', e.target.value)}
                  disabled={loading}
                  rows={4}
                  className="w-full px-3 py-2.5 text-[13px] text-[#111210] bg-white border border-[#E2E1DB] rounded-lg outline-none placeholder:text-[#7A7A72] focus:border-[#2563EB] focus:ring-1 focus:ring-[#2563EB] transition-colors resize-none disabled:opacity-60"
                />
              </div>

              {/* Location */}
              <div className="flex flex-col gap-1.5">
                <FieldLabel>Location</FieldLabel>
                {form.latitude && form.longitude ? (
                  <div className="flex items-center gap-2.5 px-3 py-2.5 bg-[#EAF3DE] border border-[#B8D98A] rounded-lg">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#3A6B10" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="flex-shrink-0">
                      <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/>
                    </svg>
                    <span className="text-[12.5px] text-[#3A6B10] font-medium flex-1 truncate">
                      {form.address || `GPS: ${form.latitude.toFixed(5)}, ${form.longitude.toFixed(5)}`}
                    </span>
                    <button
                      type="button"
                      onClick={() => setLocation({ lat: null, lng: null, address: '' })}
                      className="text-[11px] text-[#3A6B10] underline hover:no-underline flex-shrink-0"
                    >
                      Change
                    </button>
                  </div>
                ) : (
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center gap-2.5 px-3 py-2.5 bg-[#FAEEDA] border border-[#E8C97A] rounded-lg">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#7A4F10" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="flex-shrink-0">
                        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/>
                      </svg>
                      <span className="text-[12.5px] text-[#7A4F10]">
                        GPS unavailable — search for your location below.
                      </span>
                    </div>
                    <LocationSearch onLocationFound={setLocation} disabled={loading} />
                  </div>
                )}
              </div>

              {/* Submit */}
              <Button
                type="submit"
                variant="primary"
                size="lg"
                loading={loading}
                onClick={submitReport}
                className="w-full !bg-[#111210] !rounded-xl !text-[14px] !font-semibold !py-3 mt-1"
              >
                {loading ? 'Submitting…' : 'Submit report'}
              </Button>

            </div>
          </div>
        </div>

        {/* ── RIGHT: Past incidents panel ── */}
        <div className="w-full lg:flex-1 min-w-0">
          <div className="bg-white border border-[#E2E1DB] rounded-2xl overflow-hidden" style={{ boxShadow: '0 1px 4px rgba(17,18,16,0.07)' }}>

            {/* Panel header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-[#E2E1DB]">
              <div className="flex items-center gap-2">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#7A7A72" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <polyline points="12 6 12 12 16 14"/>
                </svg>
                <span className="text-[13px] font-semibold text-[#111210]">Your reports</span>
              </div>
              {myIncidents.length > 0 && (
                <span className="text-[11px] font-medium px-2 py-0.5 bg-[#F0F6FF] text-[#185FA5] rounded-full">
                  {myIncidents.length} total
                </span>
              )}
            </div>

            {/* Incidents list */}
            <div className="p-4">
              {loadingIncidents ? (
                <div className="flex flex-col gap-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-20 bg-[#F7F6F2] rounded-xl animate-pulse" />
                  ))}
                </div>
              ) : myIncidents.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-10 text-center">
                  <div className="w-10 h-10 rounded-full bg-[#F7F6F2] flex items-center justify-center mb-3">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C8C7C1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
                      <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                    </svg>
                  </div>
                  <p className="text-[13px] font-medium text-[#3D3D38]">No reports yet</p>
                  <p className="text-[12px] text-[#7A7A72] mt-1">Your submitted incidents will appear here.</p>
                </div>
              ) : (
                <div className="flex flex-col gap-3 max-h-[520px] overflow-y-auto pr-1">
                  {myIncidents.map((incident) => (
                    <IncidentCard
                      key={incident.id || incident._id}
                      incident={incident}
                      onResolve={resolveIncident}
                    />
                  ))}
                </div>
              )}
            </div>

          </div>
        </div>

      </div>
    </div>
  );
}

// ─── Main export ──────────────────────────────────────────────────────────────

export default function ReportPage() {
  return (
    <APIProvider apiKey={MAPS_LOADER_CONFIG.apiKey} libraries={MAPS_LOADER_CONFIG.libraries}>
      <div className="min-h-screen flex flex-col bg-[#F7F6F2]">
        <Navbar />
        <main className="flex-1 overflow-y-auto">
          <ReportForm />
        </main>
      </div>
    </APIProvider>
  );
}