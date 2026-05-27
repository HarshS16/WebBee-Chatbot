import { useState, useRef } from 'react';
import SourceCard from './SourceCard';

/**
 * MessageBubble — Renders a single chat message (user or assistant).
 * 
 * User messages appear on the right with a brand gradient.
 * Assistant messages appear on the left with markdown-like rendering
 * and source citation cards below.
 */
export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const isError = message.isError;
  const [showSources, setShowSources] = useState(false);
  const timeoutRef = useRef(null);

  const handleMouseEnter = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setShowSources(true);
  };

  const handleMouseLeave = () => {
    timeoutRef.current = setTimeout(() => {
      setShowSources(false);
    }, 200);
  };

  return (
    <div
      className={`flex gap-3 animate-slide-up ${isUser ? 'justify-end' : 'justify-start'}`}
      id={`message-${message.id}`}
    >
      {/* Assistant avatar */}
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-lg shadow-brand-500/20 text-white">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
          </svg>
        </div>
      )}

      {/* Message content */}
      <div className={`max-w-[80%] md:max-w-[70%] ${isUser ? 'order-first' : ''}`}>
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-gradient-to-r from-brand-600 to-brand-500 text-white rounded-br-md shadow-lg shadow-brand-500/20'
              : isError
              ? 'glass-card border-red-500/20 bg-red-500/[0.06]'
              : 'glass-card'
          }`}
        >
          {/* Error icon */}
          {isError && (
            <div className="flex items-center gap-2 mb-2 text-red-400 text-xs font-medium">
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
              </svg>
              Error
            </div>
          )}

          {/* Message text */}
          <div className={`text-sm leading-relaxed ${
            isUser
              ? 'text-white'
              : isError
              ? 'text-red-200/90'
              : 'text-surface-850 markdown-content'
          }`}>
            {isUser ? (
              message.content
            ) : (
              <FormattedContent text={message.content} />
            )}
          </div>
        </div>

        {/* Source citations */}
        {!isUser && message.sources?.length > 0 && (
          <div className="relative mt-2 inline-block">
            <button
              className="inline-flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-medium rounded-lg text-surface-600 hover:text-brand-600 bg-surface-100/70 hover:bg-surface-100 border border-surface-200/80 hover:border-brand-500/20 transition-all duration-200"
              onMouseEnter={handleMouseEnter}
              onMouseLeave={handleMouseLeave}
              id={`sources-btn-${message.id}`}
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
              Sources ({message.sources.length})
            </button>

            {showSources && (
              <div
                className="absolute bottom-full left-0 mb-2 w-72 sm:w-96 max-h-72 overflow-y-auto z-50 rounded-2xl bg-white/95 backdrop-blur-xl border border-surface-200 shadow-xl p-2.5 space-y-2 animate-fade-in"
                onMouseEnter={handleMouseEnter}
                onMouseLeave={handleMouseLeave}
                id={`sources-popup-${message.id}`}
              >
                <div className="text-[10px] font-semibold text-surface-500 tracking-wider pb-1.5 border-b border-surface-100 flex items-center justify-between px-1">
                  <span>CITED SOURCES ({message.sources.length})</span>
                </div>
                <div className="space-y-1.5 pt-0.5">
                  {message.sources.map((source, idx) => (
                    <SourceCard
                      key={idx}
                      title={source.title}
                      url={source.url}
                      snippet={source.snippet}
                      compact={true}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Timestamp */}
        <p className={`text-[10px] text-surface-600 mt-1 ${isUser ? 'text-right' : 'text-left ml-1'}`}>
          {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>

      {/* User avatar */}
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-gradient-to-br from-surface-600 to-surface-700 flex items-center justify-center">
          <svg className="w-4 h-4 text-surface-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
          </svg>
        </div>
      )}
    </div>
  );
}


/**
 * Simple markdown-like formatter for assistant responses.
 * Handles bold, links, lists, and line breaks.
 */
function FormattedContent({ text }) {
  if (!text) return null;

  // Split into paragraphs
  const paragraphs = text.split('\n\n');

  return (
    <div className="markdown-content">
      {paragraphs.map((paragraph, pIdx) => {
        // Check if it's a list
        const lines = paragraph.split('\n');
        const isList = lines.every(
          (line) => line.trim().startsWith('- ') || line.trim().startsWith('• ') || /^\d+\.\s/.test(line.trim()) || line.trim() === ''
        );

        if (isList) {
          const isOrdered = lines.some((l) => /^\d+\.\s/.test(l.trim()));
          const Tag = isOrdered ? 'ol' : 'ul';
          return (
            <Tag key={pIdx}>
              {lines
                .filter((l) => l.trim())
                .map((line, lIdx) => (
                  <li key={lIdx}>
                    <InlineFormat text={line.replace(/^[-•]\s|^\d+\.\s/, '')} />
                  </li>
                ))}
            </Tag>
          );
        }

        // Check for heading (lines starting with **)
        if (paragraph.trim().startsWith('**') && paragraph.trim().endsWith('**')) {
          return (
            <h3 key={pIdx}>
              {paragraph.trim().replace(/^\*\*|\*\*$/g, '')}
            </h3>
          );
        }

        // Regular paragraph
        return (
          <p key={pIdx}>
            {lines.map((line, lIdx) => (
              <span key={lIdx}>
                <InlineFormat text={line} />
                {lIdx < lines.length - 1 && <br />}
              </span>
            ))}
          </p>
        );
      })}
    </div>
  );
}


/**
 * Inline formatting: bold, links, code
 */
function InlineFormat({ text }) {
  if (!text) return null;

  // Process bold (**text**), links [text](url), and inline code (`code`)
  const parts = [];
  let remaining = text;
  let key = 0;

  while (remaining) {
    // Bold
    const boldMatch = remaining.match(/\*\*(.+?)\*\*/);
    // Link
    const linkMatch = remaining.match(/\[([^\]]+)\]\(([^)]+)\)/);
    // Code
    const codeMatch = remaining.match(/`([^`]+)`/);

    // Find earliest match
    const matches = [
      boldMatch && { type: 'bold', match: boldMatch },
      linkMatch && { type: 'link', match: linkMatch },
      codeMatch && { type: 'code', match: codeMatch },
    ].filter(Boolean);

    if (matches.length === 0) {
      parts.push(<span key={key++}>{remaining}</span>);
      break;
    }

    const earliest = matches.reduce((a, b) =>
      a.match.index < b.match.index ? a : b
    );

    // Text before match
    if (earliest.match.index > 0) {
      parts.push(<span key={key++}>{remaining.slice(0, earliest.match.index)}</span>);
    }

    // The match itself
    switch (earliest.type) {
      case 'bold':
        parts.push(<strong key={key++}>{earliest.match[1]}</strong>);
        break;
      case 'link':
        parts.push(
          <a key={key++} href={earliest.match[2]} target="_blank" rel="noopener noreferrer">
            {earliest.match[1]}
          </a>
        );
        break;
      case 'code':
        parts.push(<code key={key++}>{earliest.match[1]}</code>);
        break;
    }

    remaining = remaining.slice(earliest.match.index + earliest.match[0].length);
  }

  return <>{parts}</>;
}
