"""
Full Model Comparison: TF-IDF vs SBERT on 20 Newsgroups.

Evaluates both models on identical train/test splits and
produces a side-by-side comparison with confusion matrices.

Usage:
    cd ml_pipeline
    python evaluate_models.py

Outputs:
    models/saved_models/full_evaluation.json
    models/saved_models/cm_tfidf.png
    models/saved_models/cm_sbert.png
"""

import json
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")   # Non-interactive backend (no display required)
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sentence_transformers import SentenceTransformer

# ── Config ────────────────────────────────────────────────────────────────────

SAVE_DIR = Path("models/saved_models")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

CATEGORIES = [
    "rec.sport.hockey",
    "sci.space",
    "talk.politics.misc",
    "comp.graphics",
    "sci.med",
    "rec.autos",
]

K = 10   # Precision@K and Recall@K cutoff


# ── Metric helpers ────────────────────────────────────────────────────────────

def precision_at_k(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    k: int,
) -> float:
    top_k = np.argsort(y_scores, axis=1)[:, -k:]
    hits  = sum(y_true[i] in top_k[i] for i in range(len(y_true)))
    return hits / (len(y_true) * k)


def recall_at_k(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    k: int,
) -> float:
    top_k = np.argsort(y_scores, axis=1)[:, -k:]
    hits  = sum(y_true[i] in top_k[i] for i in range(len(y_true)))
    return hits / len(y_true)


# ── Confusion matrix plot ─────────────────────────────────────────────────────

def plot_confusion_matrix(
    y_true: list,
    y_pred: list,
    class_names: list[str],
    title: str,
    filename: str,
) -> None:
    """
    Generate and save a confusion matrix heatmap.

    Args:
        y_true:      True labels.
        y_pred:      Predicted labels.
        class_names: Display names for each class.
        title:       Plot title.
        filename:    Output filename (saved in SAVE_DIR).
    """
    cm = confusion_matrix(y_true, y_pred)

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names,
        ax=ax,
        linewidths=0.5,
    )

    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_ylabel("True Label", fontsize=11)
    ax.set_xlabel("Predicted Label", fontsize=11)
    ax.tick_params(axis="x", rotation=45)
    ax.tick_params(axis="y", rotation=0)

    plt.tight_layout()
    out_path = SAVE_DIR / filename
    plt.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close()

    print(f"      Confusion matrix saved: {out_path}")


# ── TF-IDF evaluation ─────────────────────────────────────────────────────────

def evaluate_tfidf(
    X_train: list,
    X_test:  list,
    y_train: list,
    y_test:  list,
    cat_names: list[str],
) -> dict:
    """
    Evaluate TF-IDF + Logistic Regression baseline.

    Returns:
        Dict of evaluation metrics.
    """
    print("\n  [1/2] TF-IDF + Logistic Regression")
    print("        Fitting TF-IDF vectoriser...")

    tfidf = TfidfVectorizer(
        max_features  = 20_000,
        sublinear_tf  = True,
        strip_accents = "unicode",
        analyzer      = "word",
        min_df        = 2,
    )
    X_train_tfidf = tfidf.fit_transform(X_train)
    X_test_tfidf  = tfidf.transform(X_test)

    print("        Training Logistic Regression...")
    clf = LogisticRegression(
        max_iter = 1000,
        C        = 1.0,
        solver   = "lbfgs",
        multi_class = "multinomial",
        random_state = 42,
        n_jobs = -1,
    )
    clf.fit(X_train_tfidf, y_train)

    print("        Evaluating...")
    t0       = time.perf_counter()
    y_pred   = clf.predict(X_test_tfidf)
    y_scores = clf.predict_proba(X_test_tfidf)
    rt_ms    = (time.perf_counter() - t0) * 1000 / len(y_test)

    acc    = accuracy_score(y_test, y_pred)
    prec   = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    rec    = recall_score(y_test, y_pred, average="weighted", zero_division=0)
    f1     = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    p_at_k = precision_at_k(np.array(y_test), y_scores, k=K)
    r_at_k = recall_at_k(np.array(y_test), y_scores, k=K)

    print(f"        Accuracy: {acc:.4f} | F1: {f1:.4f} | P@{K}: {p_at_k:.4f} | {rt_ms:.1f}ms")

    plot_confusion_matrix(
        y_test, y_pred, cat_names,
        title    = "TF-IDF + LogReg — Confusion Matrix",
        filename = "cm_tfidf.png",
    )

    return {
        "model_name":        "TF-IDF Baseline",
        "accuracy":          round(acc,    4),
        "precision":         round(prec,   4),
        "recall":            round(rec,    4),
        "f1_score":          round(f1,     4),
        f"precision_at_{K}": round(p_at_k, 4),
        f"recall_at_{K}":    round(r_at_k, 4),
        "retrieval_time_ms": round(rt_ms,  2),
    }


# ── SBERT evaluation ──────────────────────────────────────────────────────────

def evaluate_sbert(
    X_train: list,
    X_test:  list,
    y_train: list,
    y_test:  list,
    cat_names: list[str],
) -> dict:
    """
    Evaluate SBERT + Logistic Regression.

    Returns:
        Dict of evaluation metrics.
    """
    print("\n  [2/2] SBERT (all-MiniLM-L6-v2) + Logistic Regression")
    print("        Loading SBERT model...")

    model = SentenceTransformer("all-MiniLM-L6-v2")

    print("        Encoding training set...")
    X_train_emb = model.encode(
        X_train,
        batch_size=64,
        normalize_embeddings=True,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    print("        Encoding test set...")
    X_test_emb = model.encode(
        X_test,
        batch_size=64,
        normalize_embeddings=True,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    print("        Training Logistic Regression...")
    clf = LogisticRegression(
        max_iter    = 1000,
        C           = 1.0,
        solver      = "lbfgs",
        multi_class = "multinomial",
        random_state = 42,
        n_jobs      = -1,
    )
    clf.fit(X_train_emb, y_train)

    print("        Evaluating...")
    t0       = time.perf_counter()
    y_pred   = clf.predict(X_test_emb)
    y_scores = clf.predict_proba(X_test_emb)
    rt_ms    = (time.perf_counter() - t0) * 1000 / len(y_test)

    acc    = accuracy_score(y_test, y_pred)
    prec   = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    rec    = recall_score(y_test, y_pred, average="weighted", zero_division=0)
    f1     = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    p_at_k = precision_at_k(np.array(y_test), y_scores, k=K)
    r_at_k = recall_at_k(np.array(y_test), y_scores, k=K)

    print(f"        Accuracy: {acc:.4f} | F1: {f1:.4f} | P@{K}: {p_at_k:.4f} | {rt_ms:.1f}ms")

    plot_confusion_matrix(
        y_test, y_pred, cat_names,
        title    = "SBERT + LogReg — Confusion Matrix",
        filename = "cm_sbert.png",
    )

    return {
        "model_name":        "SBERT (all-MiniLM-L6-v2)",
        "accuracy":          round(acc,    4),
        "precision":         round(prec,   4),
        "recall":            round(rec,    4),
        "f1_score":          round(f1,     4),
        f"precision_at_{K}": round(p_at_k, 4),
        f"recall_at_{K}":    round(r_at_k, 4),
        "retrieval_time_ms": round(rt_ms,  2),
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("  Model Evaluation: TF-IDF vs SBERT")
    print("  Dataset: 20 Newsgroups")
    print("=" * 65)

    # ── Load dataset ──────────────────────────────────────────────────────────
    print("\n[1/3] Loading dataset...")
    data = fetch_20newsgroups(
        subset     = "all",
        categories = CATEGORIES,
        remove     = ("headers", "footers", "quotes"),
        random_state = 42,
    )

    # Short class names for confusion matrix axes
    cat_names = [n.split(".")[-1] for n in data.target_names]

    X_train, X_test, y_train, y_test = train_test_split(
        data.data,
        data.target,
        test_size    = 0.2,
        random_state = 42,
        stratify     = data.target,
    )
    print(f"      Train: {len(X_train)} | Test: {len(X_test)}")

    # ── Evaluate models ───────────────────────────────────────────────────────
    print("\n[2/3] Evaluating models...")

    tfidf_results = evaluate_tfidf(X_train, X_test, y_train, y_test, cat_names)
    sbert_results = evaluate_sbert(X_train, X_test, y_train, y_test, cat_names)

    # ── Print comparison ──────────────────────────────────────────────────────
    print("\n[3/3] Results comparison")
    print("=" * 65)
    print(f"  {'Metric':<22} {'TF-IDF':<15} {'SBERT'}")
    print(f"  {'-'*22} {'-'*15} {'-'*15}")

    metrics = ["accuracy", "precision", "recall", "f1_score",
               f"precision_at_{K}", f"recall_at_{K}", "retrieval_time_ms"]

    for metric in metrics:
        tfidf_val = tfidf_results.get(metric, "N/A")
        sbert_val = sbert_results.get(metric, "N/A")
        label     = metric.replace("_", " ").title()

        if isinstance(tfidf_val, float) and metric != "retrieval_time_ms":
            print(
                f"  {label:<22} "
                f"{tfidf_val:<15.4f} "
                f"{sbert_val:.4f}"
            )
        else:
            print(
                f"  {label:<22} "
                f"{str(tfidf_val):<15} "
                f"{sbert_val}"
            )

    print("=" * 65)

    # ── Save results ──────────────────────────────────────────────────────────
    all_results = {
        "dataset":    "20newsgroups",
        "categories": CATEGORIES,
        "k":          K,
        "models":     [tfidf_results, sbert_results],
    }

    out_path = SAVE_DIR / "full_evaluation.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n  Results saved to: {out_path}")
    print("  Done!\n")


if __name__ == "__main__":
    main()