from typing import Callable

# Lazy global cache for the py3langid LanguageIdentifier.
_lang_identifier: Callable | None = None


def detect_top_language(text: str) -> tuple[str, float]:
    """Detect the top language of the given text using py3langid.

    The LanguageIdentifier is built lazily on first use and cached for reuse.

    Args:
        text: The input text to detect the language for.

    Returns:
        A tuple of the ISO 639-1 language code and its confidence in ``[0, 1]``.
        Confidence depends on the ``py3langid`` model, so treat it as
        approximate rather than a threshold you can rely on across versions.

    Raises:
        ImportError: If py3langid is not installed.

    Examples:
        >>> lang, confidence = detect_top_language("This sentence is written in English.")
        >>> lang, confidence > 0.8
        ('en', True)
        >>> detect_top_language("Ceci est une phrase ecrite en francais.")[0]
        'fr'
        >>> code, confidence = detect_top_language("")
        >>> round(confidence, 2)
        0.01
    """
    global _lang_identifier
    if _lang_identifier is None:
        try:
            from py3langid.langid import MODEL_FILE, LanguageIdentifier

            _lang_identifier = LanguageIdentifier.from_model_file(
                MODEL_FILE, norm_probs=True
            )
        except ImportError as e:  # pragma: no cover
            raise ImportError(
                "The 'py3langid' library is required for auto language detection. "
                "Please install it with 'pip install 'py3langid>=0.4.0,<0.5.0'' "
                "or install the lang-detect extra with 'pip install 'chunklet-py[lang-detect]''"
            ) from e

    return _lang_identifier.classify(text)
