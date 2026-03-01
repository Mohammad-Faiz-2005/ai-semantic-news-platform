/**
 * Home page.
 *
 * Sections:
 *   1. Hero — headline, subtitle, SearchBar
 *   2. Stats row — articles indexed, model, vector search
 *   3. Recommendations grid — personalised via GET /recommendations
 *
 * On mount:
 *   Fetches top-6 personalised recommendations.
 *   Shows skeleton cards while loading.
 *   Shows friendly empty state if no history yet.
 */

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import SearchBar          from "../components/SearchBar";
import RecommendationCard from "../components/RecommendationCard";
import { useAuth }        from "../context/AuthContext";
import api                from "../api/axios";

export default function Home() {
  const { user }   = useAuth();
  const navigate   = useNavigate();

  // ── State ──────────────────────────────────────────────────────────────────
  const [recommendations, setRecommendations] = useState([]);
  const [loadingRecs, setLoadingRecs]         = useState(true);
  const [recsError, setRecsError]             = useState("");

  // ── Fetch recommendations on mount ────────────────────────────────────────
  useEffect(() => {
    api.get("/recommendations?top_k=6")
      .then((res) => {
        setRecommendations(res.data.recommendations || []);
      })
      .catch(() => {
        setRecsError("Could not load recommendations.");
      })
      .finally(() => setLoadingRecs(false));
  }, []);

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">

      {/* ── Hero Section ────────────────────────────────────────────── */}
      <div className="text-center mb-12">
        {/* Greeting */}
        {user?.name && (
          <p className="text-sm text-blue-600 font-medium mb-2">
            👋 Welcome back, {user.name.split(" ")[0]}
          </p>
        )}

        <h1 className="text-4xl sm:text-5xl font-extrabold text-gray-900
                       leading-tight mb-4">
          AI-Powered{" "}
          <span className="text-blue-600">News Search</span>
        </h1>

        <p className="text-gray-500 text-lg mb-8 max-w-xl mx-auto leading-relaxed">
          Semantic search using{" "}
          <span className="font-semibold text-gray-700">Sentence-BERT</span>{" "}
          and{" "}
          <span className="font-semibold text-gray-700">FAISS</span>
          {" "}— find articles by meaning, not just keywords.
        </p>

        {/* Search bar */}
        <SearchBar
          onSearch={(q, m) =>
            navigate(`/results?q=${encodeURIComponent(q)}&model=${m}`)
          }
          className="max-w-2xl mx-auto"
          autoFocus
        />
      </div>

      {/* ── Stats Row ───────────────────────────────────────────────── */}
      <div className="grid grid-cols-3 gap-4 mb-12">
        {[
          {
            label: "Articles Indexed",
            value: "12+",
            icon:  "📰",
            sub:   "in FAISS",
          },
          {
            label: "Embedding Model",
            value: "SBERT",
            icon:  "🤖",
            sub:   "all-MiniLM-L6-v2",
          },
          {
            label: "Vector Search",
            value: "FAISS",
            icon:  "⚡",
            sub:   "IndexFlatIP",
          },
        ].map((stat) => (
          <div key={stat.label} className="card text-center">
            <div className="text-2xl mb-2">{stat.icon}</div>
            <div className="text-xl font-bold text-blue-600 leading-none">
              {stat.value}
            </div>
            <div className="text-xs font-medium text-gray-700 mt-1">
              {stat.label}
            </div>
            <div className="text-xs text-gray-400 mt-0.5">
              {stat.sub}
            </div>
          </div>
        ))}
      </div>

      {/* ── How it works ────────────────────────────────────────────── */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600
                      rounded-2xl p-6 mb-12 text-white">
        <h2 className="font-bold text-lg mb-3">
          How semantic search works
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            {
              step: "01",
              title: "Query Embedding",
              desc:  "Your query is encoded into a 384-dim vector using Sentence-BERT.",
            },
            {
              step: "02",
              title: "FAISS Search",
              desc:  "FAISS computes cosine similarity against all article embeddings.",
            },
            {
              step: "03",
              title: "Ranked Results",
              desc:  "Top-K semantically similar articles are returned with scores.",
            },
          ].map((item) => (
            <div key={item.step} className="flex gap-3">
              <span className="text-3xl font-black text-blue-300 leading-none flex-shrink-0">
                {item.step}
              </span>
              <div>
                <p className="font-semibold text-sm">{item.title}</p>
                <p className="text-blue-100 text-xs mt-0.5 leading-relaxed">
                  {item.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Recommendations Section ──────────────────────────────────── */}
      <div>
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-xl font-bold text-gray-900">
              Recommended for you
            </h2>
            <p className="text-sm text-gray-400 mt-0.5">
              Based on your search history
            </p>
          </div>
          <button
            onClick={() => navigate("/search")}
            className="text-sm text-blue-600 hover:text-blue-700
                       font-medium hover:underline"
          >
            Explore all →
          </button>
        </div>

        {/* Loading skeletons */}
        {loadingRecs && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <div
                key={i}
                className="skeleton h-40 rounded-xl"
              />
            ))}
          </div>
        )}

        {/* Error state */}
        {!loadingRecs && recsError && (
          <div className="alert-error">
            {recsError}
          </div>
        )}

        {/* Recommendations grid */}
        {!loadingRecs && !recsError && recommendations.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {recommendations.map((rec) => (
              <RecommendationCard
                key={rec.article.id}
                article={rec.article}
                similarityScore={rec.similarity_score}
              />
            ))}
          </div>
        )}

        {/* Empty state — no history yet */}
        {!loadingRecs && !recsError && recommendations.length === 0 && (
          <div className="card text-center py-12">
            <div className="text-4xl mb-3">🔍</div>
            <p className="text-gray-600 font-medium mb-1">
              No recommendations yet
            </p>
            <p className="text-sm text-gray-400 mb-5">
              Search for some articles to get personalised recommendations.
            </p>
            <button
              onClick={() => navigate("/search")}
              className="btn-primary text-sm mx-auto"
            >
              Start Searching
            </button>
          </div>
        )}
      </div>
    </div>
  );
}