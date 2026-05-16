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
    <div className="min-h-screen grid bg-[#F7F6F2]" style={{ gridTemplateColumns: '1fr 1fr' }}>

      {/* ── Left panel — branding ───────────────────────────── */}
      <div
        className="hidden md:flex flex-col justify-between bg-[#111210] p-12"
        style={{ minHeight: '100vh' }}
      >
        {/* Logo */}
        <span className="text-[20px] font-bold select-none" style={{ fontFamily: 'Georgia, serif' }}>
          <span className="text-white">Urban</span>
          <span className="text-[#6B9FFF]">Flow</span>
        </span>

        {/* Centre quote */}
        <div>
          <p
            className="text-white font-bold leading-tight mb-4"
            style={{ fontFamily: 'Georgia, serif', fontSize: '34px', letterSpacing: '-0.8px' }}
          >
            "Know the road<br />before you drive it."
          </p>
          <p className="text-white/40 text-[14px]">
            Real-time traffic intelligence for Yaoundé drivers.
          </p>
        </div>

        {/* Bottom stat pills */}
        <div className="flex gap-3">
          {[
            { value: '12,000+', label: 'Active drivers' },
            { value: '5 km',    label: 'Alert radius' },
            { value: 'Live',    label: 'Incident feed' },
          ].map((s) => (
            <div key={s.label} className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3">
              <div className="text-white text-[18px] font-bold" style={{ fontFamily: 'Georgia, serif' }}>{s.value}</div>
              <div className="text-white/35 text-[12px] mt-0.5">{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Right panel — form ──────────────────────────────── */}
      <div className="flex items-center justify-center p-8">
        <div className="w-full max-w-sm">

          {/* Header */}
          <div className="mb-8">
            <h1
              className="text-[28px] font-bold text-[#111210] mb-1.5"
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
            <div className="flex items-center gap-2.5 px-4 py-3 bg-[#FCEBEB] border border-[#F5C0B8] rounded-lg text-[13px] text-[#A32D2D] mb-6">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
      </div>

    </div>
  );
}