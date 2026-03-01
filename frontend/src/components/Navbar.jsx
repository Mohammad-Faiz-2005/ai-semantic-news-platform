/**
 * Navbar — Sticky top navigation bar.
 *
 * Features:
 *   - Brand logo + name (links to home)
 *   - Desktop nav links with active state highlighting
 *   - Role-based links (Upload only shown to admins)
 *   - Mobile hamburger menu (toggleable)
 *   - Logout button
 *
 * Active link styling:
 *   Uses NavLink from react-router-dom with isActive callback.
 *   Active links get blue text + blue background pill.
 */

import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { isAuthenticated, isAdmin, logout, user } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  // ── Handlers ───────────────────────────────────────────────────────────────

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const closeMenu = () => setMenuOpen(false);

  // ── Styles ─────────────────────────────────────────────────────────────────

  const navLinkClass = ({ isActive }) =>
    [
      "text-sm font-medium px-3 py-2 rounded-lg transition-colors duration-200",
      isActive
        ? "text-blue-600 bg-blue-50"
        : "text-gray-600 hover:text-gray-900 hover:bg-gray-100",
    ].join(" ");

  const mobileNavLinkClass = ({ isActive }) =>
    [
      "block text-sm font-medium px-4 py-2.5 rounded-lg transition-colors duration-200",
      isActive
        ? "text-blue-600 bg-blue-50"
        : "text-gray-700 hover:text-gray-900 hover:bg-gray-100",
    ].join(" ");

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">

          {/* ── Brand ──────────────────────────────────────────────────── */}
          <Link
            to="/"
            className="flex items-center gap-2.5 flex-shrink-0"
            onClick={closeMenu}
          >
            {/* Logo mark */}
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-sm">
              <span className="text-white text-sm font-bold tracking-tight">
                SN
              </span>
            </div>

            {/* Brand name — hidden on very small screens */}
            <div className="hidden sm:block">
              <span className="font-bold text-gray-900 text-lg leading-none">
                SemanticNews
              </span>
              <span className="block text-xs text-gray-400 leading-none mt-0.5">
                AI-Powered Search
              </span>
            </div>
          </Link>

          {/* ── Desktop Navigation ─────────────────────────────────────── */}
          <div className="hidden md:flex items-center gap-1">
            {isAuthenticated ? (
              <>
                <NavLink to="/" className={navLinkClass} end>
                  Home
                </NavLink>

                <NavLink to="/search" className={navLinkClass}>
                  Search
                </NavLink>

                <NavLink to="/dashboard" className={navLinkClass}>
                  Dashboard
                </NavLink>

                {/* Upload — only visible to admins */}
                {isAdmin && (
                  <NavLink to="/upload" className={navLinkClass}>
                    Upload
                    <span className="ml-1.5 inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-red-100 text-red-700">
                      Admin
                    </span>
                  </NavLink>
                )}

                <NavLink to="/profile" className={navLinkClass}>
                  Profile
                </NavLink>

                {/* Divider */}
                <div className="w-px h-5 bg-gray-200 mx-2" />

                {/* User info */}
                <span className="text-sm text-gray-500 mr-1">
                  {user?.name?.split(" ")[0]}
                </span>

                {/* Logout */}
                <button
                  onClick={handleLogout}
                  className="text-sm font-medium text-red-600 hover:text-red-700
                             px-3 py-2 rounded-lg hover:bg-red-50
                             transition-colors duration-200"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <NavLink to="/login" className={navLinkClass}>
                  Login
                </NavLink>
                <Link to="/register" className="btn-primary text-sm ml-1">
                  Get Started
                </Link>
              </>
            )}
          </div>

          {/* ── Mobile Hamburger Button ─────────────────────────────────── */}
          <button
            className="md:hidden p-2 rounded-lg text-gray-600
                       hover:bg-gray-100 hover:text-gray-900
                       transition-colors duration-200
                       focus:outline-none focus:ring-2 focus:ring-blue-500"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label={menuOpen ? "Close menu" : "Open menu"}
            aria-expanded={menuOpen}
          >
            {menuOpen ? (
              /* Close (X) icon */
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            ) : (
              /* Hamburger icon */
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            )}
          </button>
        </div>

        {/* ── Mobile Menu (dropdown) ──────────────────────────────────── */}
        {menuOpen && (
          <div className="md:hidden border-t border-gray-100 py-3 space-y-1">
            {isAuthenticated ? (
              <>
                <NavLink
                  to="/"
                  className={mobileNavLinkClass}
                  end
                  onClick={closeMenu}
                >
                  🏠 Home
                </NavLink>

                <NavLink
                  to="/search"
                  className={mobileNavLinkClass}
                  onClick={closeMenu}
                >
                  🔍 Search
                </NavLink>

                <NavLink
                  to="/dashboard"
                  className={mobileNavLinkClass}
                  onClick={closeMenu}
                >
                  📊 Dashboard
                </NavLink>

                {isAdmin && (
                  <NavLink
                    to="/upload"
                    className={mobileNavLinkClass}
                    onClick={closeMenu}
                  >
                    📤 Upload
                    <span className="ml-2 text-xs bg-red-100 text-red-700 px-1.5 py-0.5 rounded">
                      Admin
                    </span>
                  </NavLink>
                )}

                <NavLink
                  to="/profile"
                  className={mobileNavLinkClass}
                  onClick={closeMenu}
                >
                  👤 Profile
                </NavLink>

                {/* Divider */}
                <div className="border-t border-gray-100 my-2" />

                {/* User info row */}
                <div className="px-4 py-1 text-xs text-gray-400">
                  Signed in as{" "}
                  <span className="font-medium text-gray-600">{user?.email}</span>
                </div>

                <button
                  onClick={() => { handleLogout(); closeMenu(); }}
                  className="w-full text-left block text-sm font-medium
                             text-red-600 hover:text-red-700
                             px-4 py-2.5 rounded-lg hover:bg-red-50
                             transition-colors duration-200"
                >
                  🚪 Logout
                </button>
              </>
            ) : (
              <>
                <NavLink
                  to="/login"
                  className={mobileNavLinkClass}
                  onClick={closeMenu}
                >
                  Login
                </NavLink>
                <NavLink
                  to="/register"
                  className={mobileNavLinkClass}
                  onClick={closeMenu}
                >
                  Register
                </NavLink>
              </>
            )}
          </div>
        )}
      </div>
    </nav>
  );
}