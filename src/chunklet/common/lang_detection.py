from typing import Callable

# Lazy global cache for the py3langid LanguageIdentifier.
_lang_identifier: Callable | None = None


def _load_lang_identifier():
    """Load py3langid safely on Android/Pydroid3.

    NumPy expects the temporary file object to expose a valid `.name`
    attribute during model loading. Some Android runtimes provide a raw
    file descriptor instead, which breaks `numpy.load()` with:
    `AttributeError: 'int' object has no attribute 'endswith'`
    """
    import tempfile

    original_tempfile = tempfile.TemporaryFile
    try:
        def _patched_tempfile(*args, **kwargs):
            kwargs.setdefault("delete", False)
            return tempfile.NamedTemporaryFile(*args, **kwargs)

        tempfile.TemporaryFile = _patched_tempfile

        from py3langid.langid import MODEL_FILE, LanguageIdentifier
        return LanguageIdentifier.from_model_file(MODEL_FILE, norm_probs=True)
    finally:
        tempfile.TemporaryFile = original_tempfile


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
            _lang_identifier = _load_lang_identifier()
        except ImportError as e:  # pragma: no cover
            raise ImportError(
                "The 'py3langid' library is required for auto language detection. "
                "Please install it with 'pip install 'py3langid>=0.4.0,<0.5.0'' "
                "or install the lang-detect extra with 'pip install 'chunklet-py[lang-detect]''"
            ) from e

    return _lang_identifier.classify(text)
