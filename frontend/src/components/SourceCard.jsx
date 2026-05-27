/**
 * SourceCard — Displays a clickable source citation card.
 * 
 * Shows the page title, a text snippet, and links to the source URL.
 * Features glassmorphism styling with hover effects.
 */
export default function SourceCard({ title, url, snippet, compact = false }) {
  // Clean up the title
  const displayTitle = title
    ?.replace(/\s*[-|—]\s*WebBee.*$/i, '')
    ?.trim() || 'Source';

  // Truncate snippet
  const displaySnippet = snippet?.length > 120
    ? snippet.slice(0, 120) + '...'
    : snippet || '';

  // Extract domain path for display
  let displayPath = '';
  try {
    const urlObj = new URL(url);
    displayPath = urlObj.pathname === '/' ? urlObj.hostname : urlObj.pathname;
  } catch {
    displayPath = url;
  }

  if (compact) {
    return (
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="group block p-2 rounded-xl bg-surface-100/40 hover:bg-surface-100 border border-surface-200/50 hover:border-surface-300/80 transition-all duration-200 no-underline"
        id={`source-card-compact-${title?.replace(/\s+/g, '-').toLowerCase().slice(0, 20)}`}
      >
        <div className="flex items-start gap-2.5">
          {/* Icon */}
          <div className="flex-shrink-0 w-6 h-6 rounded-md bg-brand-500/10 flex items-center justify-center mt-0.5">
            <svg
              className="w-3.5 h-3.5 text-brand-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
              />
            </svg>
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2">
              <h4 className="text-xs font-semibold text-surface-800 group-hover:text-brand-600 transition-colors truncate">
                {displayTitle}
              </h4>
              <span className="text-[10px] text-surface-500 truncate max-w-[120px]">{displayPath}</span>
            </div>
            
            {displaySnippet && (
              <p className="text-[11px] text-surface-500 mt-0.5 line-clamp-1 leading-normal">
                {displaySnippet}
              </p>
            )}
          </div>

          {/* Arrow */}
          <svg
            className="w-3 h-3 text-surface-400 group-hover:text-brand-600 transition-all group-hover:translate-x-0.5 flex-shrink-0 mt-1"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </a>
    );
  }

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="group block glass-card-hover p-3 no-underline"
      id={`source-card-${title?.replace(/\s+/g, '-').toLowerCase().slice(0, 20)}`}
    >
      <div className="flex items-start gap-2.5">
        {/* Icon */}
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-brand-500/10 flex items-center justify-center mt-0.5">
          <svg
            className="w-4 h-4 text-brand-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
            />
          </svg>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-surface-850 group-hover:text-brand-600 transition-colors truncate">
            {displayTitle}
          </h4>
          
          {displaySnippet && (
            <p className="text-xs text-surface-600 mt-1 line-clamp-2 leading-relaxed">
              {displaySnippet}
            </p>
          )}
          
          <div className="flex items-center gap-1 mt-1.5">
            <svg
              className="w-3 h-3 text-surface-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
              />
            </svg>
            <span className="text-xs text-surface-500 truncate">{displayPath}</span>
          </div>
        </div>

        {/* Arrow */}
        <svg
          className="w-4 h-4 text-surface-400 group-hover:text-brand-600 transition-all group-hover:translate-x-0.5 flex-shrink-0 mt-1"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </a>
  );
}
