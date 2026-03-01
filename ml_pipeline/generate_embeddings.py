"""
Rebuild FAISS Index from Live Database.

Connects to the PostgreSQL database, fetches all articles,
generates SBERT embeddings in batch, builds a new FAISS index,
and saves it to disk.

Also updates the embedding_generated flag in the database.

Usage:
    cd ml_pipeline
    python generate_embeddings.py \
        --db-url postgresql://newsuser:newspassword@localhost:5432/newsdb

    # Optional flags:
    python generate_embeddings.py \
        --db-url postgresql://... \
        --batch-size 32 \
        --model all-MiniLM-L6-v2 \
        --output-dir ../vector_store
"""

import argparse
import pickle
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text

# ── Config ────────────────────────────────────────────────────────────────────

EMBEDDING_DIM  = 384
DEFAULT_MODEL  = "all-MiniLM-L6-v2"
DEFAULT_OUTDIR = Path("../vector_store")
DEFAULT_BATCH  = 64


# ── Helpers ───────────────────────────────────────────────────────────────────

def fetch_articles(db_url: str) -> list[tuple]:
    """
    Fetch all articles from the PostgreSQL database.

    Args:
        db_url: PostgreSQL DSN connection string.

    Returns:
        List of (id, title, content) tuples.
    """
    engine = create_engine(db_url, pool_pre_ping=True)
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, title, content FROM articles ORDER BY id")
        ).fetchall()
    print(f"  Fetched {len(rows)} articles from database.")
    return rows


def mark_embedded(db_url: str, article_ids: list[int]) -> None:
    """
    Set embedding_generated = TRUE for all processed articles.

    Args:
        db_url:       PostgreSQL DSN connection string.
        article_ids:  List of article IDs to update.
    """
    engine = create_engine(db_url)
    with engine.connect() as conn:
        conn.execute(
            text(
                "UPDATE articles "
                "SET embedding_generated = TRUE "
                "WHERE id = ANY(:ids)"
            ),
            {"ids": article_ids},
        )
        conn.commit()
    print(f"  Marked {len(article_ids)} articles as embedded.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # ── Argument parsing ──────────────────────────────────────────────────────
    parser = argparse.ArgumentParser(
        description="Rebuild FAISS index from PostgreSQL article database."
    )
    parser.add_argument(
        "--db-url",
        required=True,
        help="PostgreSQL DSN e.g. postgresql://user:pass@host/dbname",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH,
        help=f"SBERT encoding batch size (default: {DEFAULT_BATCH})",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Sentence-BERT model name (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTDIR),
        help=f"Output directory for FAISS files (default: {DEFAULT_OUTDIR})",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    index_path  = output_dir / "faiss_index.bin"
    id_map_path = output_dir / "id_mapping.pkl"

    print("=" * 65)
    print("  FAISS Index Builder")
    print("=" * 65)
    print(f"  DB URL     : {args.db_url[:40]}...")
    print(f"  Model      : {args.model}")
    print(f"  Batch size : {args.batch_size}")
    print(f"  Output dir : {output_dir}")
    print("=" * 65)

    # ── Step 1: Fetch articles ────────────────────────────────────────────────
    print("\n[1/4] Fetching articles from database...")
    rows = fetch_articles(args.db_url)

    if not rows:
        print("  No articles found. Exiting.")
        return

    article_ids = [row[0] for row in rows]
    texts       = [f"{row[1]}. {row[2]}" for row in rows]

    # ── Step 2: Generate embeddings ───────────────────────────────────────────
    print(f"\n[2/4] Loading SBERT model: {args.model}")
    model = SentenceTransformer(args.model)

    print(f"      Encoding {len(texts)} articles...")
    embeddings = model.encode(
        texts,
        batch_size          = args.batch_size,
        normalize_embeddings = True,
        show_progress_bar   = True,
        convert_to_numpy    = True,
    ).astype(np.float32)

    print(f"      Embeddings shape: {embeddings.shape}")

    # ── Step 3: Build FAISS index ─────────────────────────────────────────────
    print("\n[3/4] Building FAISS IndexFlatIP...")
    index = faiss.IndexFlatIP(EMBEDDING_DIM)
    index.add(embeddings)
    print(f"      Vectors in index: {index.ntotal}")

    # Save index
    faiss.write_index(index, str(index_path))
    print(f"      Index saved: {index_path}")

    # Save ID mapping
    with open(id_map_path, "wb") as f:
        pickle.dump(article_ids, f)
    print(f"      ID map saved: {id_map_path}")

    # ── Step 4: Update database ───────────────────────────────────────────────
    print("\n[4/4] Updating database embedding flags...")
    mark_embedded(args.db_url, article_ids)

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  Done!")
    print(f"  Articles indexed : {index.ntotal}")
    print(f"  Index file       : {index_path}")
    print(f"  ID mapping file  : {id_map_path}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()