import { useState, useCallback, useEffect, useRef } from 'react';
import { sendMessage } from '../api/chatApi';

const SESSION_STORAGE_KEY = 'webbee_chat_history';

/**
 * Custom hook for managing chat state and API interactions.
 */
export function useChat() {
  const [messages, setMessages] = useState(() => {
    // Restore chat history from session storage
    try {
      const saved = sessionStorage.getItem(SESSION_STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const messageIdCounter = useRef(Date.now());

  // Persist messages to session storage
  useEffect(() => {
    try {
      sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(messages));
    } catch {
      // Session storage might be full or unavailable
    }
  }, [messages]);

  const generateId = useCallback(() => {
    messageIdCounter.current += 1;
    return `msg_${messageIdCounter.current}`;
  }, []);

  const send = useCallback(async (text) => {
    if (!text.trim() || isLoading) return;

    setError(null);

    // Add user message
    const userMessage = {
      id: generateId(),
      role: 'user',
      content: text.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await sendMessage(text.trim());

      // Add assistant message
      const assistantMessage = {
        id: generateId(),
        role: 'assistant',
        content: response.answer,
        sources: response.sources || [],
        foundContext: response.found_context,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Chat error:', err);

      let errorMessage = 'Something went wrong. Please try again.';

      if (err.response) {
        if (err.response.status === 429) {
          errorMessage = 'You\'re sending messages too quickly. Please wait a moment and try again.';
        } else if (err.response.data?.detail) {
          errorMessage = err.response.data.detail;
        } else if (err.response.data?.error) {
          errorMessage = err.response.data.error;
        }
      } else if (err.code === 'ECONNABORTED') {
        errorMessage = 'The request timed out. Please try again.';
      } else if (!navigator.onLine) {
        errorMessage = 'You appear to be offline. Please check your connection.';
      }

      setError(errorMessage);

      // Add error message as assistant response
      const errorMsg = {
        id: generateId(),
        role: 'assistant',
        content: errorMessage,
        sources: [],
        foundContext: false,
        isError: true,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, generateId]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
    sessionStorage.removeItem(SESSION_STORAGE_KEY);
  }, []);

  return {
    messages,
    isLoading,
    error,
    send,
    clearChat,
  };
}
