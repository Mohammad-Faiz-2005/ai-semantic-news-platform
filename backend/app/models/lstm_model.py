"""
BiLSTM text classifier using PyTorch.

Used in the model comparison module as an alternative to SBERT.
Architecture: Embedding → BiLSTM → Mean Pooling → Linear → Softmax

The model is trained offline using ml_pipeline/train_lstm.py
and loaded from disk at runtime for inference/comparison.
"""

from __future__ import annotations

from pathlib import Path

import torch
import torch.nn as nn

from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Path where the trained model weights are saved
LSTM_MODEL_PATH = Path("ml_models/lstm_classifier.pt")
LSTM_VOCAB_PATH = Path("ml_models/lstm_vocab.pkl")


class LSTMClassifier(nn.Module):
    """
    Bi-directional LSTM text classifier.

    Architecture:
        Input (token IDs)
            │
            ▼
        Embedding Layer (vocab_size → embed_dim)
            │
            ▼
        Dropout
            │
            ▼
        BiLSTM (embed_dim → hidden_dim * 2)
            │
            ▼
        Mean Pooling over time steps
            │
            ▼
        Dropout
            │
            ▼
        Linear (hidden_dim * 2 → num_classes)
            │
            ▼
        Output logits
    """

    def __init__(
        self,
        vocab_size: int,
        embed_dim: int = 128,
        hidden_dim: int = 256,
        num_layers: int = 2,
        num_classes: int = 20,
        dropout: float = 0.3,
        padding_idx: int = 0,
    ) -> None:
        """
        Args:
            vocab_size:  Size of the token vocabulary.
            embed_dim:   Embedding vector dimension.
            hidden_dim:  LSTM hidden state dimension (per direction).
            num_layers:  Number of LSTM layers stacked.
            num_classes: Number of output categories.
            dropout:     Dropout probability (applied after embedding and pooling).
            padding_idx: Token index used for padding (ignored in embedding).
        """
        super().__init__()

        self.embedding = nn.Embedding(
            vocab_size,
            embed_dim,
            padding_idx=padding_idx,
        )

        self.lstm = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        self.dropout = nn.Dropout(dropout)

        # BiLSTM output dim = hidden_dim * 2 (forward + backward)
        self.fc = nn.Linear(hidden_dim * 2, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Token ID tensor of shape (batch_size, seq_len)

        Returns:
            Logit tensor of shape (batch_size, num_classes)
        """
        # (B, S) → (B, S, embed_dim)
        embedded = self.dropout(self.embedding(x))

        # (B, S, embed_dim) → (B, S, hidden_dim * 2)
        lstm_out, _ = self.lstm(embedded)

        # Mean pooling over sequence dimension: (B, S, 2H) → (B, 2H)
        pooled = lstm_out.mean(dim=1)

        # (B, 2H) → (B, num_classes)
        logits = self.fc(self.dropout(pooled))

        return logits


def load_lstm_model(
    vocab_size: int,
    num_classes: int = 20,
    device: str = "cpu",
) -> LSTMClassifier:
    """
    Load the trained LSTM model from disk.

    If no saved weights are found, returns a randomly initialised model
    (useful for testing the architecture without training).

    Args:
        vocab_size:  Must match the vocab used during training.
        num_classes: Must match the number of categories trained on.
        device:      Torch device string ("cpu" or "cuda").

    Returns:
        LSTMClassifier in eval mode on the specified device.
    """
    model = LSTMClassifier(
        vocab_size=vocab_size,
        num_classes=num_classes,
    )

    if LSTM_MODEL_PATH.exists():
        state_dict = torch.load(LSTM_MODEL_PATH, map_location=device)
        model.load_state_dict(state_dict)
        logger.info("LSTM model weights loaded from %s", LSTM_MODEL_PATH)
    else:
        logger.warning(
            "No saved LSTM weights found at %s. "
            "Using randomly initialised weights. "
            "Run ml_pipeline/train_lstm.py to train the model.",
            LSTM_MODEL_PATH,
        )

    model.eval()
    return model.to(device)