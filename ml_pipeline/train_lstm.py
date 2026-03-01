"""
BiLSTM Text Classifier — Training Script.

Architecture:
    Embedding (vocab_size → 128)
        → BiLSTM (128 → 512, 2 layers, bidirectional)
        → Mean Pooling
        → Dropout(0.3)
        → Linear (512 → num_classes)

Training:
    - Dataset  : 20 Newsgroups (8 categories)
    - Optimizer: Adam (lr=3e-4)
    - Scheduler: StepLR (step=5, gamma=0.5)
    - Loss      : CrossEntropyLoss
    - Epochs    : 20

Usage:
    cd ml_pipeline
    python train_lstm.py

Outputs:
    models/saved_models/lstm_classifier.pt
    models/saved_models/lstm_vocab.pkl
    models/saved_models/lstm_evaluation.json
"""

import json
import pickle
import time
from collections import Counter
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.datasets import fetch_20newsgroups
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset

# ── Config ────────────────────────────────────────────────────────────────────

SAVE_DIR   = Path("models/saved_models")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

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

# Model hyperparameters
VOCAB_SIZE  = 20_000
MAX_LEN     = 300
EMBED_DIM   = 128
HIDDEN_DIM  = 256
NUM_LAYERS  = 2
DROPOUT     = 0.3

# Training hyperparameters
BATCH_SIZE  = 64
EPOCHS      = 20
LR          = 3e-4
WEIGHT_DECAY = 1e-4

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# ── Vocabulary ────────────────────────────────────────────────────────────────

def build_vocab(texts: list[str], max_size: int = VOCAB_SIZE) -> dict[str, int]:
    """
    Build a word-level vocabulary from a list of texts.

    Special tokens:
        0 → <PAD>  (padding)
        1 → <UNK>  (unknown words)

    Args:
        texts:    List of raw text strings.
        max_size: Maximum vocabulary size (including special tokens).

    Returns:
        Dict mapping word → integer index.
    """
    counter = Counter(
        word
        for text in texts
        for word in text.lower().split()
    )
    vocab = {"<PAD>": 0, "<UNK>": 1}
    for word, _ in counter.most_common(max_size - 2):
        vocab[word] = len(vocab)
    return vocab


def encode_text(
    text: str,
    vocab: dict[str, int],
    max_len: int = MAX_LEN,
) -> list[int]:
    """
    Convert a text string to a fixed-length list of token IDs.

    Truncates to max_len, pads with 0 if shorter.

    Args:
        text:    Raw text string.
        vocab:   Word-to-index mapping.
        max_len: Fixed output sequence length.

    Returns:
        List of integer token IDs of length max_len.
    """
    tokens = text.lower().split()[:max_len]
    ids    = [vocab.get(w, 1) for w in tokens]   # 1 = <UNK>
    ids   += [0] * (max_len - len(ids))            # 0 = <PAD>
    return ids


# ── Dataset ───────────────────────────────────────────────────────────────────

class TextDataset(Dataset):
    """
    PyTorch Dataset wrapping encoded text + label pairs.
    """

    def __init__(
        self,
        encodings: list[list[int]],
        labels: list[int],
    ) -> None:
        self.x = torch.tensor(encodings, dtype=torch.long)
        self.y = torch.tensor(labels,    dtype=torch.long)

    def __len__(self) -> int:
        return len(self.y)

    def __getitem__(self, idx: int):
        return self.x[idx], self.y[idx]


# ── Model ─────────────────────────────────────────────────────────────────────

class BiLSTMClassifier(nn.Module):
    """
    Bidirectional LSTM text classifier.

    Input : (batch_size, seq_len) token ID tensors
    Output: (batch_size, num_classes) logits
    """

    def __init__(
        self,
        vocab_size:  int,
        embed_dim:   int = EMBED_DIM,
        hidden_dim:  int = HIDDEN_DIM,
        num_layers:  int = NUM_LAYERS,
        num_classes: int = 8,
        dropout:     float = DROPOUT,
    ) -> None:
        super().__init__()

        self.embedding = nn.Embedding(
            vocab_size, embed_dim, padding_idx=0
        )
        self.lstm = nn.LSTM(
            input_size  = embed_dim,
            hidden_size = hidden_dim,
            num_layers  = num_layers,
            batch_first = True,
            bidirectional = True,
            dropout = dropout if num_layers > 1 else 0.0,
        )
        self.dropout = nn.Dropout(dropout)
        # BiLSTM output: hidden_dim * 2 (forward + backward)
        self.fc = nn.Linear(hidden_dim * 2, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        embedded  = self.dropout(self.embedding(x))  # (B, S, E)
        lstm_out, _ = self.lstm(embedded)             # (B, S, 2H)
        pooled    = lstm_out.mean(dim=1)              # (B, 2H)
        return self.fc(self.dropout(pooled))          # (B, C)


# ── Training helpers ──────────────────────────────────────────────────────────

def run_epoch(
    model:     nn.Module,
    loader:    DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer | None,
    training:  bool = True,
) -> tuple[float, list, list]:
    """
    Run one epoch of training or evaluation.

    Args:
        model:     The BiLSTM model.
        loader:    DataLoader for this split.
        criterion: Loss function.
        optimizer: Optimizer (None during evaluation).
        training:  True for training, False for evaluation.

    Returns:
        Tuple of (avg_loss, predictions, true_labels).
    """
    model.train() if training else model.eval()

    total_loss = 0.0
    all_preds  = []
    all_labels = []

    ctx = torch.enable_grad() if training else torch.no_grad()

    with ctx:
        for x_batch, y_batch in loader:
            x_batch = x_batch.to(DEVICE)
            y_batch = y_batch.to(DEVICE)

            logits = model(x_batch)
            loss   = criterion(logits, y_batch)

            if training:
                optimizer.zero_grad()
                loss.backward()
                # Gradient clipping prevents exploding gradients in LSTM
                nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                optimizer.step()

            total_loss += loss.item() * len(y_batch)
            preds = logits.argmax(dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(y_batch.cpu().numpy())

    avg_loss = total_loss / len(loader.dataset)
    return avg_loss, all_preds, all_labels


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print(f"  BiLSTM Training  |  device={DEVICE}")
    print("=" * 65)

    # ── Load dataset ──────────────────────────────────────────────────────────
    print("\n[1/6] Loading 20 Newsgroups dataset...")
    data = fetch_20newsgroups(
        subset="all",
        categories=CATEGORIES,
        remove=("headers", "footers", "quotes"),
        random_state=42,
    )
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        data.data, data.target,
        test_size=0.2, random_state=42, stratify=data.target,
    )
    print(f"      Train: {len(X_train_raw)} | Test: {len(X_test_raw)}")

    # ── Build vocabulary ──────────────────────────────────────────────────────
    print("\n[2/6] Building vocabulary...")
    vocab = build_vocab(X_train_raw, max_size=VOCAB_SIZE)
    print(f"      Vocab size: {len(vocab)}")

    # ── Encode texts ──────────────────────────────────────────────────────────
    print("\n[3/6] Encoding texts...")
    X_train_enc = [encode_text(t, vocab) for t in X_train_raw]
    X_test_enc  = [encode_text(t, vocab) for t in X_test_raw]

    train_loader = DataLoader(
        TextDataset(X_train_enc, y_train),
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0,
    )
    test_loader = DataLoader(
        TextDataset(X_test_enc, y_test),
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0,
    )

    # ── Initialise model ──────────────────────────────────────────────────────
    print("\n[4/6] Initialising BiLSTM model...")
    num_classes = len(data.target_names)
    model = BiLSTMClassifier(
        vocab_size  = len(vocab),
        num_classes = num_classes,
    ).to(DEVICE)

    total_params = sum(p.numel() for p in model.parameters())
    print(f"      Parameters  : {total_params:,}")
    print(f"      Classes     : {num_classes}")

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(
        model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY
    )
    scheduler = torch.optim.lr_scheduler.StepLR(
        optimizer, step_size=5, gamma=0.5
    )

    # ── Training loop ─────────────────────────────────────────────────────────
    print(f"\n[5/6] Training for {EPOCHS} epochs...")
    print(f"      {'Epoch':<8} {'Train Loss':<14} {'Val Loss':<14} {'Val Acc':<12} {'LR'}")
    print(f"      {'-'*8} {'-'*14} {'-'*14} {'-'*12} {'-'*10}")

    history = {
        "train_loss": [],
        "val_loss":   [],
        "val_acc":    [],
    }

    best_f1   = 0.0
    best_epoch = 0

    for epoch in range(1, EPOCHS + 1):
        # Training pass
        tr_loss, _, _ = run_epoch(
            model, train_loader, criterion, optimizer, training=True
        )

        # Validation pass
        va_loss, va_preds, va_labels = run_epoch(
            model, test_loader, criterion, None, training=False
        )

        # Metrics
        va_acc = accuracy_score(va_labels, va_preds)
        va_f1  = f1_score(va_labels, va_preds, average="weighted", zero_division=0)
        current_lr = scheduler.get_last_lr()[0]

        # Scheduler step
        scheduler.step()

        # Track history
        history["train_loss"].append(round(tr_loss, 4))
        history["val_loss"].append(round(va_loss, 4))
        history["val_acc"].append(round(va_acc, 4))

        # Track best epoch
        if va_f1 > best_f1:
            best_f1    = va_f1
            best_epoch = epoch
            # Save best model weights
            torch.save(
                model.state_dict(),
                SAVE_DIR / "lstm_classifier_best.pt",
            )

        print(
            f"      {epoch:<8} "
            f"{tr_loss:<14.4f} "
            f"{va_loss:<14.4f} "
            f"{va_acc:<12.4f} "
            f"{current_lr:.2e}"
        )

    # ── Final evaluation ──────────────────────────────────────────────────────
    print(f"\n[6/6] Final evaluation (best epoch: {best_epoch})...")

    t_start = time.perf_counter()
    _, y_pred, y_true = run_epoch(
        model, test_loader, criterion, None, training=False
    )
    retrieval_ms = (time.perf_counter() - t_start) * 1000 / len(y_test)

    acc  = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, average="weighted", zero_division=0)
    rec  = recall_score(y_true, y_pred, average="weighted", zero_division=0)
    f1   = f1_score(y_true, y_pred, average="weighted", zero_division=0)

    print("\n" + "=" * 65)
    print("  RESULTS")
    print("=" * 65)
    print(f"  Accuracy      : {acc:.4f}  ({acc*100:.1f}%)")
    print(f"  Precision     : {prec:.4f}  ({prec*100:.1f}%)")
    print(f"  Recall        : {rec:.4f}  ({rec*100:.1f}%)")
    print(f"  F1 Score      : {f1:.4f}  ({f1*100:.1f}%)")
    print(f"  Best Epoch    : {best_epoch}/{EPOCHS}")
    print(f"  Avg Speed     : {retrieval_ms:.2f} ms/sample")
    print("=" * 65)

    # ── Save artefacts ────────────────────────────────────────────────────────

    # Final model weights
    torch.save(model.state_dict(), SAVE_DIR / "lstm_classifier.pt")
    print(f"\n  Model saved    : {SAVE_DIR}/lstm_classifier.pt")

    # Vocabulary
    with open(SAVE_DIR / "lstm_vocab.pkl", "wb") as f:
        pickle.dump(vocab, f)
    print(f"  Vocab saved    : {SAVE_DIR}/lstm_vocab.pkl")

    # Evaluation results + training history
    evaluation = {
        "model":           "BiLSTM",
        "dataset":         "20newsgroups",
        "categories":      CATEGORIES,
        "hyperparameters": {
            "vocab_size":  VOCAB_SIZE,
            "max_len":     MAX_LEN,
            "embed_dim":   EMBED_DIM,
            "hidden_dim":  HIDDEN_DIM,
            "num_layers":  NUM_LAYERS,
            "dropout":     DROPOUT,
            "batch_size":  BATCH_SIZE,
            "epochs":      EPOCHS,
            "lr":          LR,
        },
        "accuracy":        round(acc,  4),
        "precision":       round(prec, 4),
        "recall":          round(rec,  4),
        "f1_score":        round(f1,   4),
        "best_epoch":      best_epoch,
        "avg_retrieval_ms": round(retrieval_ms, 2),
        "history":         history,
    }

    eval_path = SAVE_DIR / "lstm_evaluation.json"
    with open(eval_path, "w") as f:
        json.dump(evaluation, f, indent=2)
    print(f"  Results saved  : {eval_path}")
    print("  Done!\n")


if __name__ == "__main__":
    main()