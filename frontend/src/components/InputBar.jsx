import { useState, useRef, useEffect } from 'react';

/**
 * InputBar — Chat input with send button.
 * 
 * Features:
 * - Auto-resizing textarea
 * - Submit on Enter (Shift+Enter for new line)
 * - Disabled state while loading
 * - Character count
 */
export default function InputBar({ onSend, isLoading }) {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);
  const MAX_LENGTH = 2000;

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [text]);

  // Focus on mount
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  }, []);

  const handleSubmit = () => {
    if (!text.trim() || isLoading) return;
    onSend(text.trim());
    setText('');
    // Reset height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="p-4 border-t border-surface-200/60">
      <div className="max-w-3xl mx-auto">
        <div className={`
          flex items-end gap-2 glass-card p-2 transition-all duration-200
          ${text.trim() ? 'border-brand-500/40 glow-brand' : ''}
        `}>
          {/* Textarea */}
          <textarea
            ref={textareaRef}
            id="chat-input"
            value={text}
            onChange={(e) => setText(e.target.value.slice(0, MAX_LENGTH))}
            onKeyDown={handleKeyDown}
            placeholder={isLoading ? 'Waiting for response...' : 'Ask about WebBee Global...'}
            disabled={isLoading}
            rows={1}
            className="
              flex-1 bg-transparent text-surface-900 text-sm placeholder-surface-400
              resize-none outline-none border-none px-3 py-2
              disabled:opacity-50 disabled:cursor-not-allowed
              leading-relaxed
            "
          />

          {/* Send button */}
          <button
            id="send-button"
            onClick={handleSubmit}
            disabled={!text.trim() || isLoading}
            className={`
              flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center
              transition-all duration-200
              ${text.trim() && !isLoading
                ? 'bg-gradient-to-r from-brand-600 to-brand-500 text-white shadow-lg shadow-brand-500/25 hover:shadow-brand-500/40 hover:scale-105 active:scale-95'
                : 'bg-surface-200/80 text-surface-400 cursor-not-allowed'
              }
            `}
          >
            {isLoading ? (
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
              </svg>
            )}
          </button>
        </div>

        {/* Footer hints */}
        <div className="flex items-center justify-between mt-1.5 px-1">
          <p className="text-[10px] text-surface-500">
            Press Enter to send · Shift+Enter for new line
          </p>
          {text.length > MAX_LENGTH * 0.8 && (
            <p className={`text-[10px] ${text.length >= MAX_LENGTH ? 'text-red-400' : 'text-surface-500'}`}>
              {text.length}/{MAX_LENGTH}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
