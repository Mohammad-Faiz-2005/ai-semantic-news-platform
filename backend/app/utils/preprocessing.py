"""
Text preprocessing utilities.

Used by:
    - EmbeddingService  → before SBERT encoding
    - RetrievalService  → before TF-IDF vectorisation
    - ML pipeline       → during dataset preparation

Design goals:
    - Light-touch cleaning that preserves semantic meaning
    - SBERT is robust to raw text, so we avoid aggressive normalisation
    - Truncation prevents exceeding model input limits
"""

import re
import string


def clean_text(text: str) -> str:
    """
    Apply light-touch text cleaning.

    Operations:
        1. Lowercase
        2. Remove URLs (http/https/www)
        3. Collapse newlines and tabs to single spaces
        4. Collapse multiple spaces to one
        5. Strip leading/trailing whitespace

    Args:
        text: Raw input string.

    Returns:
        Cleaned string.

    Example:
        >>> clean_text("Check out https://example.com for   MORE info!\n")
        "check out for more info!"
    """
    if not text:
        return ""

    # Lowercase
    text = text.lower()

    # Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", "", text)

    # Collapse whitespace characters (newlines, tabs, carriage returns)
    text = re.sub(r"[\r\n\t]+", " ", text)

    # Collapse multiple spaces
    text = re.sub(r" {2,}", " ", text)

    return text.strip()


def truncate_text(text: str, max_tokens: int = 512) -> str:
    """
    Truncate text to approximately max_tokens tokens.

    Uses a rough character-based approximation:
        1 token ≈ 4 characters (average for English text)

    This avoids exceeding Sentence-BERT's 512-token input limit,
    which would silently truncate or error depending on the model.

    Args:
        text:       Input string.
        max_tokens: Maximum approximate token count. Default 512.

    Returns:
        Truncated string (unchanged if within limit).
    """
    max_chars = max_tokens * 4
    if len(text) > max_chars:
        return text[:max_chars]
    return text


def preprocess_for_embedding(text: str) -> str:
    """
    Full preprocessing pipeline for embedding generation.

    Applies:
        1. clean_text()    → remove noise
        2. truncate_text() → enforce input length limit

    Args:
        text: Raw input string (article content or user query).

    Returns:
        Preprocessed string ready for SBERT encoding.
    """
    return truncate_text(clean_text(text))


def tokenize_simple(text: str) -> list[str]:
    """
    Simple whitespace tokenizer for TF-IDF and LSTM preprocessing.

    Operations:
        1. Clean text
        2. Remove punctuation
        3. Split on whitespace

    Args:
        text: Raw input string.

    Returns:
        List of lowercase word tokens.

    Example:
        >>> tokenize_simple("Hello, World! How are you?")
        ["hello", "world", "how", "are", "you"]
    """
    text = clean_text(text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    return [token for token in text.split() if token]


def combine_title_content(title: str, content: str) -> str:
    """
    Combine article title and content for embedding.

    The title is prepended with a period separator to help
    the model distinguish title importance from body text.

    Args:
        title:   Article title string.
        content: Article body text.

    Returns:
        Combined string: "<title>. <content>"
    """
    title = title.strip()
    content = content.strip()

    if title and content:
        return f"{title}. {content}"
    return title or content