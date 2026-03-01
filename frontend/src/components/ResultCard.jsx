/**
 * ResultCard — Displays a single search result article.
 *
 * Props:
 *   article         (object) — Article data from API response
 *   similarityScore (number) — Cosine similarity score (0.0 - 1.0)
 *   rank            (number) — Rank position (1-based)
 *
 * Features:
 *   - Rank badge (numbered circle)
 *   - Domain colour badge
 *   - Source and date metadata
 *   - Truncated content preview (220 chars)
 *   - Similarity score with colour coding:
 *       ≥ 80% → green
 *       ≥ 60% → yellow
 *       < 60% → gray
 */

const DOMAIN_COLORS = {
  technology:   "bg-blue-100 text-blue-700 border-blue-200",
  sports:       "bg-green-100 text-green-700 border-green-200",
  politics:     "bg-red-100 text-red-700 border-red-200",
  finance:      "bg-yellow-100 text-yellow-700 border-yellow-200",
  health:       "bg-pink-100 text-pink-700 border-pink-200",
  science:      "bg-purple-100 text-purple-700 border-purple-200",
  environment:  "bg-emerald-100 text-emerald-700 border-emerald-200",
  entertainment:"bg-orange-100 text-orange-700 border-orange-200",
};

const RANK_COLORS = [
  "bg-yellow-400 text-yellow-900",  // Rank 1 — gold
  "bg-gray-300 text-gray-800",      // Rank 2 — silver
  "bg-amber-500 text-amber-900",    // Rank 3 — bronze
];

export default function ResultCard({ article, similarityScore, rank }) {
  // ── Derived values ─────────────────────────────────────────────────────────

  const domainKey   = article.domain?.toLowerCase() || "";
  const domainColor = DOMAIN_COLORS[domainKey] || "bg-gray-100 text-gray-600 border-gray-200";

  const scorePercent = Math.round((similarityScore ?? 0) * 100);
  const scoreColor   =
    scorePercent >= 80 ? "text-green-600" :
    scorePercent >= 60 ? "text-yellow-600" :
    "text-gray-400";

  const rankBadgeColor =
    rank <= 3
      ? RANK_COLORS[rank - 1]
      : "bg-blue-600 text-white";

  // Content preview — truncate to 220 chars
  const preview =
    article.content?.length > 220
      ? article.content.substring(0, 220) + "…"
      : article.content;

  // Format date
  const formattedDate = article.created_at
    ? new Date(article.created_at).toLocaleDateString("en-US", {
        month:  "short",
        day:    "numeric",
        year:   "numeric",
      })
    : null;

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <article className="card-hover">
      <div className="flex items-start gap-4">

        {/* ── Rank Badge ────────────────────────────────────────────── */}
        <div
          className={`
            flex-shrink-0
            w-8 h-8
            rounded-full
            flex items-center justify-center
            text-xs font-bold
            ${rankBadgeColor}
          `}
          aria-label={`Rank ${rank}`}
        >
          {rank}
        </div>

        {/* ── Article Content ───────────────────────────────────────── */}
        <div className="flex-1 min-w-0">

          {/* Metadata row */}
          <div className="flex items-center gap-2 flex-wrap mb-2">
            {/* Domain badge */}
            {article.domain && (
              <span className={`badge border ${domainColor}`}>
                {article.domain}
              </span>
            )}

            {/* Source */}
            {article.source && (
              <span className="text-xs text-gray-400">
                {article.source}
              </span>
            )}

            {/* Embedding status */}
            {article.embedding_generated && (
              <span className="text-xs text-emerald-500 flex items-center gap-0.5">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
                Indexed
              </span>
            )}

            {/* Date — pushed to the right */}
            {formattedDate && (
              <span className="text-xs text-gray-400 ml-auto">
                {formattedDate}
              </span>
            )}
          </div>

          {/* Title */}
          <h3 className="font-semibold text-gray-900 text-base leading-snug mb-1.5">
            {article.title}
          </h3>

          {/* Content preview */}
          <p className="text-sm text-gray-600 leading-relaxed">
            {preview}
          </p>

        </div>

        {/* ── Similarity Score ──────────────────────────────────────── */}
        {similarityScore !== undefined && (
          <div className="flex-shrink-0 text-right min-w-[52px]">
            <p className={`text-xl font-bold leading-none ${scoreColor}`}>
              {scorePercent}%
            </p>
            <p className="text-xs text-gray-400 mt-0.5 leading-none">
              match
            </p>

            {/* Score bar */}
            <div className="w-12 h-1 bg-gray-200 rounded-full mt-2 ml-auto">
              <div
                className={`h-1 rounded-full transition-all ${
                  scorePercent >= 80 ? "bg-green-500" :
                  scorePercent >= 60 ? "bg-yellow-400" :
                  "bg-gray-300"
                }`}
                style={{ width: `${scorePercent}%` }}
              />
            </div>
          </div>
        )}

      </div>
    </article>
  );
}