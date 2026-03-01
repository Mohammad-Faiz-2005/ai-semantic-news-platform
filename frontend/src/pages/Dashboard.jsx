/**
 * Dashboard page — Analytics and model comparison.
 *
 * Sections:
 *   1. Platform stats (articles, users, searches)
 *   2. Model comparison metrics table
 *   3. F1 Score bar chart
 *   4. Precision@K & Recall@K grouped bar chart
 *   5. LSTM training loss curves (line chart)
 *   6. Retrieval time comparison (bar chart)
 *   7. Article domain distribution (badges)
 *
 * Data sources:
 *   GET /api/v1/analytics
 *   GET /api/v1/analytics/loss-curves
 *   GET /api/v1/analytics/retrieval-comparison
 */

import { useEffect, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Bar, Line } from "react-chartjs-2";
import api from "../api/axios";

// Register Chart.js components
ChartJS.register(
  CategoryScale, LinearScale,
  BarElement, LineElement, PointElement,
  Title, Tooltip, Legend, Filler
);

// ── Chart colour palettes ─────────────────────────────────────────────────────

const MODEL_COLORS = [
  "rgba(251, 191, 36, 0.85)",   // TF-IDF   — amber
  "rgba(139, 92, 246, 0.85)",   // LSTM      — purple
  "rgba(59, 130, 246, 0.85)",   // SBERT     — blue
];

const MODEL_COLORS_LIGHT = [
  "rgba(251, 191, 36, 0.35)",
  "rgba(139, 92, 246, 0.35)",
  "rgba(59, 130, 246, 0.35)",
];

// ── Shared chart options factory ──────────────────────────────────────────────

const makeChartOptions = (title, yMax = 1) => ({
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: { position: "top", labels: { font: { size: 11 } } },
    title:  { display: true, text: title, font: { size: 13, weight: "600" } },
  },
  scales: {
    y: {
      beginAtZero: true,
      max: yMax,
      ticks: { font: { size: 11 } },
    },
    x: {
      ticks: { font: { size: 11 } },
    },
  },
});

export default function Dashboard() {
  // ── State ──────────────────────────────────────────────────────────────────
  const [analytics,  setAnalytics]  = useState(null);
  const [lossCurves, setLossCurves] = useState(null);
  const [retrieval,  setRetrieval]  = useState(null);
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState("");

  // ── Fetch all dashboard data on mount ─────────────────────────────────────
  useEffect(() => {
    Promise.all([
      api.get("/analytics"),
      api.get("/analytics/loss-curves"),
      api.get("/analytics/retrieval-comparison"),
    ])
      .then(([a, l, r]) => {
        setAnalytics(a.data);
        setLossCurves(l.data);
        setRetrieval(r.data);
      })
      .catch(() => setError("Failed to load analytics data."))
      .finally(() => setLoading(false));
  }, []);

  // ── Loading skeletons ──────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">
          Analytics Dashboard
        </h1>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="skeleton h-24 rounded-xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="skeleton h-64 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  // ── Error state ────────────────────────────────────────────────────────────
  if (error) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-10">
        <div className="alert-error">{error}</div>
      </div>
    );
  }

  // ── Derived chart data ─────────────────────────────────────────────────────
  const models     = analytics?.model_metrics || [];
  const modelNames = models.map((m) => m.model_name);

  const f1ChartData = {
    labels: modelNames,
    datasets: [{
      label:           "F1 Score",
      data:            models.map((m) => m.f1_score),
      backgroundColor: MODEL_COLORS,
      borderRadius:    6,
      borderWidth:     0,
    }],
  };

  const pkChartData = {
    labels: modelNames,
    datasets: [
      {
        label:           "Precision@K",
        data:            models.map((m) => m.precision_at_k),
        backgroundColor: MODEL_COLORS,
        borderRadius:    6,
        borderWidth:     0,
      },
      {
        label:           "Recall@K",
        data:            models.map((m) => m.recall_at_k),
        backgroundColor: MODEL_COLORS_LIGHT,
        borderRadius:    6,
        borderWidth:     0,
      },
    ],
  };

  const lossChartData = lossCurves && {
    labels: lossCurves.epochs,
    datasets: [
      {
        label:           "Train Loss",
        data:            lossCurves.train_loss,
        borderColor:     "rgb(59, 130, 246)",
        backgroundColor: "rgba(59, 130, 246, 0.1)",
        tension:         0.4,
        fill:            true,
        pointRadius:     2,
      },
      {
        label:           "Val Loss",
        data:            lossCurves.val_loss,
        borderColor:     "rgb(239, 68, 68)",
        backgroundColor: "rgba(239, 68, 68, 0.1)",
        tension:         0.4,
        fill:            true,
        pointRadius:     2,
      },
    ],
  };

  const retrievalChartData = retrieval && {
    labels: retrieval.models,
    datasets: [{
      label:           "Retrieval Time (ms)",
      data:            retrieval.retrieval_time_ms,
      backgroundColor: MODEL_COLORS,
      borderRadius:    6,
      borderWidth:     0,
    }],
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">

      {/* ── Page Header ─────────────────────────────────────────────── */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Analytics Dashboard
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          Platform statistics and ML model comparison metrics
        </p>
      </div>

      {/* ── Platform Stats ───────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        {[
          {
            label: "Total Articles",
            value: analytics?.total_articles ?? "—",
            icon:  "📰",
            color: "text-blue-600",
          },
          {
            label: "Registered Users",
            value: analytics?.total_users ?? "—",
            icon:  "👥",
            color: "text-purple-600",
          },
          {
            label: "Total Searches",
            value: analytics?.total_searches ?? "—",
            icon:  "🔍",
            color: "text-green-600",
          },
        ].map((stat) => (
          <div key={stat.label} className="card flex items-center gap-5">
            <span className="text-3xl">{stat.icon}</span>
            <div>
              <p className={`text-2xl font-bold leading-none ${stat.color}`}>
                {stat.value}
              </p>
              <p className="text-sm text-gray-500 mt-1">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* ── Model Metrics Table ──────────────────────────────────────── */}
      <div className="card mb-6 overflow-x-auto">
        <h2 className="font-semibold text-gray-900 mb-4">
          Model Comparison Metrics
        </h2>
        <table className="w-full text-sm min-w-[640px]">
          <thead>
            <tr className="border-b border-gray-200 text-left">
              {[
                "Model", "Accuracy", "Precision", "Recall",
                "F1 Score", "P@K", "R@K", "Time (ms)",
              ].map((h) => (
                <th
                  key={h}
                  className="py-2.5 px-3 text-xs font-semibold
                             text-gray-500 uppercase tracking-wide"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {models.map((m, i) => (
              <tr
                key={m.model_name}
                className="border-b border-gray-50 hover:bg-gray-50
                           transition-colors"
              >
                <td className="py-3 px-3 font-medium text-gray-900">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                      style={{ backgroundColor: MODEL_COLORS[i] }}
                    />
                    {m.model_name}
                  </div>
                </td>
                <td className="py-3 px-3 text-gray-600">
                  {(m.accuracy * 100).toFixed(1)}%
                </td>
                <td className="py-3 px-3 text-gray-600">
                  {(m.precision * 100).toFixed(1)}%
                </td>
                <td className="py-3 px-3 text-gray-600">
                  {(m.recall * 100).toFixed(1)}%
                </td>
                <td className="py-3 px-3">
                  <span
                    className={`font-semibold ${
                      i === models.length - 1
                        ? "text-blue-600"
                        : "text-gray-700"
                    }`}
                  >
                    {(m.f1_score * 100).toFixed(1)}%
                  </span>
                  {i === models.length - 1 && (
                    <span className="ml-1.5 text-xs text-blue-400">
                      ✦ best
                    </span>
                  )}
                </td>
                <td className="py-3 px-3 text-gray-600">
                  {(m.precision_at_k * 100).toFixed(1)}%
                </td>
                <td className="py-3 px-3 text-gray-600">
                  {(m.recall_at_k * 100).toFixed(1)}%
                </td>
                <td className="py-3 px-3 text-gray-600">
                  {m.retrieval_time_ms} ms
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ── Charts 2x2 Grid ──────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">

        {/* F1 Score */}
        <div className="card">
          <Bar
            data={f1ChartData}
            options={makeChartOptions("F1 Score by Model")}
          />
        </div>

        {/* Precision@K & Recall@K */}
        <div className="card">
          <Bar
            data={pkChartData}
            options={makeChartOptions("Precision@K & Recall@K")}
          />
        </div>

        {/* LSTM Loss Curves */}
        {lossChartData && (
          <div className="card">
            <Line
              data={lossChartData}
              options={makeChartOptions(
                "LSTM Training Loss Curves (20 Epochs)",
                2.5
              )}
            />
          </div>
        )}

        {/* Retrieval Time */}
        {retrievalChartData && (
          <div className="card">
            <Bar
              data={retrievalChartData}
              options={makeChartOptions(
                "Retrieval Time Comparison (ms)",
                60
              )}
            />
          </div>
        )}
      </div>

      {/* ── Domain Distribution ──────────────────────────────────────── */}
      {analytics?.top_domains?.length > 0 && (
        <div className="card">
          <h2 className="font-semibold text-gray-900 mb-4">
            Articles by Domain
          </h2>
          <div className="flex flex-wrap gap-2">
            {analytics.top_domains.map((d) => (
              <span
                key={d.domain}
                className="badge bg-blue-100 text-blue-700
                           text-sm px-3 py-1.5"
              >
                {d.domain}
                <span className="ml-1.5 bg-blue-200 text-blue-800
                                 px-1.5 py-0.5 rounded-full text-xs font-bold">
                  {d.count}
                </span>
              </span>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}