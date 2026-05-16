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

// ─── Location search input using Google Maps Geocoding ────────────────────────

function LocationSearch({ onLocationFound, disabled }) {
  const inputRef = useRef(null);

  function handleSearch() {
    const query = inputRef.current?.value?.trim();
    if (!query) return;

    // Use Google Maps Geocoding service
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
        className="px-4 py-2 bg-[#111210] text-white text-[13px] font-medium rounded-lg hover:bg-[#3D3D38] transition-colors disabled:opacity-60"
      >
        Search
      </button>
    </div>
  );
}

// ─── Inner form (needs to be inside APIProvider) ──────────────────────────────

function ReportForm() {
  const {
    form,
    setField,
    setLocation,
    submitReport,
    loading,
    success,
    error,
  } = useReport();

  return (
    <div className="w-full max-w-lg">

      {/* Header */}
      <div className="mb-8">
        <h1
          className="text-[28px] font-bold text-[#111210] mb-1.5"
          style={{ fontFamily: 'Georgia, serif', letterSpacing: '-0.5px' }}
        >
          Report an incident
        </h1>
        <p className="text-[14px] text-[#7A7A72]">
          Help other drivers by reporting what you see on the road.
        </p>
      </div>

      {/* Success banner */}
      {success && (
        <div className="flex items-center gap-3 px-4 py-3 bg-[#EAF3DE] border border-[#B8D98A] rounded-xl text-[13px] text-[#3A6B10] mb-6">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
          Incident reported successfully! Thank you for keeping Yaoundé safe.
        </div>
      )}

      {/* Error banner */}
      {error && (
        <div className="flex items-center gap-3 px-4 py-3 bg-[#FCEBEB] border border-[#F5C0B8] rounded-xl text-[13px] text-[#A32D2D] mb-6">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          {error}
        </div>
      )}

      {/* Form card */}
      <div className="bg-white border border-[#E2E1DB] rounded-2xl p-8" style={{ boxShadow: '0 1px 3px rgba(17,18,16,0.06)' }}>
        <div className="flex flex-col gap-5">

          {/* Incident type */}
          <div className="flex flex-col gap-1">
            <label className="text-[11px] font-medium text-[#3D3D38] uppercase tracking-wide">Incident type</label>
            <select
              value={form.type}
              onChange={(e) => setField('type', e.target.value)}
              disabled={loading}
              className="w-full px-3 py-2 text-[13px] text-[#111210] bg-white border border-[#E2E1DB] rounded-lg outline-none focus:border-[#2563EB] focus:ring-1 focus:ring-[#2563EB] transition-colors disabled:opacity-60"
            >
              <option value="">Select incident type…</option>
              {INCIDENT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>

          {/* Severity */}
          <div className="flex flex-col gap-2">
            <label className="text-[11px] font-medium text-[#3D3D38] uppercase tracking-wide">Severity</label>
            <div className="flex gap-2">
              {SEVERITY_LEVELS.map((level) => {
                const styles = {
                  Low:    { active: 'bg-[#EAF3DE] border-[#B8D98A] text-[#3A6B10]', inactive: 'bg-white border-[#E2E1DB] text-[#7A7A72]' },
                  Medium: { active: 'bg-[#FAEEDA] border-[#E8C97A] text-[#7A4F10]', inactive: 'bg-white border-[#E2E1DB] text-[#7A7A72]' },
                  High:   { active: 'bg-[#FCEBEB] border-[#F5C0B8] text-[#A32D2D]', inactive: 'bg-white border-[#E2E1DB] text-[#7A7A72]' },
                };
                const isActive = form.severity === level;
                return (
                  <button
                    key={level}
                    type="button"
                    onClick={() => setField('severity', level)}
                    disabled={loading}
                    className={`flex-1 py-2 rounded-lg border text-[13px] font-medium transition-colors ${isActive ? styles[level].active : styles[level].inactive}`}
                  >
                    {level}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Description */}
          <div className="flex flex-col gap-1">
            <label className="text-[11px] font-medium text-[#3D3D38] uppercase tracking-wide">Description</label>
            <textarea
              placeholder="Describe what you see — e.g. 'Two cars collided near Carrefour Nlongkak, blocking the right lane.'"
              value={form.description}
              onChange={(e) => setField('description', e.target.value)}
              disabled={loading}
              rows={4}
              className="w-full px-3 py-2 text-[13px] text-[#111210] bg-white border border-[#E2E1DB] rounded-lg outline-none placeholder:text-[#7A7A72] focus:border-[#2563EB] focus:ring-1 focus:ring-[#2563EB] transition-colors resize-none disabled:opacity-60"
            />
          </div>

          {/* Location */}
          <div className="flex flex-col gap-2">
            <label className="text-[11px] font-medium text-[#3D3D38] uppercase tracking-wide">Location</label>

            {/* GPS status */}
            {form.latitude && form.longitude ? (
              <div className="flex items-center gap-2.5 px-3 py-2.5 bg-[#EAF3DE] border border-[#B8D98A] rounded-lg">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#3A6B10" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/>
                </svg>
                <span className="text-[12.5px] text-[#3A6B10] font-medium flex-1">
                  {form.address
                    ? form.address
                    : `GPS: ${form.latitude.toFixed(5)}, ${form.longitude.toFixed(5)}`
                  }
                </span>
                {/* Allow changing location even if GPS found */}
                <button
                  type="button"
                  onClick={() => setLocation({ lat: null, lng: null, address: '' })}
                  className="text-[11px] text-[#3A6B10] underline hover:no-underline"
                >
                  Change
                </button>
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                <div className="flex items-center gap-2.5 px-3 py-2.5 bg-[#FAEEDA] border border-[#E8C97A] rounded-lg">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#7A4F10" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
            className="w-full !bg-[#111210] !rounded-xl !text-[15px] !font-semibold !py-3 mt-2"
          >
            {loading ? 'Submitting…' : 'Submit report'}
          </Button>

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
        <main className="flex-1 flex items-start justify-center py-12 px-4">
          <ReportForm />
        </main>
      </div>
    </APIProvider>
  );
}