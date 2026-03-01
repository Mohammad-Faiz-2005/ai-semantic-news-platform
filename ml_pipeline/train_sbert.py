"""
SBERT Evaluation on 20 Newsgroups Dataset.

Pipeline:
    1. Load 20 Newsgroups dataset (8 categories)
    2. Encode all texts with Sentence-BERT (all-MiniLM-L6-v2)
    3. Train a Logistic Regression classifier head on SBERT embeddings
    4. Evaluate on held-out test set
    5. Compute Precision@K and Recall@K
    6. Save results to JSON

Usage:
    cd ml_pipeline
    python train_sbert.py

Output:
    models/saved_models/sbert_evaluation.json
"""

import json
import time
from pathlib import Path

import numpy as np
from sklearn.datasets import fetch_20newsgroups
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sentence_transformers import SentenceTransformer

# ── Config ────────────────────────────────────────────────────────────────────

SAVE_DIR   = Path("models/saved_models")
MODEL_NAME = "all-MiniLM-L6-v2"
K          = 10   # Precision@K and Recall@K cutoff

CATEGORIES = [
    "rec.sport.hockey",
    "sci.space",
    "talk.politics.misc",
    "comp.graphics",
    "sci.med",
    "rec.autos",
    "talk.religion.misc",
    "sci.electronics",
]

SAVE_DIR.mkdir(parents=True, exist_ok=True)


# ── Metric helpers ────────────────────────────────────────────────────────────

def precision_at_k(y_true: np.ndarray, y_scores: np.ndarray, k: int) -> float:
    """
    Compute mean Precision@K across all test samples.

    For each sample, check if the true label appears in the
    top-K predicted classes (by probability score).
    """
    top_k_preds = np.argsort(y_scores, axis=1)[:, -k:]
    hits = sum(
        y_true[i] in top_k_preds[i]
        for i in range(len(y_true))
    )
    return hits / (len(y_true) * k)


def recall_at_k(y_true: np.ndarray, y_scores: np.ndarray, k: int) -> float:
    """
    Compute mean Recall@K across all test samples.

    For each sample, check if the true label appears in the
    top-K predicted classes.
    """
    top_k_preds = np.argsort(y_scores, axis=1)[:, -k:]
    hits = sum(
        y_true[i] in top_k_preds[i]
        for i in range(len(y_true))
    )
    return hits / len(y_true)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("  SBERT Evaluation — 20 Newsgroups")
    print("=" * 65)

    # ── Step 1: Load dataset ──────────────────────────────────────────────────
    print("\n[1/5] Loading 20 Newsgroups dataset...")
    data = fetch_20newsgroups(
        subset="all",
        categories=CATEGORIES,
        remove=("headers", "footers", "quotes"),
        random_state=42,
    )
    print(f"      Total samples : {len(data.data)}")
    print(f"      Categories    : {len(data.target_names)}")

    X_train, X_test, y_train, y_test = train_test_split(
        data.data,
        data.target,
        test_size=0.2,
        random_state=42,
        stratify=data.target,
    )
    print(f"      Train samples : {len(X_train)}")
    print(f"      Test samples  : {len(X_test)}")

    # ── Step 2: Load SBERT model ──────────────────────────────────────────────
    print(f"\n[2/5] Loading SBERT model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    print(f"      Embedding dim : {model.get_sentence_embedding_dimension()}")

    # ── Step 3: Encode texts ──────────────────────────────────────────────────
    print("\n[3/5] Encoding training texts...")
    t_enc_start = time.perf_counter()
    X_train_emb = model.encode(
        X_train,
        batch_size=64,
        normalize_embeddings=True,
        show_progress_bar=True,
        convert_to_numpy=True,
    )
    print(f"      Train encoding : {time.perf_counter() - t_enc_start:.1f}s")

    print("\n      Encoding test texts...")
    t_test_start = time.perf_counter()
    X_test_emb = model.encode(
        X_test,
        batch_size=64,
        normalize_embeddings=True,
        show_progress_bar=True,
        convert_to_numpy=True,
    )
    test_enc_time = time.perf_counter() - t_test_start
    avg_retrieval_ms = (test_enc_time * 1000) / len(X_test)
    print(f"      Test encoding  : {test_enc_time:.1f}s")
    print(f"      Avg per sample : {avg_retrieval_ms:.2f}ms")

    # ── Step 4: Train Logistic Regression head ────────────────────────────────
    print("\n[4/5] Training Logistic Regression classifier head...")
    clf = LogisticRegression(
        max_iter=1000,
        C=1.0,
        solver="lbfgs",
        multi_class="multinomial",
        random_state=42,
        n_jobs=-1,
    )
    t_clf = time.perf_counter()
    clf.fit(X_train_emb, y_train)
    print(f"      Training time  : {time.perf_counter() - t_clf:.1f}s")

    # ── Step 5: Evaluate ──────────────────────────────────────────────────────
    print("\n[5/5] Evaluating on test set...")
    y_pred   = clf.predict(X_test_emb)
    y_scores = clf.predict_proba(X_test_emb)

    acc   = accuracy_score(y_test, y_pred)
    prec  = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    rec   = recall_score(y_test, y_pred, average="weighted", zero_division=0)
    f1    = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    p_at_k = precision_at_k(np.array(y_test), y_scores, k=K)
    r_at_k = recall_at_k(np.array(y_test), y_scores, k=K)

    # ── Print results ─────────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  RESULTS")
    print("=" * 65)
    print(f"  Accuracy      : {acc:.4f}  ({acc*100:.1f}%)")
    print(f"  Precision     : {prec:.4f}  ({prec*100:.1f}%)")
    print(f"  Recall        : {rec:.4f}  ({rec*100:.1f}%)")
    print(f"  F1 Score      : {f1:.4f}  ({f1*100:.1f}%)")
    print(f"  Precision@{K}  : {p_at_k:.4f}  ({p_at_k*100:.1f}%)")
    print(f"  Recall@{K}    : {r_at_k:.4f}  ({r_at_k*100:.1f}%)")
    print(f"  Avg Speed     : {avg_retrieval_ms:.2f} ms/sample")
    print("=" * 65)

    print("\n  Per-class report:")
    print(classification_report(
        y_test, y_pred,
        target_names=data.target_names,
        zero_division=0,
    ))

    # ── Save results ──────────────────────────────────────────────────────────
    results = {
        "model":              MODEL_NAME,
        "dataset":            "20newsgroups",
        "categories":         CATEGORIES,
        "train_samples":      len(X_train),
        "test_samples":       len(X_test),
        "accuracy":           round(acc,   4),
        "precision":          round(prec,  4),
        "recall":             round(rec,   4),
        "f1_score":           round(f1,    4),
        f"precision_at_{K}":  round(p_at_k, 4),
        f"recall_at_{K}":     round(r_at_k, 4),
        "avg_retrieval_ms":   round(avg_retrieval_ms, 2),
    }

    out_path = SAVE_DIR / "sbert_evaluation.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n  Results saved to: {out_path}")
    print("  Done!\n")


if __name__ == "__main__":
    main()