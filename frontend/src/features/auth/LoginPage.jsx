// UrbanFlow — LoginPage.jsx
// Layer 1 (UI): Login form layout only. No fetch(). No API calls.
// All logic lives in useAuth.js (Layer 2).

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from './useAuth';
import Input from '../../components/Input';
import Button from '../../components/Button';

export default function LoginPage() {
  const { login, loading, error } = useAuth();

  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');

  function handleSubmit(e) {
    e.preventDefault();
    login({ email, password });
  }

  return (
    <div className="min-h-screen bg-[#F7F6F2] relative overflow-hidden">

      {/* Subtle grid texture — same as landing page */}
      <div
        className="absolute inset-0 pointer-events-none opacity-30"
        style={{
          backgroundImage: 'linear-gradient(#E2E1DB 1px, transparent 1px), linear-gradient(90deg, #E2E1DB 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />
      {/* Radial vignette */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{ background: 'radial-gradient(ellipse 80% 70% at 50% 40%, transparent 30%, #F7F6F2 100%)' }}
      />

      {/* Page shell */}
      <div className="relative z-10 min-h-screen flex flex-col lg:flex-row">

        {/* ── Left panel — branding ─────────────────────────── */}
        <div className="flex flex-col justify-between lg:w-[420px] xl:w-[480px] flex-shrink-0 p-8 lg:p-14 lg:min-h-screen">

          {/* Logo */}
          <Link to="/">
            <span className="text-[20px] font-bold select-none" style={{ fontFamily: 'Georgia, serif' }}>
              <span className="text-[#111210]">Urban</span>
              <span className="text-[#2563EB]">Flow</span>
            </span>
          </Link>

          {/* Quote — hidden on mobile, shown on desktop */}
          <div className="hidden lg:block">
            <p
              className="text-[#111210] font-bold leading-tight mb-4"
              style={{ fontFamily: 'Georgia, serif', fontSize: '32px', letterSpacing: '-0.8px' }}
            >
              "Know the road<br />before you drive it."
            </p>
            <p className="text-[#7A7A72] text-[14px] mb-10">
              Real-time traffic intelligence for Yaoundé drivers.
            </p>

            {/* Stat pills */}
            <div className="flex flex-col gap-3">
              {[
                { value: '12,000+', label: 'Active drivers on UrbanFlow' },
                { value: '5 km',    label: 'Proximity alert radius' },
                { value: 'Live',    label: 'Incident feed, updated every 30s' },
              ].map((s) => (
                <div
                  key={s.label}
                  className="flex items-center gap-4 bg-white border border-[#E2E1DB] rounded-2xl px-5 py-4"
                  style={{ boxShadow: '0 1px 3px rgba(17,18,16,0.05)' }}
                >
                  <div
                    className="text-[#111210] text-[22px] font-bold w-20 flex-shrink-0"
                    style={{ fontFamily: 'Georgia, serif', letterSpacing: '-0.5px' }}
                  >
                    {s.value}
                  </div>
                  <div className="text-[13px] text-[#7A7A72] leading-snug">{s.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Bottom fine print — desktop only */}
          <p className="hidden lg:block text-[12px] text-[#B0AFA7]">
            © 2026 UrbanFlow · Made in Yaoundé 🇨🇲
          </p>
        </div>

        {/* ── Right panel — form ──────────────────────────────── */}
        <div className="flex-1 flex items-center justify-center px-6 pb-16 lg:py-14">
          <div className="w-full max-w-[400px]">

            {/* Card */}
            <div
              className="bg-white border border-[#E2E1DB] rounded-3xl p-8 sm:p-10"
              style={{ boxShadow: '0 4px 24px rgba(17,18,16,0.07), 0 1px 4px rgba(17,18,16,0.05)' }}
            >
              {/* Header */}
              <div className="mb-8">
                <h1
                  className="text-[26px] font-bold text-[#111210] mb-1.5"
                  style={{ fontFamily: 'Georgia, serif', letterSpacing: '-0.5px' }}
                >
                  Welcome back
                </h1>
                <p className="text-[14px] text-[#7A7A72]">
                  Log in to your UrbanFlow account.
                </p>
              </div>

              {/* Error banner */}
              {error && (
                <div className="flex items-center gap-2.5 px-4 py-3 bg-[#FCEBEB] border border-[#F5C0B8] rounded-xl text-[13px] text-[#A32D2D] mb-6">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="flex-shrink-0">
                    <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                  </svg>
                  {error}
                </div>
              )}

              {/* Form */}
              <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                <Input
                  label="Email address"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  disabled={loading}
                />

                <Input
                  label="Password"
                  type="password"
                  placeholder="Your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  disabled={loading}
                />

                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  loading={loading}
                  className="w-full mt-2 !bg-[#111210] !text-white hover:!bg-[#3D3D38] !rounded-xl !text-[15px] !font-semibold !py-3"
                >
                  {loading ? 'Logging in…' : 'Log in'}
                </Button>
              </form>

              {/* Footer link */}
              <p className="text-center text-[13px] text-[#7A7A72] mt-6">
                Don't have an account?{' '}
                <Link to="/register" className="text-[#2563EB] font-medium hover:underline">
                  Create one free
                </Link>
              </p>
            </div>

            {/* Mobile-only stat pills — shown below the card */}
            <div className="flex gap-3 mt-5 lg:hidden">
              {[
                { value: '12k+', label: 'Drivers' },
                { value: '5 km', label: 'Alerts' },
                { value: 'Live', label: 'Feed' },
              ].map((s) => (
                <div
                  key={s.label}
                  className="flex-1 bg-white border border-[#E2E1DB] rounded-2xl px-3 py-3 text-center"
                  style={{ boxShadow: '0 1px 3px rgba(17,18,16,0.05)' }}
                >
                  <div
                    className="text-[#111210] text-[18px] font-bold"
                    style={{ fontFamily: 'Georgia, serif' }}
                  >
                    {s.value}
                  </div>
                  <div className="text-[11px] text-[#7A7A72] mt-0.5">{s.label}</div>
                </div>
              ))}
            </div>

          </div>
        </div>

      </div>
    </div>
  );
}