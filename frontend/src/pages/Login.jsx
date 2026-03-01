/**
 * Login page.
 *
 * Features:
 *   - Email + password form
 *   - Demo credentials box (shown by default for easy testing)
 *   - Error display (wrong credentials, server errors)
 *   - Loading state on submit button
 *   - Redirect to original page after login (via location.state.from)
 *   - Link to Register page
 */

import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate  = useNavigate();
  const location  = useLocation();

  // Redirect back to the page the user tried to access before login
  const from = location.state?.from?.pathname || "/";

  // ── State ──────────────────────────────────────────────────────────────────
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError]     = useState("");
  const [loading, setLoading] = useState(false);

  // ── Handlers ───────────────────────────────────────────────────────────────

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    // Clear error when user starts typing
    if (error) setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    // Basic client-side validation
    if (!form.email.trim())    { setError("Email is required.");    return; }
    if (!form.password.trim()) { setError("Password is required."); return; }

    setLoading(true);
    try {
      await login(form.email.trim(), form.password);
      navigate(from, { replace: true });
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : "Login failed. Please check your credentials."
      );
    } finally {
      setLoading(false);
    }
  };

  // ── Quick fill helper for demo credentials ─────────────────────────────────

  const fillDemo = (type) => {
    if (type === "admin") {
      setForm({ email: "admin@newsplatform.com", password: "Admin@1234" });
    } else {
      setForm({ email: "user@newsplatform.com", password: "User@1234" });
    }
    setError("");
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen flex items-center justify-center
                    bg-gradient-to-br from-blue-50 via-white to-indigo-50
                    px-4 py-12">
      <div className="w-full max-w-md">

        {/* ── Brand header ──────────────────────────────────────────── */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 bg-blue-600 rounded-2xl
                          flex items-center justify-center
                          mx-auto mb-4 shadow-lg">
            <span className="text-white text-xl font-bold">SN</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome back
          </h1>
          <p className="text-gray-500 mt-1 text-sm">
            Sign in to SemanticNews
          </p>
        </div>

        {/* ── Card ──────────────────────────────────────────────────── */}
        <div className="card">

          {/* ── Demo credentials ────────────────────────────────────── */}
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
            <p className="text-xs font-semibold text-blue-800 uppercase
                          tracking-wide mb-2">
              Demo Credentials
            </p>
            <div className="space-y-1.5">
              {/* User demo */}
              <div className="flex items-center justify-between">
                <div className="text-xs text-blue-700">
                  <span className="font-medium">User:</span>{" "}
                  user@newsplatform.com / User@1234
                </div>
                <button
                  type="button"
                  onClick={() => fillDemo("user")}
                  className="text-xs text-blue-600 hover:text-blue-800
                             font-semibold underline ml-2 flex-shrink-0"
                >
                  Use
                </button>
              </div>
              {/* Admin demo */}
              <div className="flex items-center justify-between">
                <div className="text-xs text-blue-700">
                  <span className="font-medium">Admin:</span>{" "}
                  admin@newsplatform.com / Admin@1234
                </div>
                <button
                  type="button"
                  onClick={() => fillDemo("admin")}
                  className="text-xs text-blue-600 hover:text-blue-800
                             font-semibold underline ml-2 flex-shrink-0"
                >
                  Use
                </button>
              </div>
            </div>
          </div>

          {/* ── Error alert ─────────────────────────────────────────── */}
          {error && (
            <div className="alert-error mb-5" role="alert">
              {error}
            </div>
          )}

          {/* ── Form ────────────────────────────────────────────────── */}
          <form onSubmit={handleSubmit} className="space-y-5" noValidate>

            {/* Email */}
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700 mb-1.5"
              >
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                value={form.email}
                onChange={handleChange}
                className="input-field"
                placeholder="you@example.com"
                required
              />
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700 mb-1.5"
              >
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                value={form.password}
                onChange={handleChange}
                className="input-field"
                placeholder="••••••••"
                required
              />
            </div>

            {/* Submit */}
            <button
              type="submit"
              className="btn-primary w-full"
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
                  Signing in...
                </span>
              ) : (
                "Sign In"
              )}
            </button>
          </form>

          {/* ── Register link ────────────────────────────────────────── */}
          <p className="text-center text-sm text-gray-500 mt-5">
            Don&apos;t have an account?{" "}
            <Link
              to="/register"
              className="text-blue-600 font-medium hover:underline"
            >
              Create one free
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}