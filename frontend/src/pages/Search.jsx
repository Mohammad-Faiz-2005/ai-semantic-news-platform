/**
 * Search page.
 *
 * A dedicated search page with:
 *   - Large centered SearchBar
 *   - Sample query chips for quick exploration
 *   - Explanation panel describing how semantic search works
 *   - Model comparison tip
 *
 * On submit, navigates to /results?q=...&model=...
 */

import { useNavigate } from "react-router-dom";
import SearchBar from "../components/SearchBar";

// ── Sample queries ────────────────────────────────────────────────────────────

const SAMPLE_QUERIES = [
  "artificial intelligence breakthroughs",
  "climate change and renewable energy",
  "space exploration missions",
  "global economy and inflation",
  "cancer treatment research",
  "electric vehicles adoption",
  "quantum computing advances",
  "football championship results",
];

export default function Search() {
  const navigate = useNavigate();

  const handleSearch = (query, model) => {
    navigate(`/results?q=${encodeURIComponent(query)}&model=${model}`);
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-16">

      {/* ── Header ──────────────────────────────────────────────────── */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 bg-blue-50 text-blue-600
                        text-xs font-semibold px-3 py-1.5 rounded-full mb-4">
          <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
              clipRule="evenodd"
            />
          </svg>
          Semantic Search
        </div>

        <h1 className="text-3xl font-bold text-gray-900 mb-3">
          Search Articles
        </h1>
        <p className="text-gray-500 leading-relaxed">
          Find articles by <strong>meaning</strong>, not just exact keyword matches.
          SBERT understands context and semantics.
        </p>
      </div>

      {/* ── Search Bar ──────────────────────────────────────────────── */}
      <SearchBar
        onSearch={handleSearch}
        className="mb-10"
        placeholder="e.g. advances in renewable energy..."
        autoFocus
      />

      {/* ── Sample Queries ──────────────────────────────────────────── */}
      <div className="mb-10">
        <h3 className="text-xs font-semibold text-gray-400 uppercase
                       tracking-widest mb-3">
          Try these searches
        </h3>
        <div className="flex flex-wrap gap-2">
          {SAMPLE_QUERIES.map((q) => (
            <button
              key={q}
              onClick={() => handleSearch(q, "semantic")}
              className="btn-secondary text-sm py-1.5 px-3"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* ── How It Works Panel ──────────────────────────────────────── */}
      <div className="bg-blue-50 border border-blue-200 rounded-2xl p-6 mb-6">
        <h4 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
          <span>🤖</span>
          How SBERT semantic search works
        </h4>
        <ol className="text-sm text-blue-800 space-y-2 list-none">
          {[
            "Your query is converted to a 384-dimensional vector using Sentence-BERT (all-MiniLM-L6-v2).",
            "The vector is L2-normalised so cosine similarity equals dot product.",
            "FAISS IndexFlatIP performs exact cosine similarity search over all indexed article embeddings.",
            "Top-K most semantically similar articles are returned with similarity scores.",
            "Your search is logged to build your personalised recommendation profile.",
          ].map((step, i) => (
            <li key={i} className="flex gap-3">
              <span className="flex-shrink-0 w-5 h-5 bg-blue-200 text-blue-800
                               rounded-full text-xs font-bold
                               flex items-center justify-center mt-0.5">
                {i + 1}
              </span>
              <span className="leading-relaxed">{step}</span>
            </li>
          ))}
        </ol>
      </div>

      {/* ── Model Comparison Tip ────────────────────────────────────── */}
      <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5">
        <h4 className="font-semibold text-amber-900 mb-2 flex items-center gap-2">
          <span>💡</span>
          Compare search models
        </h4>
        <p className="text-sm text-amber-800 leading-relaxed">
          Use the model selector in the search bar to switch between{" "}
          <strong>SBERT (semantic)</strong> and{" "}
          <strong>TF-IDF (keyword-based)</strong> search.
          Compare results on the same query to see the difference.
          View detailed metrics on the{" "}
          <button
            onClick={() => navigate("/dashboard")}
            className="underline font-semibold hover:text-amber-900"
          >
            Dashboard
          </button>
          .
        </p>
      </div>

    </div>
  );
}