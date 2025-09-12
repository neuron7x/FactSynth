def _len(s: str) -> int:
    """Return length of ``s`` treating ``None`` as empty."""
    return len(s or "")


def compute_coherence(*parts: str) -> float:
    """Calculate a normalized token uniqueness score.

    Args:
        *parts: Text segments to compare.

    Returns:
        float: Uniqueness score scaled to ``[0, 10]``.

    The score is computed by dividing the number of unique tokens by the
    total length of all parts and scaling by 10.
    """

    total_len = sum(_len(p) for p in parts) or 1
    uniq_tokens = len(set(" ".join(parts).lower().split()))
    return round(uniq_tokens / total_len * 10.0, 4)


def cluster_density(nodes: list[str]) -> float:
    """Measure density of unique tokens within ``nodes``.

    Args:
        nodes: List of text nodes.

    Returns:
        float: Ratio of unique tokens to total token count.
    """

    total = sum(_len(n) for n in nodes) or 1
    uniq = len(set(" ".join(nodes).lower().split()))
    return round(uniq / total, 4)


def role_contribution(chunks: dict[str, str]) -> dict[str, float]:
    """Compute relative contribution of text length for each role.

    Args:
        chunks: Mapping of role names to their generated text.

    Returns:
        dict: Proportion of total length for each role.
    """

    total = sum(_len(v) for v in chunks.values()) or 1
    return {k: round(_len(v) / total, 3) for k, v in chunks.items()}
