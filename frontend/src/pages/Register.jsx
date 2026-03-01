/**
 * Register page.
 *
 * Features:
 *   - Name, email, password, confirm password fields
 *   - Client-side validation (password match, min length)
 *   - Error display (duplicate email, server errors)
 *   - Loading state on submit
 *   - Redirect to home on success
 *   - Link to Login page
 */

import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Register() {
  const { register } = useAuth();
  const navigate     = useNavigate();

  // ── State ──────────────────────────────────────────────────────────────────
  const [form, setForm] = useState({
    name: "", email: "", password: "", confirmPassword: "",
  });
  const [error, setError]     = useState("");
  const [loading, setLoading] = useState(false);

  // ── Handlers ───────────────────────────────────────────────────────────────

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    if (error) setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    // Client-side validation
    if (!form.name.trim()) {
      setError("Full name is required."); return;
    }
    if (!form.email.trim()) {
      setError("Email address is required."); return;
    }
    if (form.password.length < 6) {
      setError("Password must be at least 6 characters."); return;
    }
    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match."); return;
    }

    setLoading(true);
    try {
      await register(form.name.trim(), form.email.trim(), form.password);
      navigate("/", { replace: true });
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : "Registration failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
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
            Create an account
          </h1>
          <p className="text-gray-500 mt-1 text-sm">
            Join SemanticNews today — it&apos;s free
          </p>
        </div>

        {/* ── Card ──────────────────────────────────────────────────── */}
        <div className="card">

          {/* ── Error alert ─────────────────────────────────────────── */}
          {error && (
            <div className="alert-error mb-5" role="alert">
              {error}
            </div>
          )}

          {/* ── Form ────────────────────────────────────────────────── */}
          <form onSubmit={handleSubmit} className="space-y-5" noValidate>

            {/* Full Name */}
            <div>
              <label
                htmlFor="name"
                className="block text-sm font-medium text-gray-700 mb-1.5"
              >
                Full name
              </label>
              <input
                id="name"
                name="name"
                type="text"
                autoComplete="name"
                value={form.name}
                onChange={handleChange}
                className="input-field"
                placeholder="Jane Doe"
                required
              />
            </div>

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
                placeholder="jane@example.com"
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
                <span className="text-gray-400 font-normal ml-1">
                  (min. 6 characters)
                </span>
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                value={form.password}
                onChange={handleChange}
                className="input-field"
                placeholder="••••••••"
                required
              />
            </div>

            {/* Confirm Password */}
            <div>
              <label
                htmlFor="confirmPassword"
                className="block text-sm font-medium text-gray-700 mb-1.5"
              >
                Confirm password
              </label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                autoComplete="new-password"
                value={form.confirmPassword}
                onChange={handleChange}
                className={`input-field ${
                  form.confirmPassword && form.password !== form.confirmPassword
                    ? "border-red-400 focus:ring-red-400"
                    : ""
                }`}
                placeholder="••••••••"
                required
              />
              {/* Inline mismatch warning */}
              {form.confirmPassword &&
                form.password !== form.confirmPassword && (
                  <p className="text-xs text-red-500 mt-1">
                    Passwords do not match.
                  </p>
                )}
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
                  Creating account...
                </span>
              ) : (
                "Create Account"
              )}
            </button>
          </form>

          {/* ── Login link ───────────────────────────────────────────── */}
          <p className="text-center text-sm text-gray-500 mt-5">
            Already have an account?{" "}
            <Link
              to="/login"
              className="text-blue-600 font-medium hover:underline"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}