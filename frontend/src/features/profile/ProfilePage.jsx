// UrbanFlow — ProfilePage.jsx
// Layer 1 (UI): Profile info, saved routes, update form, delete account.
// No fetch(). No API calls. All logic lives in useProfile.js (Layer 2).

import { useState, useEffect } from 'react';
import { useProfile } from './useProfile';
import Navbar from '../../components/Navbar';
import Button from '../../components/Button';
import Input from '../../components/Input';
import { PageLoader } from '../../components/LoadingSpinner';

function SectionCard({ title, description, children }) {
  return (
    <div
      className="bg-white border border-[#E2E1DB] rounded-2xl overflow-hidden"
      style={{ boxShadow: '0 1px 3px rgba(17,18,16,0.06)' }}
    >
      <div className="px-7 py-5 border-b border-[#E2E1DB]">
        <h2 className="text-[16px] font-semibold text-[#111210]">{title}</h2>
        {description && <p className="text-[13px] text-[#7A7A72] mt-0.5">{description}</p>}
      </div>
      <div className="px-7 py-6">{children}</div>
    </div>
  );
}

function SavedRouteCard({ route, onDelete }) {
  return (
    <div className="flex items-center justify-between p-4 bg-[#F7F6F2] border border-[#E2E1DB] rounded-xl">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-[#E6F1FB] flex items-center justify-center flex-shrink-0">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/>
          </svg>
        </div>
        <div>
          <div className="text-[13px] font-medium text-[#111210]">
            {route.origin} → {route.destination}
          </div>
          {route.prediction?.congestion_level && (
            <div className="text-[11.5px] text-[#7A7A72] mt-0.5">
              Last prediction: {route.prediction.congestion_level} congestion
            </div>
          )}
        </div>
      </div>
      <button
        onClick={() => onDelete(route.id)}
        className="w-7 h-7 flex items-center justify-center rounded-lg text-[#7A7A72] hover:bg-[#FCEBEB] hover:text-[#D85A30] transition-colors"
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a1 1 0 011-1h4a1 1 0 011 1v2"/>
        </svg>
      </button>
    </div>
  );
}

export default function ProfilePage() {
  const {
    profile,
    savedRoutes,
    loading,
    saving,
    error,
    successMessage,
    updateProfile,
    deleteUser,
    deleteRoute,
  } = useProfile();

  const [fullName, setFullName]           = useState('');
  const [email, setEmail]                 = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword]     = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Populate form when profile loads
  useEffect(() => {
    if (profile) {
      setFullName(profile.full_name || '');
      setEmail(profile.email || '');
    }
  }, [profile]);

  function handleUpdateProfile() {
    const data = { full_name: fullName, email };
    if (newPassword) {
      data.current_password = currentPassword;
      data.new_password = newPassword;
    }
    updateProfile(data);
    setCurrentPassword('');
    setNewPassword('');
  }

  if (loading) return <><Navbar /><PageLoader /></>;

  return (
    <div className="min-h-screen flex flex-col bg-[#F7F6F2]">
      <Navbar />

      <main className="flex-1 flex justify-center py-12 px-4">
        <div className="w-full max-w-2xl flex flex-col gap-6">

          {/* Header */}
          <div>
            <h1
              className="text-[28px] font-bold text-[#111210] mb-1"
              style={{ fontFamily: 'Georgia, serif', letterSpacing: '-0.5px' }}
            >
              Profile
            </h1>
            <p className="text-[14px] text-[#7A7A72]">Manage your account and saved routes.</p>
          </div>

          {/* Success */}
          {successMessage && (
            <div className="flex items-center gap-3 px-4 py-3 bg-[#EAF3DE] border border-[#B8D98A] rounded-xl text-[13px] text-[#3A6B10]">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              {successMessage}
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="flex items-center gap-3 px-4 py-3 bg-[#FCEBEB] border border-[#F5C0B8] rounded-xl text-[13px] text-[#A32D2D]">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              {error}
            </div>
          )}

          {/* Personal info */}
          <SectionCard title="Personal information" description="Update your name and email address.">
            <div className="flex flex-col gap-4">
              <Input
                label="Full name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                disabled={saving}
              />
              <Input
                label="Email address"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={saving}
              />
            </div>
          </SectionCard>

          {/* Change password */}
          <SectionCard title="Change password" description="Leave blank to keep your current password.">
            <div className="flex flex-col gap-4">
              <Input
                label="Current password"
                type="password"
                placeholder="Enter current password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                disabled={saving}
              />
              <Input
                label="New password"
                type="password"
                placeholder="Min. 8 characters"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                disabled={saving}
              />
            </div>
          </SectionCard>

          {/* Save button */}
          <Button
            variant="primary"
            size="lg"
            loading={saving}
            onClick={handleUpdateProfile}
            className="!bg-[#111210] !rounded-xl !text-[15px] !font-semibold !py-3"
          >
            {saving ? 'Saving…' : 'Save changes'}
          </Button>

          {/* Saved routes */}
          <SectionCard
            title="Saved routes"
            description={savedRoutes.length > 0 ? `${savedRoutes.length} route${savedRoutes.length > 1 ? 's' : ''} saved` : 'No saved routes yet.'}
          >
            {savedRoutes.length === 0 ? (
              <p className="text-[13px] text-[#7A7A72]">
                Save a route from the Map page to see it here.
              </p>
            ) : (
              <div className="flex flex-col gap-2">
                {savedRoutes.map((route, i) => (
                  <SavedRouteCard
                    key={route.id || i}
                    route={route}
                    onDelete={deleteRoute}
                  />
                ))}
              </div>
            )}
          </SectionCard>

          {/* Danger zone */}
          <SectionCard title="Danger zone" description="Permanently delete your account and all your data.">
            {!showDeleteConfirm ? (
              <Button
                variant="danger"
                size="md"
                onClick={() => setShowDeleteConfirm(true)}
                className="!rounded-lg"
              >
                Delete account
              </Button>
            ) : (
              <div className="flex flex-col gap-3">
                <p className="text-[13px] text-[#A32D2D] font-medium">
                  Are you sure? This action cannot be undone. All your data will be permanently deleted.
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="danger"
                    size="md"
                    onClick={deleteUser}
                    className="!rounded-lg"
                  >
                    Yes, delete my account
                  </Button>
                  <Button
                    variant="outline"
                    size="md"
                    onClick={() => setShowDeleteConfirm(false)}
                    className="!rounded-lg"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            )}
          </SectionCard>

        </div>
      </main>
    </div>
  );
}