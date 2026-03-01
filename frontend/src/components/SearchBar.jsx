/**
 * SearchBar — Reusable search input with model selector.
 *
 * Props:
 *   initialQuery  (string)   — Pre-filled query value. Default: ""
 *   initialModel  (string)   — Pre-selected model. Default: "semantic"
 *   onSearch      (function) — Callback(query, model) on form submit.
 *                              If not provided, navigates to /results?q=...
 *   className     (string)   — Extra CSS classes for the wrapper. Default: ""
 *   placeholder   (string)   — Input placeholder text.
 *   autoFocus     (boolean)  — Auto-focus the input on mount. Default: false
 *
 * Model options:
 *   "semantic" → SBERT + FAISS (primary)
 *   "tfidf"    → TF-IDF baseline (comparison)
 *
 * Usage:
 *   // Navigate to results page on search
 *   <SearchBar />
 *
 *   // Custom handler (e.g. results page re-search)
 *   <SearchBar
 *     initialQuery={query}
 *     initialModel={model}
 *     onSearch={(q, m) => setSearchParams({ q, model: m })}
 *   />
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function SearchBar({
  initialQuery  = "",
  initialModel  = "semantic",
  onSearch      = null,
  className     = "",
  placeholder   = "Search news articles semantically...",
  autoFocus     = false,
}) {
  const [query, setQuery] = useState(initialQuery);
  const [model, setModel] = useState(initialModel);
  const navigate = useNavigate();

  // ── Submit Handler ─────────────────────────────────────────────────────────

  const handleSubmit = (e) => {
    e.preventDefault();

    const trimmed = query.trim();
    if (!trimmed) return;

    if (onSearch) {
      // Use custom callback if provided
      onSearch(trimmed, model);
    } else {
      // Default: navigate to results page with query params
      navigate(
        `/results?q=${encodeURIComponent(trimmed)}&model=${model}`
      );
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <form
      onSubmit={handleSubmit}
      className={`flex gap-2 ${className}`}
      role="search"
    >
      {/* ── Search Input ──────────────────────────────────────────────── */}
      <div className="flex-1 relative">
        {/* Search icon */}
        <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
          <svg
            className="w-5 h-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>

        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          autoFocus={autoFocus}
          autoComplete="off"
          spellCheck="false"
          aria-label="Search query"
          className="input-field pl-10 pr-4"
        />

        {/* Clear button — shown when query is non-empty */}
        {query && (
          <button
            type="button"
            onClick={() => setQuery("")}
            className="absolute inset-y-0 right-3 flex items-center
                       text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Clear search"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* ── Model Selector ────────────────────────────────────────────── */}
      <select
        value={model}
        onChange={(e) => setModel(e.target.value)}
        aria-label="Search model"
        className="flex-shrink-0
                   border border-gray-300 rounded-lg
                   px-3 py-2.5
                   text-sm text-gray-700
                   bg-white
                   focus:outline-none focus:ring-2 focus:ring-blue-500
                   transition duration-150
                   cursor-pointer"
      >
        <option value="semantic">🤖 SBERT (Semantic)</option>
        <option value="tfidf">📊 TF-IDF (Baseline)</option>
      </select>

      {/* ── Submit Button ─────────────────────────────────────────────── */}
      <button
        type="submit"
        disabled={!query.trim()}
        className="btn-primary flex-shrink-0 whitespace-nowrap"
        aria-label="Submit search"
      >
        Search
      </button>
    </form>
  );
}