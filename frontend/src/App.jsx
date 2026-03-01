/**
 * App.jsx — Root application component.
 *
 * Sets up:
 *   - React Router v6 (BrowserRouter)
 *   - AuthProvider context (global JWT state)
 *   - Route definitions:
 *       Public routes:    /login, /register
 *       Protected routes: everything else (requires valid JWT)
 *       Admin routes:     /upload (requires admin role)
 *
 * Layout:
 *   Protected pages include the Navbar at the top.
 *   Public pages (Login, Register) render without Navbar.
 */

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./routes/ProtectedRoute";
import Navbar from "./components/Navbar";

// Pages
import Login         from "./pages/Login";
import Register      from "./pages/Register";
import Home          from "./pages/Home";
import Search        from "./pages/Search";
import Results       from "./pages/Results";
import UploadArticle from "./pages/UploadArticle";
import Dashboard     from "./pages/Dashboard";
import Profile       from "./pages/Profile";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="min-h-screen bg-gray-50">
          <Routes>

            {/* ── Public Routes (no Navbar, no auth required) ──────────── */}
            <Route path="/login"    element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* ── Protected Routes (Navbar + auth required) ────────────── */}
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <>
                    {/* Sticky top navigation bar */}
                    <Navbar />

                    {/* Page content rendered below the navbar */}
                    <main className="min-h-[calc(100vh-4rem)]">
                      <Routes>

                        {/* Home — hero search + recommendations */}
                        <Route path="/" element={<Home />} />

                        {/* Search — dedicated search page */}
                        <Route path="/search" element={<Search />} />

                        {/* Results — search results with similarity scores */}
                        <Route path="/results" element={<Results />} />

                        {/* Dashboard — analytics charts + model comparison */}
                        <Route path="/dashboard" element={<Dashboard />} />

                        {/* Profile — user info + logout */}
                        <Route path="/profile" element={<Profile />} />

                        {/* Upload — admin only article upload */}
                        <Route
                          path="/upload"
                          element={
                            <ProtectedRoute adminOnly>
                              <UploadArticle />
                            </ProtectedRoute>
                          }
                        />

                        {/* Catch-all → redirect to home */}
                        <Route
                          path="*"
                          element={<Navigate to="/" replace />}
                        />

                      </Routes>
                    </main>
                  </>
                </ProtectedRoute>
              }
            />

          </Routes>
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
}