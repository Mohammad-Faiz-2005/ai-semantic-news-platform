/**
 * AuthContext — Global authentication state management.
 *
 * Provides:
 *   user          → Current user object { id, name, email, role, created_at }
 *   token         → JWT access token string
 *   isAuthenticated → Boolean: true if token exists
 *   isAdmin       → Boolean: true if user.role === "admin"
 *   login()       → POST /auth/login → stores token + user
 *   register()    → POST /auth/register → stores token + user
 *   logout()      → Clears token + user from state and localStorage
 *
 * Persistence:
 *   Token and user are stored in localStorage so they survive page refreshes.
 *   On mount, the context reads from localStorage to restore the session.
 *
 * Usage:
 *   import { useAuth } from "../context/AuthContext";
 *   const { user, isAuthenticated, login, logout } = useAuth();
 */

import React, {
  createContext,
  useContext,
  useState,
  useCallback,
} from "react";
import api from "../api/axios";

// ── Context ───────────────────────────────────────────────────────────────────

const AuthContext = createContext(null);

// ── Provider ──────────────────────────────────────────────────────────────────

export function AuthProvider({ children }) {
  /**
   * Initialise state from localStorage.
   *
   * This runs once on mount, restoring the session from a previous visit.
   * If localStorage is corrupted or missing, defaults to null.
   */
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem("user");
      return stored ? JSON.parse(stored) : null;
    } catch {
      // Corrupted JSON in localStorage — clear it
      localStorage.removeItem("user");
      return null;
    }
  });

  const [token, setToken] = useState(
    () => localStorage.getItem("access_token") || null
  );

  // ── Helper: persist auth data ───────────────────────────────────────────────

  const _persistAuth = useCallback((accessToken, userData) => {
    /**
     * Store token and user in both React state and localStorage.
     * Called after successful login or register.
     */
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("user", JSON.stringify(userData));
    setToken(accessToken);
    setUser(userData);
  }, []);

  // ── Login ─────────────────────────────────────────────────────────────────

  const login = useCallback(
    async (email, password) => {
      /**
       * Authenticate with the backend.
       *
       * Args:
       *   email:    User's email address.
       *   password: User's plain-text password.
       *
       * Returns:
       *   The user object on success.
       *
       * Throws:
       *   Axios error on failure (401 for wrong credentials, etc.)
       *   Calling component is responsible for catching and displaying errors.
       */
      const { data } = await api.post("/auth/login", { email, password });

      _persistAuth(data.access_token, data.user);

      return data.user;
    },
    [_persistAuth]
  );

  // ── Register ──────────────────────────────────────────────────────────────

  const register = useCallback(
    async (name, email, password) => {
      /**
       * Create a new user account and log in.
       *
       * Args:
       *   name:     Full name of the new user.
       *   email:    Email address (must be unique).
       *   password: Plain-text password (min 6 chars).
       *
       * Returns:
       *   The newly created user object on success.
       *
       * Throws:
       *   Axios error on failure (409 for duplicate email, 422 for validation, etc.)
       */
      const { data } = await api.post("/auth/register", {
        name,
        email,
        password,
      });

      _persistAuth(data.access_token, data.user);

      return data.user;
    },
    [_persistAuth]
  );

  // ── Logout ────────────────────────────────────────────────────────────────

  const logout = useCallback(() => {
    /**
     * Clear all auth state and localStorage data.
     *
     * Does NOT call any backend endpoint (JWT is stateless).
     * The token simply expires on its own after ACCESS_TOKEN_EXPIRE_MINUTES.
     */
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    setToken(null);
    setUser(null);
  }, []);

  // ── Context Value ─────────────────────────────────────────────────────────

  const value = {
    user,
    token,
    login,
    register,
    logout,
    isAuthenticated: !!token,
    isAdmin: user?.role === "admin",
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useAuth() {
  /**
   * Custom hook to access AuthContext.
   *
   * Must be used inside an <AuthProvider> component.
   *
   * Returns:
   *   The full AuthContext value object.
   *
   * Throws:
   *   Error if used outside of AuthProvider.
   */
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth() must be used inside an <AuthProvider>. " +
      "Wrap your component tree with <AuthProvider>."
    );
  }

  return context;
}