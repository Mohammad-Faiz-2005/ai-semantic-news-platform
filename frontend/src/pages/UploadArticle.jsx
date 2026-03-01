/**
 * UploadArticle page (Admin only).
 *
 * Features:
 *   - Title, domain, source, content fields
 *   - Character counter for content
 *   - Client-side validation (min content length)
 *   - Success message with article details after upload
 *   - Error display
 *   - Loading state on submit
 *   - Admin-only warning banner
 *
 * On success:
 *   The article is immediately searchable (FAISS updated server-side).
 */

import { useState } from "react";
import api from "../api/axios";

// ── Constants ─────────────────────────────────────────────────────────────────

const DOMAINS = [
  "technology",
  "politics",
  "sports",
  "finance",
  "health",
  "science",
  "environment",
  "entertainment",
];

const MIN_CONTENT_LENGTH = 50;

export default function UploadArticle() {
  // ── State ──────────────────────────────────────────────────────────────────
  const [form, setForm] = useState({
    title:   "",
    content: "",
    domain:  "",
    source:  "",
  });
  const [loading, setLoading]   = useState(false);
  const [success, setSuccess]   = useState(null);   // { message, article }
  const [error, setError]       = useState("");

  // ── Handlers ───────────────────────────────────────────────────────────────

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    if (error) setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess(null);

    // Client-side validation
    if (!form.title.trim()) {
      setError("Article title is required."); return;
    }
    if (form.content.trim().length < MIN_CONTENT_LENGTH) {
      setError(`Content must be at least ${MIN_CONTENT_LENGTH} characters.`); return;
    }

    setLoading(true);
    try {
      const { data } = await api.post("/upload", {
        title:   form.title.trim(),
        content: form.content.trim(),
        domain:  form.domain  || null,
        source:  form.source.trim() || null,
      });

      setSuccess({
        message: data.message,
        article: data.article,
      });

      // Reset form
      setForm({ title: "", content: "", domain: "", source: "" });

    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : "Upload failed. Ensure you are logged in as an admin."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setForm({ title: "", content: "", domain: "", source: "" });
    setError("");
    setSuccess(null);
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-10">

      {/* ── Page Header ─────────────────────────────────────────────── */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-2xl font-bold text-gray-900">
            Upload Article
          </h1>
          <span className="badge bg-red-100 text-red-700">Admin Only</span>
        </div>
        <p className="text-gray-500 text-sm leading-relaxed">
          Add a new article to the platform. The SBERT embedding is generated
          automatically and added to the FAISS index — the article is
          immediately searchable after upload.
        </p>
      </div>

      {/* ── Success Message ──────────────────────────────────────────── */}
      {success && (
        <div className="alert-success mb-6">
          <div className="flex items-start gap-3">
            <span className="text-xl flex-shrink-0">✅</span>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-green-900">
                Article uploaded successfully
              </p>
              <p className="text-sm text-green-700 mt-0.5">
                {success.message}
              </p>
              {/* Article summary */}
              <div className="mt-3 bg-white border border-green-200
                              rounded-lg p-3 text-sm">
                <p className="font-medium text-gray-800 truncate">
                  {success.article.title}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  {success.article.domain && (
                    <span className="badge bg-blue-100 text-blue-700">
                      {success.article.domain}
                    </span>
                  )}
                  <span className="text-xs text-gray-400">
                    ID: {success.article.id}
                  </span>
                  {success.article.embedding_generated && (
                    <span className="text-xs text-green-600">
                      ✓ Indexed in FAISS
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={() => setSuccess(null)}
                className="btn-secondary text-sm mt-3"
              >
                Upload another article
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Error Message ────────────────────────────────────────────── */}
      {error && (
        <div className="alert-error mb-6">
          <div className="flex items-start gap-2">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* ── Upload Form ──────────────────────────────────────────────── */}
      {!success && (
        <div className="card">
          <form onSubmit={handleSubmit} className="space-y-5" noValidate>

            {/* ── Title ───────────────────────────────────────────────── */}
            <div>
              <label
                htmlFor="title"
                className="block text-sm font-medium text-gray-700 mb-1.5"
              >
                Article Title{" "}
                <span className="text-red-500">*</span>
              </label>
              <input
                id="title"
                name="title"
                type="text"
                value={form.title}
                onChange={handleChange}
                className="input-field"
                placeholder="e.g. Breakthrough in Quantum Computing Announced"
                required
              />
            </div>

            {/* ── Domain + Source (side by side) ───────────────────── */}
            <div className="grid grid-cols-2 gap-4">

              {/* Domain */}
              <div>
                <label
                  htmlFor="domain"
                  className="block text-sm font-medium text-gray-700 mb-1.5"
                >
                  Domain
                </label>
                <select
                  id="domain"
                  name="domain"
                  value={form.domain}
                  onChange={handleChange}
                  className="input-field cursor-pointer"
                >
                  <option value="">Select domain...</option>
                  {DOMAINS.map((d) => (
                    <option key={d} value={d}>
                      {d.charAt(0).toUpperCase() + d.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              {/* Source */}
              <div>
                <label
                  htmlFor="source"
                  className="block text-sm font-medium text-gray-700 mb-1.5"
                >
                  Source
                </label>
                <input
                  id="source"
                  name="source"
                  type="text"
                  value={form.source}
                  onChange={handleChange}
                  className="input-field"
                  placeholder="e.g. BBC News"
                />
              </div>
            </div>

            {/* ── Content ─────────────────────────────────────────────── */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label
                  htmlFor="content"
                  className="block text-sm font-medium text-gray-700"
                >
                  Article Content{" "}
                  <span className="text-red-500">*</span>
                  <span className="text-gray-400 font-normal ml-1">
                    (min {MIN_CONTENT_LENGTH} characters)
                  </span>
                </label>

                {/* Character counter */}
                <span className={`text-xs ${
                  form.content.length < MIN_CONTENT_LENGTH
                    ? "text-red-400"
                    : "text-green-500"
                }`}>
                  {form.content.length} chars
                  {form.content.length >= MIN_CONTENT_LENGTH && " ✓"}
                </span>
              </div>

              <textarea
                id="content"
                name="content"
                value={form.content}
                onChange={handleChange}
                rows={10}
                className="input-field resize-none font-mono text-sm"
                placeholder="Paste or type the full article text here..."
                required
              />

              {/* Progress bar for content length */}
              <div className="mt-1.5 h-1 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-300 ${
                    form.content.length >= MIN_CONTENT_LENGTH
                      ? "bg-green-500"
                      : "bg-red-400"
                  }`}
                  style={{
                    width: `${Math.min(
                      (form.content.length / MIN_CONTENT_LENGTH) * 100,
                      100
                    )}%`,
                  }}
                />
              </div>
            </div>

            {/* ── Form Actions ─────────────────────────────────────────── */}
            <div className="flex gap-3 pt-2">
              <button
                type="submit"
                className="btn-primary flex-1"
                disabled={loading}
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg
                      className="animate-spin h-4 w-4 text-white"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12" cy="12" r="10"
                        stroke="currentColor" strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8v8H4z"
                      />
                    </svg>
                    Uploading & Indexing...
                  </span>
                ) : (
                  "Upload & Index Article"
                )}
              </button>

              <button
                type="button"
                onClick={handleReset}
                className="btn-secondary"
                disabled={loading}
              >
                Clear
              </button>
            </div>
          </form>
        </div>
      )}

      {/* ── Info Banner ──────────────────────────────────────────────── */}
      <div className="alert-warning mt-6">
        <div className="flex items-start gap-2">
          <span className="text-lg flex-shrink-0">⚠️</span>
          <div className="text-sm">
            <p className="font-semibold text-amber-900 mb-1">
              Admin-only endpoint
            </p>
            <p className="text-amber-800 leading-relaxed">
              This page requires admin credentials. Uploaded articles are
              immediately processed by SBERT to generate embeddings and
              added to the live FAISS index. They appear in search results
              within seconds of upload.
            </p>
          </div>
        </div>
      </div>

    </div>
  );
}