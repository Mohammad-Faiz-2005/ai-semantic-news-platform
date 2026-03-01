/**
 * RecommendationCard — Compact article card for the recommendations grid.
 *
 * Props:
 *   article         (object) — Article data from API response
 *   similarityScore (number) — Cosine similarity score (0.0 - 1.0)
 *
 * Features:
 *   - Domain-coloured card background
 *   - Match percentage badge (hidden when score is 0 — fallback articles)
 *   - Truncated title (2 lines max)
 *   - Truncated content preview (120 chars)
 *   - Source attribution
 *
 * Used on:
 *   - Home page recommendations grid
 */

const DOMAIN_STYLES = {
  technology:    "bg-blue-50 border-blue-200 hover:border-blue-300",
  sports:        "bg-green-50 border-green-200 hover:border-green-300",
  politics:      "bg-red-50 border-red-200 hover:border-red-300",
  finance:       "bg-yellow-50 border-yellow-200 hover:border-yellow-300",
  health:        "bg-pink-50 border-pink-200 hover:border-pink-300",
  science:       "bg-purple-50 border-purple-200 hover:border-purple-300",
  environment:   "bg-emerald-50 border-emerald-200 hover:border-emerald-300",
  entertainment: "bg-orange-50 border-orange-200 hover:border-orange-300",
};

const DOMAIN_LABEL_COLORS = {
  technology:    "text-blue-600",
  sports:        "text-green-600",
  politics:      "text-red-600",
  finance:       "text-yellow-600",
  health:        "text-pink-600",
  science:       "text-purple-600",
  environment:   "text-emerald-600",
  entertainment: "text-orange-600",
};

export default function RecommendationCard({ article, similarityScore }) {
  // ── Derived values ─────────────────────────────────────────────────────────

  const domainKey   = article.domain?.toLowerCase() || "";
  const cardStyle   = DOMAIN_STYLES[domainKey]      || "bg-gray-50 border-gray-200 hover:border-gray-300";
  const labelColor  = DOMAIN_LABEL_COLORS[domainKey]|| "text-gray-500";

  const scorePercent = Math.round((similarityScore ?? 0) * 100);
  const showScore    = scorePercent > 0;

  // Content preview — truncate to 120 chars
  const preview =
    article.content?.length > 120
      ? article.content.substring(0, 120) + "…"
      : article.content;

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <article
      className={`
        border rounded-xl p-4
        transition-all duration-200
        hover:shadow-sm cursor-pointer
        ${cardStyle}
      `}
    >
      {/* ── Header row ──────────────────────────────────────────────── */}
      <div className="flex items-start justify-between gap-2 mb-2">

        {/* Domain label */}
        <span
          className={`
            text-xs font-semibold uppercase tracking-wide
            ${labelColor}
          `}
        >
          {article.domain || "General"}
        </span>

        {/* Match score badge — only shown for personalised recommendations */}
        {showScore && (
          <span className="
            flex-shrink-0
            text-xs font-semibold
            text-blue-600 bg-blue-100
            px-2 py-0.5 rounded-full
          ">
            {scorePercent}% match
          </span>
        )}
      </div>

      {/* ── Title ───────────────────────────────────────────────────── */}
      <h4 className="
        font-semibold text-gray-900 text-sm
        leading-snug mb-1.5
        truncate-2
      ">
        {article.title}
      </h4>

      {/* ── Content Preview ─────────────────────────────────────────── */}
      <p className="text-xs text-gray-600 leading-relaxed mb-3">
        {preview}
      </p>

      {/* ── Footer ──────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        {/* Source */}
        {article.source ? (
          <span className="text-xs text-gray-400 truncate">
            — {article.source}
          </span>
        ) : (
          <span />
        )}

        {/* Arrow indicator */}
        <svg
          className="w-3.5 h-3.5 text-gray-400 flex-shrink-0"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5l7 7-7 7"
          />
        </svg>
      </div>
    </article>
  );
}