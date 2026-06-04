// Controls the open/close state of the chat panel globally.
// Any component can call useChatPanel() to open, close, or toggle it.


import { createContext, useContext, useState } from 'react';

const ChatPanelContext = createContext();

export function ChatPanelProvider({ children }) {
  const [isOpen, setIsOpen] = useState(false);
  const open   = () => setIsOpen(true);
  const close  = () => setIsOpen(false);
  const toggle = () => setIsOpen((prev) => !prev);
  return (
    <ChatPanelContext.Provider value={{ isOpen, open, close, toggle }}>
      {children}
    </ChatPanelContext.Provider>
  );
}

export function useChatPanel() {
  return useContext(ChatPanelContext);
}