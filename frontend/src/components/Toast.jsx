// UrbanFlow — Toast.jsx
// Lightweight auto-dismissing toast for transient feedback.

import { useEffect, useState } from 'react';

export function Toast({ message, onDismiss, duration = 4000 }) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
      setTimeout(onDismiss, 300); // wait for fade out
    }, duration);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-50 transition-all duration-300 ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'}`}>
      <div className="flex items-center gap-2.5 px-4 py-3 bg-[#111210] text-white text-[13px] font-medium rounded-xl shadow-lg">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#86EFAC" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
        </svg>
        {message}
      </div>
    </div>
  );
}