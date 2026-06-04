// UrbanFlow — ChatPanel.jsx
// Sliding RAG chat panel — opens from the right on desktop, full-screen on mobile.

import { useState, useRef, useEffect } from 'react';
import { useAuthContext } from '../../context/AuthContext';
import apiClient from '../../lib/apiClient';

export default function ChatPanel({ open, onClose }) {
  const { user } = useAuthContext();
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading]   = useState(false);
  const [location, setLocation] = useState({ latitude: 3.8667, longitude: 11.5167 });
  const bottomRef = useRef(null);

  // Get user's real GPS location
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setLocation({
          latitude:  pos.coords.latitude,
          longitude: pos.coords.longitude,
        }),
        () => {}
      );
    }
  }, []);

  // Auto-scroll to latest message
  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, open]);

  // Load history when panel opens
  useEffect(() => {
    if (!open || !user?.id) return;
    apiClient.get(`/chat/history/${user.id}`)
      .then((res) => {
        const items = res.data ?? res;
        if (!Array.isArray(items)) return;
        const rebuilt = items.flatMap((item) => [
          { role: 'user',      text: item.question },
          { role: 'assistant', text: item.answer   },
        ]);
        setMessages(rebuilt);
      })
      .catch(() => {});
  }, [open, user?.id]);

  async function sendMessage() {
    if (!question.trim() || loading) return;
    const userMsg = { role: 'user', text: question.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setQuestion('');
    setLoading(true);

    try {
      const res = await apiClient.post('/chat', {
        question:  userMsg.text,
        latitude:  location.latitude,
        longitude: location.longitude,
      });
      const data = res.data ?? res;
      setMessages((prev) => [...prev, { role: 'assistant', text: data.answer }]);
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', text: 'Sorry, something went wrong. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  if (!open) return null;

  return (
    <>
      {/* ── Mobile: full-screen overlay ── */}
      <div
        className="
          md:hidden
          fixed inset-0 z-50
          flex flex-col bg-white
        "
      >
        <ChatPanelContent
          messages={messages}
          loading={loading}
          question={question}
          setQuestion={setQuestion}
          sendMessage={sendMessage}
          handleKeyDown={handleKeyDown}
          onClose={onClose}
          bottomRef={bottomRef}
        />
      </div>

      {/* ── Desktop: side panel (original behaviour) ── */}
      <div
        className="
          hidden md:flex flex-col
          bg-white border-l border-[#E2E1DB] h-full
        "
        style={{ width: '360px', minWidth: '360px' }}
      >
        <ChatPanelContent
          messages={messages}
          loading={loading}
          question={question}
          setQuestion={setQuestion}
          sendMessage={sendMessage}
          handleKeyDown={handleKeyDown}
          onClose={onClose}
          bottomRef={bottomRef}
        />
      </div>
    </>
  );
}

// ─── Shared panel content ─────────────────────────────────────────────────────

function ChatPanelContent({ messages, loading, question, setQuestion, sendMessage, handleKeyDown, onClose, bottomRef }) {
  return (
    <>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#E2E1DB] flex-shrink-0">
        <div className="flex items-center gap-2">
          <svg width="18" height="18" viewBox="0 0 28 28" fill="none">
            <path d="M14 2C14 2 15.5 9.5 20 14C15.5 18.5 14 26 14 26C14 26 12.5 18.5 8 14C12.5 9.5 14 2 14 2Z" fill="url(#gemini_grad)"/>
            <defs>
              <linearGradient id="gemini_grad" x1="8" y1="2" x2="20" y2="26" gradientUnits="userSpaceOnUse">
                <stop stopColor="#4285F4"/>
                <stop offset="0.5" stopColor="#9B72CB"/>
                <stop offset="1" stopColor="#D96570"/>
              </linearGradient>
            </defs>
          </svg>
          <span className="text-[14px] font-semibold text-[#111210]">UrbanFlow AI</span>
        </div>
        <button
          onClick={onClose}
          className="text-[#7A7A72] hover:text-[#111210] transition-colors p-1 rounded-full hover:bg-[#F5F5F3]"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center px-4 py-12">
            <svg width="32" height="32" viewBox="0 0 28 28" fill="none" className="mb-3">
              <path d="M14 2C14 2 15.5 9.5 20 14C15.5 18.5 14 26 14 26C14 26 12.5 18.5 8 14C12.5 9.5 14 2 14 2Z" fill="url(#gemini_grad2)"/>
              <defs>
                <linearGradient id="gemini_grad2" x1="8" y1="2" x2="20" y2="26" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#4285F4"/>
                  <stop offset="0.5" stopColor="#9B72CB"/>
                  <stop offset="1" stopColor="#D96570"/>
                </linearGradient>
              </defs>
            </svg>
            <p className="text-[13px] font-medium text-[#111210]">Ask me anything about traffic</p>
            <p className="text-[12px] text-[#7A7A72] mt-1">I can check incidents, congestion, and routes near you.</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[80%] px-3 py-2 rounded-2xl text-[13px] leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-[#2563EB] text-white rounded-br-sm'
                  : 'bg-[#F5F5F3] text-[#111210] rounded-bl-sm'
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-[#F5F5F3] px-3 py-2 rounded-2xl rounded-bl-sm">
              <div className="flex gap-1 items-center h-4">
                <span className="w-1.5 h-1.5 bg-[#9B72CB] rounded-full animate-bounce" style={{ animationDelay: '0ms' }}/>
                <span className="w-1.5 h-1.5 bg-[#9B72CB] rounded-full animate-bounce" style={{ animationDelay: '150ms' }}/>
                <span className="w-1.5 h-1.5 bg-[#9B72CB] rounded-full animate-bounce" style={{ animationDelay: '300ms' }}/>
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-3 border-t border-[#E2E1DB] flex-shrink-0">
        <div className="flex items-end gap-2 bg-[#F5F5F3] rounded-2xl px-3 py-2">
          <textarea
            rows={1}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about traffic, incidents..."
            className="flex-1 bg-transparent text-[13px] text-[#111210] placeholder-[#7A7A72] resize-none outline-none leading-relaxed"
            style={{ maxHeight: '80px' }}
          />
          <button
            onClick={sendMessage}
            disabled={!question.trim() || loading}
            className="flex-shrink-0 w-7 h-7 rounded-full bg-[#2563EB] disabled:bg-[#E2E1DB] flex items-center justify-center transition-colors"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"/>
              <polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
          </button>
        </div>
        <p className="text-[10px] text-[#7A7A72] text-center mt-2">Press Enter to send · Shift+Enter for new line</p>
      </div>
    </>
  );
}