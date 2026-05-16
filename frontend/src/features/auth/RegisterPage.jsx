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

  const [fullName, setFullName]           = useState('');
  const [email, setEmail]                 = useState('');
  const [password, setPassword]           = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [localError, setLocalError]       = useState(null);

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
            "Join thousands of<br />smarter commuters."
          </p>
          <p className="text-white/40 text-[14px]">
            Free to join. No credit card. No spam. Ever.
          </p>
        </div>

        {/* Checklist */}
        <div className="flex flex-col gap-3">
          {[
            'Real-time congestion predictions',
            'Community incident reports',
            'Automatic 5 km proximity alerts',
            'Save and revisit your routes',
          ].map((item) => (
            <div key={item} className="flex items-center gap-3">
              <div className="w-5 h-5 rounded-full bg-[#2563EB]/20 border border-[#2563EB]/40 flex items-center justify-center flex-shrink-0">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#6B9FFF" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </div>
              <span className="text-white/60 text-[13.5px]">{item}</span>
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
              Create your account
            </h1>
            <p className="text-[14px] text-[#7A7A72]">
              Free forever. No credit card required.
            </p>
          </div>

          {/* Error banner */}
          {displayError && (
            <div className="flex items-center gap-2.5 px-4 py-3 bg-[#FCEBEB] border border-[#F5C0B8] rounded-lg text-[13px] text-[#A32D2D] mb-6">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
      </div>

    </div>
  );
}