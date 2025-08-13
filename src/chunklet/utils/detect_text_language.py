import math
import py3langid

def detect_text_language(text: str) -> tuple[str, float]:
    """
    Classify the input text using py3langid and return the language
    with its normalized probability.

    This function converts log probabilities returned by py3langid.rank()
    to normalized probabilities.

    Parameters:
        text (str): The text to classify.

    Returns:
        tuple[str, float]: The top language code and its normalized probability.
    """
    ranked = py3langid.rank(text)  # List of (lang, log_prob)
    if not ranked:
        # No results; fallback
        return "unknown", 0.0

    probs = [math.exp(lp) for _, lp in ranked]  # Convert log prob → prob
    total = sum(probs)

    if total == 0:
        # Avoid division by zero if all probabilities are zero due to underflow
        return ranked[0][0], 0.0

    norm_probs = [p / total for p in probs]  # Normalize probabilities
    top_lang, _ = ranked[0]
    top_prob = norm_probs[0]
    return top_lang, top_prob