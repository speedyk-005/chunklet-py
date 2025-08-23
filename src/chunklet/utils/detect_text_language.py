import math
import py3langid
from typing import Tuple


def detect_text_language(text: str) -> Tuple[str, float]:
    """
    Classify the input text using py3langid and return the top language
    with its normalized probability.

    Notes:
        - Uses log-sum-exp trick for numerical stability.
        - Ranking is trimmed to the top 10 candidates.

    Parameters:
        text (str): The text to classify.

    Returns:
        Tuple[str, float]: The top language code and its normalized probability.
    """
    if not isinstance(text, str):
        raise TypeError("Input 'text' must be a string.")
    ranked = py3langid.rank(text)  # List of (lang, log_prob)
    if not ranked:
        return "unknown", 0.0

    # Trim to top 10 for focus
    ranked = ranked[:10]

    # log-sum-exp trick
    max_lp = max(lp for _, lp in ranked)
    probs = [math.exp(lp - max_lp) for _, lp in ranked]
    total = sum(probs)

    if total == 0:
        return ranked[0][0], 0.0

    norm_probs = [p / total for p in probs]
    top_lang, _ = ranked[0]
    top_prob = norm_probs[0]

    return top_lang, top_prob
