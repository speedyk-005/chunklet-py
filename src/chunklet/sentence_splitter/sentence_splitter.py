import warnings

# Suppress pkg_resources deprecation warnings from third-party libraries
warnings.filterwarnings("ignore", message=".*pkg_resources.*", category=UserWarning)

from os import getenv
from pathlib import Path
from typing import Callable

import regex as re
from loguru import logger
from py3langid.langid import MODEL_FILE, LanguageIdentifier

# pysbd, sentsplit, indicnlp and sentencex are lazy imported
from chunklet.common.deprecation import deprecated_callable
from chunklet.common.logging_utils import log_info
from chunklet.common.path_utils import read_text_file
from chunklet.common.validation import validate_input
from chunklet.exceptions import BlingfireMissingError
from chunklet.sentence_splitter._universal_splitter import UniversalSplitter
from chunklet.sentence_splitter.languages import (
    INDIC_NLP_UNIQUE_LANGUAGES,
    PYSBD_SUPPORTED_LANGUAGES,
    SENTENCEX_UNIQUE_LANGUAGES,
    SENTSPLIT_UNIQUE_LANGUAGES,
)
from chunklet.sentence_splitter.registry import custom_splitter_registry

# To identify strings consisting solely of punctuation or symbols.
PUNCTUATION_ONLY_PATTERN = re.compile(r"[\p{P}\p{S}]+")

# To identify thematic breaks (e.g., '---', '***', '___')
THEMATIC_BREAK_PATTERN = re.compile(r"^\s*[\-\*_]{2,}\s*$")


class BaseSplitter:
    """
    Base class for sentence splitting.
    Defines the interface that all splitter implementations must adhere to.
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Compare against BaseSplitter (the class that actually owns the defaults)
        is_split_overridden = cls.split is not BaseSplitter.split
        is_split_text_overridden = cls.split_text is not BaseSplitter.split_text

        if is_split_overridden and not is_split_text_overridden:
            warnings.warn(
                f"Class '{cls.__name__}' overrides 'split', which is deprecated. "
                f"Please migrate to overriding 'split_text' instead.",
                DeprecationWarning,
                stacklevel=2,
            )

    def split_text(self, text: str, lang: str = "auto") -> list[str]:
        """Splits the given text into a list of sentences.

        Args:
            text (str): The input text to be split.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto').

        Returns:
            list[str]: A list of sentences extracted from the text.
        """
        raise NotImplementedError("Subclasses must implement 'split_text'.")

    @deprecated_callable(
        use_instead="split_text", deprecated_in="2.2.0", removed_in="3.0.0"
    )
    def split(self, text: str, lang: str = "auto") -> list[str]:  # pragma: no cover
        """
        Split text into sentences.

        Note:
            Deprecated since 2.2.0. Will be removed in 3.0.0. Use `split_text` instead.
        """
        return self.split_text(text, lang)


class SentenceSplitter(BaseSplitter):
    """
    A robust and versatile utility dedicated to precisely segmenting text into individual sentences.

    Key Features:
    - Multilingual Support: Leverages language-specific algorithms and detection for broad coverage.
    - Custom Splitters: Uses centralized registry for custom splitting logic.
    - Fallback Mechanism: Employs a universal rule-based splitter for unsupported languages.
    - Robust Error Handling: Provides clear error reporting for issues with custom splitters.
    - Intelligent Post-processing: Cleans up split sentences by filtering empty strings and rejoining stray punctuation.
    """

    @validate_input
    def __init__(self, verbose: bool = False):
        """
        Initializes the SentenceSplitter.

        Args:
            verbose (bool, optional): If True, enables verbose logging for debugging and informational messages.
        """
        self.verbose = verbose
        self.fallback_splitter = UniversalSplitter()

        # Create a normalized identifier for language detection
        self.identifier = LanguageIdentifier.from_pickled_model(
            MODEL_FILE, norm_probs=True
        )

    def _get_special_lang_handler(self, lang: str) -> Callable | None:  # pragma: no cover
        if lang in PYSBD_SUPPORTED_LANGUAGES:
            from pysbd import Segmenter
            log_info(self.verbose, "Using pysbd")
            return Segmenter(lang).segment
        elif lang in SENTSPLIT_UNIQUE_LANGUAGES:
            from sentsplit.segment import SentSplit
            log_info(self.verbose, "Using sentsplit")
            return SentSplit(lang).segment
        elif lang in INDIC_NLP_UNIQUE_LANGUAGES:
            from indicnlp.tokenize import sentence_tokenize
            log_info(self.verbose, "Using indicnlp")
            return lambda text: sentence_tokenize.sentence_split(text, lang)
        elif lang in SENTENCEX_UNIQUE_LANGUAGES:
            from sentencex import segment
            log_info(self.verbose, "Using sentencex")
            return lambda text: segment(lang, text)

        return None

    def _clean_sentences(self, sentences: list[str]) -> list[str]:
        """
        Filtering empty strings and rejoining stray punctuation.

        Args:
            sentences (list[str]): Raw list of split sentences.

        Returns:
            list[str]: Cleaned list of sentences with proper punctuation handling.
        """
        processed_sentences = []
        for sent in sentences:
            stripped_sent = sent.strip()
            if stripped_sent:
                if PUNCTUATION_ONLY_PATTERN.fullmatch(
                    stripped_sent
                ) and not THEMATIC_BREAK_PATTERN.match(stripped_sent):
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
            text (str): The input text to detect the language for.

        Returns:
            tuple[str, float]: A tuple containing the detected language code and its confidence.
        """
        lang_detected, confidence = self.identifier.classify(text)
        log_info(
            self.verbose,
            "Language detection: '{}' with confidence {}.",
            lang_detected,
            f"{round(confidence) * 10}/10",
        )
        return lang_detected, confidence

    @validate_input
    def split_text(self, text: str, lang: str = "auto") -> list[str]:
        """
        Splits a given text into a list of sentences.

        Args:
            text (str): The input text to be split.
            lang (str, optional): The language of the text (e.g., 'en', 'fr'). Defaults to 'auto'

        Returns:
            list[str]: A list of sentences.

        Examples:
            >>> splitter = SentenceSplitter()
            >>> splitter.split_text("Hello world. How are you?", "en")
            ['Hello world.', 'How are you?']
            >>> splitter.split_text("Bonjour le monde. Comment allez-vous?", "fr")
            ['Bonjour le monde.', 'Comment allez-vous?']
            >>> splitter.split_text("Hello world. How are you?", "auto")
            ['Hello world.', 'How are you?']
        """
        if not text:
            log_info(self.verbose, "Input text is empty. Returning empty list.")
            return []

        if lang == "auto" and getenv("USE_BLINGFIRE") == "1":  # pragma: no cover
            log_info(self.verbose, "🔥 Using blingfire")
            try:
                from blingfire import text_to_sentences
                # detected sentences are separate by newlines
                sentences = text_to_sentences(text).split("\n")
            except ImportError:
                raise BlingfireMissingError() from None
        else:
            if lang == "auto":
                logger.warning(
                    "The language is set to `auto`. Consider setting the `lang` parameter "
                    "to a specific language to improve reliability."
                )
                lang_detected, confidence = self.detected_top_language(text)
                lang = lang_detected if confidence >= 0.7 else "any"

            sentences = None
            if lang != "fallback":
                # Prioritize custom splitters from registry
                if custom_splitter_registry.is_registered(lang):
                    sentences, splitter_name = custom_splitter_registry.split(text, lang)
                    log_info(self.verbose, "Using registered splitter: {}", splitter_name)
                elif (handler := self._get_special_lang_handler(lang)) is not None:
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

    def split_file(self, path: str | Path, lang: str = "auto") -> list[str]:
        """
        Read and split a file into sentences.

        Args:
            path (str | Path): Path to the file to read.
            lang (str, optional): The language of the text (e.g., 'en', 'fr', 'auto'). Defaults to 'auto'.

        Returns:
            list[str]: A list of sentences extracted from the file.
        """
        content = read_text_file(path)
        return self.split_text(content, lang)
