/**
 * Results page.
 *
 * Reads query and model from URL search params:
 *   /results?q=<query>&model=<semantic|tfidf>
 *
 * Features:
 *   - Re-runs search when URL params change
 *   - Inline SearchBar for refining the query
 *   - Result count + retrieval time metadata
 *   - Model badge (SBERT vs TF-IDF)
 *   - Loading skeleton cards
 *   - Empty state + error state
 *   - ResultCard list with rank + similarity score
 */

import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import SearchBar  from "../components/SearchBar";
import ResultCard from "../components/ResultCard";
import api        from "../api/axios";

export default function Results() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const query = searchParams.get("q")     || "";
  const model = searchParams.get("model") || "semantic";

  // ── State ──────────────────────────────────────────────────────────────────
  const [results, setResults]   = useState([]);
  const [meta, setMeta]         = useState({ retrieval_time_ms: 0 });
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");

  // ── Fetch results when query / model changes ───────────────────────────────
  useEffect(() => {
    if (!query.trim()) return;
    fetchResults(query, model);
  }, [query, model]);

  const fetchResults = async (q, m) => {
    setLoading(true);
    setError("");
    setResults([]);

    try {
      const endpoint = m === "tfidf"
        ? "/search/tfidf"
        : "/search/semantic";

      const { data } = await api.post(endpoint, {
        query: q,
        top_k: 10,
      });

      setResults(data.results || []);
      setMeta({ retrieval_time_ms: data.retrieval_time_ms ?? 0 });

    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : "Search failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  // ── Handle new search from inline SearchBar ────────────────────────────────
  const handleSearch = (newQuery, newModel) => {
    setSearchParams({ q: newQuery, model: newModel });
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">

      {/* ── Inline Search Bar ────────────────────────────────────────── */}
      <SearchBar
        initialQuery={query}
        initialModel={model}
        onSearch={handleSearch}
        className="mb-8"
      />

      {/* ── Results Metadata ─────────────────────────────────────────── */}
      {!loading && results.length > 0 && (
        <div className="flex items-center justify-between mb-5 flex-wrap gap-2">

          {/* Result count + query */}
          <p className="text-sm text-gray-500">
            <span className="font-semibold text-gray-800">
              {results.length}
            </span>{" "}
            result{results.length !== 1 ? "s" : ""} for{" "}
            <span className="font-semibold text-gray-800">
              &ldquo;{query}&rdquo;
            </span>
          </p>

          {/* Model + retrieval time */}
          <div className="flex items-center gap-3">
            <span className={`badge ${
              model === "tfidf"
                ? "bg-amber-100 text-amber-700"
                : "bg-blue-100 text-blue-700"
            }`}>
              {model === "tfidf" ? "TF-IDF" : "SBERT Semantic"}
            </span>
            <span className="text-xs text-gray-400 flex items-center gap-1">
              <svg
                className="w-3.5 h-3.5 text-gray-300"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              {meta.retrieval_time_ms.toFixed(1)} ms
            </span>
          </div>
        </div>
      )}

      {/* ── Loading Skeletons ─────────────────────────────────────────── */}
      {loading && (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className="skeleton h-28 rounded-xl"
              style={{ opacity: 1 - i * 0.15 }}
            />
          ))}
          <p className="text-center text-sm text-gray-400 mt-4">
            Searching with {model === "tfidf" ? "TF-IDF" : "SBERT"}...
          </p>
        </div>
      )}

      {/* ── Error State ──────────────────────────────────────────────── */}
      {!loading && error && (
        <div className="alert-error">
          <div className="flex items-start gap-2">
            <span className="text-lg">⚠️</span>
            <div>
              <p className="font-semibold">Search failed</p>
              <p className="mt-0.5">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* ── Empty State ──────────────────────────────────────────────── */}
      {!loading && !error && results.length === 0 && query && (
        <div className="card text-center py-14">
          <div className="text-5xl mb-4">🔎</div>
          <h3 className="text-lg font-semibold text-gray-700 mb-2">
            No results found
          </h3>
          <p className="text-sm text-gray-400 mb-6 max-w-sm mx-auto">
            No articles matched &ldquo;{query}&rdquo;.
            Try a different query or switch search models.
          </p>
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={() =>
                handleSearch(query, model === "tfidf" ? "semantic" : "tfidf")
              }
              className="btn-secondary text-sm"
            >
              Try {model === "tfidf" ? "SBERT" : "TF-IDF"} instead
            </button>
            <button
              onClick={() => navigate("/search")}
              className="btn-primary text-sm"
            >
              New search
            </button>
          </div>
        </div>
      )}

      {/* ── No query yet ─────────────────────────────────────────────── */}
      {!loading && !error && !query && (
        <div className="card text-center py-14">
          <div className="text-5xl mb-4">🔍</div>
          <p className="text-gray-500">
            Enter a search query above to get started.
          </p>
        </div>
      )}

      {/* ── Result Cards ─────────────────────────────────────────────── */}
      {!loading && !error && results.length > 0 && (
        <div className="space-y-4">
          {results.map((result, index) => (
            <ResultCard
              key={result.article.id}
              article={result.article}
              similarityScore={result.similarity_score}
              rank={index + 1}
            />
          ))}

          {/* Footer note */}
          <p className="text-center text-xs text-gray-400 pt-4">
            Showing top {results.length} results •{" "}
            {model === "tfidf" ? "TF-IDF keyword search" : "SBERT semantic search"} •{" "}
            {meta.retrieval_time_ms.toFixed(1)} ms retrieval time
          </p>
        </div>
      )}

    </div>
  );
}