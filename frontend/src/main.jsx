/**
 * Application entry point.
 *
 * Mounts the React app into the #root div defined in public/index.html.
 * Wraps the app in React.StrictMode for development warnings.
 */

import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);