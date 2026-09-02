import re
from functools import lru_cache
from pathlib import Path
from typing import Callable

from loguru import logger

# yasbd, indicnlp, sentencex and py3langid are lazy imported
from chunklet.common.logging_utils import log_info
from chunklet.common.path_utils import read_text_file
from chunklet.common.validation import validate_input
from chunklet.sentence_splitter._universal_splitter import UniversalSplitter
from chunklet.sentence_splitter.languages import (
    INDIC_NLP_UNIQUE_LANGUAGES,
    SENTENCEX_UNIQUE_LANGUAGES,
    YASBD_SUPPORTED_LANGUAGES,
)

# To identify strings consisting solely of punctuation or symbols.
PUNCTUATION_ONLY_PATTERN = re.compile(r"\W+")

# To identify thematic breaks (e.g., '---', '***', '___')
THEMATIC_BREAK_PATTERN = re.compile(r"\s*([-*_])\s*\1{2,}\s*")


class SentenceSplitter:
    """
    A robust and versatile utility dedicated to precisely segmenting text into individual sentences.

    Key Features:
    - Multilingual Support: Leverages language-specific algorithms and detection for broad coverage.
    - Fallback Mechanism: Employs a universal rule-based splitter for unsupported languages.
    - Intelligent Post-processing: Cleans up split sentences by filtering empty strings and rejoining stray punctuation.
    """

    @validate_input
    def __init__(
        self,
        lang: str,
        verbose: bool = False,
    ):
        """
        Initializes the SentenceSplitter.

        Args:
            lang: Language code (e.g., 'en', 'fr', 'auto').
            verbose: If True, enables verbose logging for debugging and informational messages.
        """
        self.verbose = verbose
        self.fallback_splitter = UniversalSplitter()

        # Create a normalized identifier for language detection
        try:
            from py3langid.langid import MODEL_FILE, LanguageIdentifier

            self._identifier = LanguageIdentifier.from_pickled_model(
                MODEL_FILE, norm_probs=True
            )
        except ImportError as e:  # pragma: no cover
            raise ImportError(
                "The 'py3langid' library is required for auto language detection. "
                "Please install it with 'pip install 'py3langid>=0.3.0'' "
                "or install the auto extra with 'pip install 'chunklet-py[auto]''"
            ) from e

        # Tracked to reduce log spamming about language detection
        self._last_lang_used = None

        self.lang = lang

    @staticmethod
    @lru_cache(maxsize=52)
    def _get_lang_handler(lang: str, verbose: bool) -> Callable | None:
        """
        Get language-specific sentence splitting handler.

        Args:
            lang: Language code (e.g., 'en', 'ja', 'hi').
            verbose: If True, logs which splitter library is being used.

        Returns:
            A callable that takes text (str) and returns list[str], or None if no
            special handler exists for the language.
        """
        if lang in YASBD_SUPPORTED_LANGUAGES:
            from yasbd.boundary_detector import BoundaryDetector

            log_info(verbose, "Using yasbd")
            return BoundaryDetector(lang=lang).segment

        elif lang in INDIC_NLP_UNIQUE_LANGUAGES:
            try:
                from indicnlp.tokenize import sentence_tokenize
            except ImportError as e:  # pragma: no cover
                raise ImportError(
                    "The 'indic-nlp-library' is not installed. "
                    "Please install it with 'pip install 'indic-nlp-library>=0.92,<1.0'' "
                    "or install the indic extra with 'pip install 'chunklet-py[indic]''"
                ) from e
            log_info(verbose, "Using indicnlp")
            return lambda text: sentence_tokenize.sentence_split(text, lang)

        elif lang in SENTENCEX_UNIQUE_LANGUAGES:
            from sentencex import segment

            log_info(verbose, "Using sentencex")
            return lambda text: segment(lang, text)

        return None

    def _clean_sentences(self, sentences: list[str]) -> list[str]:
        """
        Filtering empty strings and rejoining stray punctuation.

        Args:
            sentences: Raw list of split sentences.

        Returns:
            Cleaned list of sentences with proper punctuation handling.
        """
        processed_sentences = []
        for sent in sentences:
            stripped_sent = sent.strip()
            if stripped_sent:
                if PUNCTUATION_ONLY_PATTERN.fullmatch(
                    stripped_sent
                ) and not THEMATIC_BREAK_PATTERN.fullmatch(stripped_sent):
                    if len(processed_sentences) >= 1:
                        # Limits to the first 5 ones
                        processed_sentences[-1] += stripped_sent[:5]
                    else:
                        processed_sentences.append(stripped_sent[:2])
                else:
                    processed_sentences.append(sent.rstrip())
        return processed_sentences

    @validate_input
    def detected_top_language(self, text: str) -> tuple[str, float]:
        """
        Detects the top language of the given text using py3langid.

        Args:
            text: The input text to detect the language for.

        Returns:
            A tuple containing the detected language code and its confidence.
        """
        lang_detected, confidence = self._identifier.classify(text)
        log_info(
            self.verbose,
            "Language detection: '{}' with confidence {}.",
            lang_detected,
            f"{round(confidence) * 10}/10",
        )
        return lang_detected, confidence

    @validate_input
    def split_text(self, text: str) -> list[str]:
        """
        Splits a given text into a list of sentences.

        Args:
            text: The input text to be split.

        Returns:
            A list of sentences.

        Examples:
            >>> splitter = SentenceSplitter(lang="en")
            >>> splitter.split_text("Hello world. How are you?")
            ['Hello world.', 'How are you?']
            >>> splitter = SentenceSplitter(lang="fr")
            >>> splitter.split_text("Bonjour le monde. Comment allez-vous?")
            ['Bonjour le monde.', 'Comment allez-vous?']
            >>> splitter = SentenceSplitter(lang="auto")
            >>> splitter.split_text("Hello world. How are you?")
            ['Hello world.', 'How are you?']
        """
        lang = self.lang

        if not text:
            log_info(self.verbose, "Input text is empty. Returning empty list.")
            return []

        if lang == "auto":
            if self._last_lang_used is None:
                logger.warning(
                    "The language is set to `auto`. Consider setting the `lang` parameter "
                    "to a specific language to improve reliability."
                )
            lang_detected, confidence = self.detected_top_language(text)
            lang = lang_detected if confidence >= 0.7 else "fallback"

        self._last_lang_used = lang

        sentences = None
        if (
            lang != "fallback"
            and (handler := self._get_lang_handler(lang, self.verbose)) is not None
        ):
            sentences = handler(text)

        # If no handler found, use fallback
        if sentences is None:
            logger.warning(
                "Using a universal rule-based splitter.\n"
                "Reason: Language not supported or detected with low confidence."
            )
            sentences = self.fallback_splitter.split(text)

        cleaned_sentences = self._clean_sentences(sentences)
        log_info(
            self.verbose,
            "Text splitted into sentences. Total sentences detected: {}",
            len(cleaned_sentences),
        )
        return cleaned_sentences

    def split_file(self, path: str | Path) -> list[str]:
        """
        Read and split a file into sentences.

        Args:
            path: Path to the file to read.

        Returns:
            A list of sentences extracted from the file.
        """
        content = read_text_file(path)
        return self.split_text(content)
