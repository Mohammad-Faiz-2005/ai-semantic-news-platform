/**
 * ProtectedRoute — Guards routes that require authentication.
 *
 * Behaviour:
 *   - If user is NOT authenticated:
 *       Redirects to /login
 *       Preserves the attempted URL in location state (for redirect after login)
 *
 *   - If adminOnly=true and user is NOT admin:
 *       Redirects to / (home page)
 *       Shows no error — admins-only routes are simply inaccessible
 *
 *   - If all checks pass:
 *       Renders the children components normally
 *
 * Props:
 *   children  (ReactNode) — The protected page/component to render
 *   adminOnly (boolean)   — If true, also requires admin role. Default: false
 *
 * Usage:
 *   // Protect any authenticated user
 *   <ProtectedRoute>
 *     <Dashboard />
 *   </ProtectedRoute>
 *
 *   // Protect admin-only pages
 *   <ProtectedRoute adminOnly>
 *     <UploadArticle />
 *   </ProtectedRoute>
 */

import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({
  children,
  adminOnly = false,
}) {
  const { isAuthenticated, isAdmin } = useAuth();
  const location = useLocation();

  // ── Not logged in → redirect to login ────────────────────────────────────

  if (!isAuthenticated) {
    /**
     * Redirect to /login and pass the current location in state.
     * After successful login, the Login page can redirect back here.
     *
     * Example:
     *   User visits /dashboard → redirected to /login
     *   After login → redirected back to /dashboard
     */
    return (
      <Navigate
        to="/login"
        state={{ from: location }}
        replace
      />
    );
  }

  // ── Logged in but not admin → redirect to home ───────────────────────────

  if (adminOnly && !isAdmin) {
    /**
     * Non-admin users trying to access admin pages are silently
     * redirected to the home page. We don't show an error page
     * to avoid leaking information about admin routes.
     */
    return (
      <Navigate
        to="/"
        replace
      />
    );
  }

  // ── All checks passed → render children ──────────────────────────────────

  return children;
}