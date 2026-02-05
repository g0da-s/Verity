"""Claim normalization utilities for consistent cache keys."""

import re
import unicodedata


def normalize_claim(claim: str) -> str:
    """Normalize a health claim for use as a cache key.

    This ensures that semantically identical claims map to the same cache entry.

    Transformations:
    - Convert to lowercase
    - Normalize unicode characters
    - Remove punctuation (except hyphens in compound words)
    - Collapse multiple spaces
    - Strip leading/trailing whitespace

    Examples:
        >>> normalize_claim("Does creatine improve muscle strength?")
        'does creatine improve muscle strength'
        >>> normalize_claim("DOES   Creatine IMPROVE muscle-strength??")
        'does creatine improve muscle-strength'
    """
    # Normalize unicode (e.g., convert accented chars to ASCII equivalents)
    text = unicodedata.normalize("NFKD", claim)
    text = text.encode("ascii", "ignore").decode("ascii")

    # Convert to lowercase
    text = text.lower()

    # Remove punctuation except hyphens (preserve compound words like "muscle-strength")
    text = re.sub(r"[^\w\s-]", "", text)

    # Collapse multiple spaces into single space
    text = re.sub(r"\s+", " ", text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text
