/**
 * Profile page.
 *
 * Displays:
 *   - User avatar (initial letter)
 *   - Name, email, role badge
 *   - Account metadata (ID, role, status)
 *   - Account stats (placeholder)
 *   - Logout button
 *
 * No API calls needed — user data comes from AuthContext (localStorage).
 */

import { useNavigate } from "react-router-dom";
import { useAuth }     from "../context/AuthContext";

export default function Profile() {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();

  if (!user) return null;

  // ── Handlers ───────────────────────────────────────────────────────────────

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  // ── Derived values ─────────────────────────────────────────────────────────

  const initial   = user.name?.charAt(0).toUpperCase() || "?";
  const joinDate  = user.created_at
    ? new Date(user.created_at).toLocaleDateString("en-US", {
        month: "long", day: "numeric", year: "numeric",
      })
    : "Unknown";

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-10">

      {/* ── Page Header ─────────────────────────────────────────────── */}
      <h1 className="text-2xl font-bold text-gray-900 mb-6">
        My Profile
      </h1>

      {/* ── Profile Card ────────────────────────────────────────────── */}
      <div className="card mb-5">

        {/* Avatar + name row */}
        <div className="flex items-center gap-5 mb-6">
          {/* Avatar circle */}
          <div
            className="w-16 h-16 rounded-full flex items-center justify-center
                       text-white text-2xl font-bold flex-shrink-0 shadow-md"
            style={{ backgroundColor: "#2563eb" }}
            aria-label={`Avatar for ${user.name}`}
          >
            {initial}
          </div>

          <div className="flex-1 min-w-0">
            <h2 className="text-xl font-semibold text-gray-900 truncate">
              {user.name}
            </h2>
            <p className="text-gray-500 text-sm truncate">
              {user.email}
            </p>
          </div>

          {/* Role badge */}
          <span
            className={`badge flex-shrink-0 ${
              isAdmin
                ? "bg-red-100 text-red-700"
                : "bg-green-100 text-green-700"
            }`}
          >
            {isAdmin ? "🔑 Admin" : "👤 User"}
          </span>
        </div>

        {/* ── Account details grid ─────────────────────────────────── */}
        <div className="border-t border-gray-100 pt-5
                        grid grid-cols-2 sm:grid-cols-3 gap-4">
          {[
            {
              label: "Member ID",
              value: `#${user.id}`,
            },
            {
              label: "Role",
              value: user.role.charAt(0).toUpperCase() + user.role.slice(1),
            },
            {
              label: "Account Status",
              value: "Active",
              valueClass: "text-green-600",
            },
            {
              label: "Member Since",
              value: joinDate,
            },
            {
              label: "Email",
              value: user.email,
              colSpan: true,
            },
          ].map((item) => (
            <div
              key={item.label}
              className={item.colSpan ? "col-span-2 sm:col-span-2" : ""}
            >
              <p className="text-xs text-gray-400 uppercase tracking-wide mb-0.5">
                {item.label}
              </p>
              <p
                className={`text-sm font-medium text-gray-800 truncate
                  ${item.valueClass || ""}`}
              >
                {item.value}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* ── Quick Links ──────────────────────────────────────────────── */}
      <div className="card mb-5">
        <h3 className="font-semibold text-gray-900 mb-4">Quick Links</h3>
        <div className="grid grid-cols-2 gap-3">
          {[
            { label: "🔍 Search Articles",  path: "/search" },
            { label: "📊 View Dashboard",   path: "/dashboard" },
            { label: "🏠 Go Home",          path: "/" },
            ...(isAdmin
              ? [{ label: "📤 Upload Article", path: "/upload" }]
              : []
            ),
          ].map((link) => (
            <button
              key={link.path}
              onClick={() => navigate(link.path)}
              className="btn-secondary text-sm text-left justify-start"
            >
              {link.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Logout Card ──────────────────────────────────────────────── */}
      <div className="card border-red-200 bg-red-50">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="font-semibold text-red-900 mb-1">
              Sign Out
            </h3>
            <p className="text-sm text-red-700">
              You will be redirected to the login page.
              Your JWT token will be cleared from this device.
            </p>
          </div>
          <button
            onClick={handleLogout}
            className="btn-danger flex-shrink-0 text-sm"
          >
            Sign Out
          </button>
        </div>
      </div>

    </div>
  );
}