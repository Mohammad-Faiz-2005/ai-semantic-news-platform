"""
Evaluation metric helpers for model comparison.

Implements:
    - Precision@K
    - Recall@K
    - Average Precision
    - Mean Average Precision (MAP)
    - build_metrics_dict() → standardised metrics dict for API responses

Used by:
    - backend/app/api/analytics.py  → returns metrics to dashboard
    - ml_pipeline/evaluate_models.py → offline evaluation
"""

from typing import List
import numpy as np


def precision_at_k(
    relevant: List[int],
    retrieved: List[int],
    k: int,
) -> float:
    """
    Compute Precision@K.

    Definition:
        P@K = |relevant ∩ top-K retrieved| / K

    Args:
        relevant:  List of ground-truth relevant item IDs.
        retrieved: List of retrieved item IDs (in rank order).
        k:         Cutoff rank.

    Returns:
        Float in [0.0, 1.0].
    """
    if k <= 0:
        return 0.0

    top_k = retrieved[:k]
    hits = len(set(top_k) & set(relevant))
    return hits / k


def recall_at_k(
    relevant: List[int],
    retrieved: List[int],
    k: int,
) -> float:
    """
    Compute Recall@K.

    Definition:
        R@K = |relevant ∩ top-K retrieved| / |relevant|

    Args:
        relevant:  List of ground-truth relevant item IDs.
        retrieved: List of retrieved item IDs (in rank order).
        k:         Cutoff rank.

    Returns:
        Float in [0.0, 1.0]. Returns 0.0 if relevant is empty.
    """
    if not relevant or k <= 0:
        return 0.0

    top_k = retrieved[:k]
    hits = len(set(top_k) & set(relevant))
    return hits / len(relevant)


def average_precision(
    relevant: List[int],
    retrieved: List[int],
) -> float:
    """
    Compute Average Precision (AP) for a single query.

    Definition:
        AP = (1/|R|) * Σ P@k * rel(k)
        where rel(k) = 1 if item at rank k is relevant, else 0

    Args:
        relevant:  List of ground-truth relevant item IDs.
        retrieved: List of retrieved item IDs (in rank order).

    Returns:
        Float in [0.0, 1.0]. Returns 0.0 if relevant is empty.
    """
    if not relevant:
        return 0.0

    hits = 0
    sum_precisions = 0.0

    for rank, item in enumerate(retrieved, start=1):
        if item in relevant:
            hits += 1
            sum_precisions += hits / rank

    return sum_precisions / len(relevant)


def mean_average_precision(
    queries_relevant: List[List[int]],
    queries_retrieved: List[List[int]],
) -> float:
    """
    Compute Mean Average Precision (MAP) across multiple queries.

    Definition:
        MAP = (1/|Q|) * Σ AP(q)

    Args:
        queries_relevant:  List of relevant ID lists, one per query.
        queries_retrieved: List of retrieved ID lists, one per query.

    Returns:
        Float in [0.0, 1.0]. Returns 0.0 if no queries provided.
    """
    if not queries_relevant:
        return 0.0

    aps = [
        average_precision(rel, ret)
        for rel, ret in zip(queries_relevant, queries_retrieved)
    ]
    return float(np.mean(aps))


def build_metrics_dict(
    model_name: str,
    accuracy: float,
    precision: float,
    recall: float,
    f1: float,
    p_at_k: float,
    r_at_k: float,
    retrieval_ms: float,
) -> dict:
    """
    Build a standardised metrics dictionary for API responses.

    All float values are rounded to 4 decimal places for consistency.

    Args:
        model_name:    Display name of the model.
        accuracy:      Classification accuracy (0.0 - 1.0).
        precision:     Weighted precision (0.0 - 1.0).
        recall:        Weighted recall (0.0 - 1.0).
        f1:            Weighted F1 score (0.0 - 1.0).
        p_at_k:        Precision@K (0.0 - 1.0).
        r_at_k:        Recall@K (0.0 - 1.0).
        retrieval_ms:  Average retrieval time in milliseconds.

    Returns:
        Dict matching the ModelMetrics Pydantic schema.
    """
    return {
        "model_name":       model_name,
        "accuracy":         round(accuracy, 4),
        "precision":        round(precision, 4),
        "recall":           round(recall, 4),
        "f1_score":         round(f1, 4),
        "precision_at_k":   round(p_at_k, 4),
        "recall_at_k":      round(r_at_k, 4),
        "retrieval_time_ms": round(retrieval_ms, 2),
    }