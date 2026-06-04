// UrbanFlow — RegisterPage.jsx
// Layer 1 (UI): Register form layout only. No fetch(). No API calls.
// All logic lives in useAuth.js (Layer 2).

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from './useAuth';
import Input from '../../components/Input';
import Button from '../../components/Button';

export default function RegisterPage() {
  const { register, loading, error } = useAuth();

  const [fullName, setFullName]               = useState('');
  const [email, setEmail]                     = useState('');
  const [password, setPassword]               = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [localError, setLocalError]           = useState(null);

  function handleSubmit(e) {
    e.preventDefault();
    setLocalError(null);

    // Client-side validation — passwords must match
    if (password !== confirmPassword) {
      setLocalError('Passwords do not match.');
      return;
    }
    if (password.length < 8) {
      setLocalError('Password must be at least 8 characters.');
      return;
    }

    register({ full_name: fullName, email, password });
  }

  const displayError = localError || error;

  return (
    <div className="min-h-screen bg-[#F7F6F2] relative overflow-hidden">

      {/* Subtle grid texture — matches landing page */}
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

          {/* Quote + checklist — desktop only */}
          <div className="hidden lg:block">
            <p
              className="text-[#111210] font-bold leading-tight mb-4"
              style={{ fontFamily: 'Georgia, serif', fontSize: '32px', letterSpacing: '-0.8px' }}
            >
              "Join thousands of<br />smarter commuters."
            </p>
            <p className="text-[#7A7A72] text-[14px] mb-10">
              Free to join. No credit card. No spam. Ever.
            </p>

            {/* Feature checklist */}
            <div className="flex flex-col gap-3">
              {[
                'Real-time congestion predictions',
                'Community incident reports',
                'Automatic 5 km proximity alerts',
                'Save and revisit your routes',
              ].map((item) => (
                <div
                  key={item}
                  className="flex items-center gap-4 bg-white border border-[#E2E1DB] rounded-2xl px-5 py-3.5"
                  style={{ boxShadow: '0 1px 3px rgba(17,18,16,0.05)' }}
                >
                  <div className="w-5 h-5 rounded-full bg-[#EEF3FD] border border-[#BFCFEF] flex items-center justify-center flex-shrink-0">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                  </div>
                  <span className="text-[13.5px] text-[#3D3D38]">{item}</span>
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
                  Create your account
                </h1>
                <p className="text-[14px] text-[#7A7A72]">
                  Free forever. No credit card required.
                </p>
              </div>

              {/* Error banner */}
              {displayError && (
                <div className="flex items-center gap-2.5 px-4 py-3 bg-[#FCEBEB] border border-[#F5C0B8] rounded-xl text-[13px] text-[#A32D2D] mb-6">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="flex-shrink-0">
                    <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                  </svg>
                  {displayError}
                </div>
              )}

              {/* Form */}
              <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                <Input
                  label="Full name"
                  type="text"
                  placeholder="Jean-Pierre Mvondo"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  autoComplete="name"
                  disabled={loading}
                />

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
                  placeholder="Min. 8 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="new-password"
                  disabled={loading}
                />

                <Input
                  label="Confirm password"
                  type="password"
                  placeholder="Repeat your password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  autoComplete="new-password"
                  disabled={loading}
                />

                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  loading={loading}
                  className="w-full mt-2 !bg-[#111210] !text-white hover:!bg-[#3D3D38] !rounded-xl !text-[15px] !font-semibold !py-3"
                >
                  {loading ? 'Creating account…' : 'Create free account'}
                </Button>
              </form>

              {/* Terms note */}
              <p className="text-center text-[12px] text-[#7A7A72] mt-4 leading-relaxed">
                By signing up you agree to our{' '}
                <a href="#" className="text-[#2563EB] hover:underline">Terms of Service</a>
                {' '}and{' '}
                <a href="#" className="text-[#2563EB] hover:underline">Privacy Policy</a>.
              </p>

              {/* Footer link */}
              <p className="text-center text-[13px] text-[#7A7A72] mt-4">
                Already have an account?{' '}
                <Link to="/login" className="text-[#2563EB] font-medium hover:underline">
                  Log in
                </Link>
              </p>
            </div>

            {/* Mobile-only checklist pills — shown below card */}
            <div className="flex flex-col gap-2.5 mt-5 lg:hidden">
              {[
                'Real-time congestion predictions',
                'Automatic 5 km proximity alerts',
                'Community incident reports',
              ].map((item) => (
                <div
                  key={item}
                  className="flex items-center gap-3 bg-white border border-[#E2E1DB] rounded-2xl px-4 py-3"
                  style={{ boxShadow: '0 1px 3px rgba(17,18,16,0.04)' }}
                >
                  <div className="w-5 h-5 rounded-full bg-[#EEF3FD] border border-[#BFCFEF] flex items-center justify-center flex-shrink-0">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                  </div>
                  <span className="text-[13px] text-[#3D3D38]">{item}</span>
                </div>
              ))}
            </div>

          </div>
        </div>

      </div>
    </div>
  );
}