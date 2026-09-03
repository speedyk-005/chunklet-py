from typing import Callable

# Lazy global cache for the py3langid LanguageIdentifier.
_lang_identifier: Callable | None = None


def detect_top_language(text: str) -> tuple[str, float]:
    """Detect the top language of the given text using py3langid.

    The LanguageIdentifier is built lazily on first use and cached for reuse.

    Args:
        text: The input text to detect the language for.

    Returns:
        A tuple containing the detected language code and its confidence.

    Raises:
        ImportError: If py3langid is not installed.
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
                "or install the auto extra with 'pip install 'chunklet-py[auto]''"
            ) from e

    return _lang_identifier.classify(text)
