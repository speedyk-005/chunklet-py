from abc import ABC, abstractmethod
import regex as re
from py3langid.langid import LanguageIdentifier, MODEL_FILE
from pysbd import Segmenter
from sentsplit.segment import SentSplit
from sentencex import segment
from indicnlp.tokenize import sentence_tokenize
from loguru import logger

from chunklet.sentence_splitter.languages import (
    PYSBD_SUPPORTED_LANGUAGES,
    SENTSPLIT_UNIQUE_LANGUAGES,
    SENTENCEX_UNIQUE_LANGUAGES,
    INDIC_NLP_UNIQUE_LANGUAGES,
)
from chunklet.sentence_splitter.registry import CustomSplitterRegistry
from chunklet.sentence_splitter._fallback_splitter import FallbackSplitter
from chunklet.common.validation import validate_input


# Regex pattern to identify strings consisting solely of punctuation or symbols.
PUNCTUATION_ONLY_PATTERN = re.compile(r"[\p{P}\p{S}]+")

# Regex pattern to identify thematic breaks (e.g., '---', '***', '___')
THEMATIC_BREAK_PATTERN = re.compile(r"^\s*[\-\*_]{2,}\s*$")


class BaseSplitter(ABC):
    """
    Abstract base class for sentence splitting.
    Defines the interface that all sentence splitter implementations must adhere to.
    """

    @abstractmethod
    def split(self, text: str, lang: str) -> list[str]:
        """
        Splits the given text into a list of sentences.

        text (str): The input text to be split.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto').

        Returns:
            list[str]: A list of sentences extracted from the text.

        Examples:
            >>> class MySplitter(BaseSplitter):
            ...     def split(self, text: str, lang: str) -> list[str]:
            ...         return text.split(".")
            >>> splitter = MySplitter()
            >>> splitter.split("Hello. World.", "en")
            ['Hello', ' World']
        """
        pass


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

    # Language handler mapping - each library chosen for specific linguistic capabilities
    LANGUAGE_HANDLERS = {
        frozenset(PYSBD_SUPPORTED_LANGUAGES): lambda lang, text: Segmenter(
            language=lang
        ).segment(text),
        frozenset(SENTSPLIT_UNIQUE_LANGUAGES): lambda lang, text: SentSplit(
            lang
        ).segment(text),
        frozenset(
            INDIC_NLP_UNIQUE_LANGUAGES
        ): lambda lang, text: sentence_tokenize.sentence_split(text, lang),
        frozenset(SENTENCEX_UNIQUE_LANGUAGES): lambda lang, text: segment(lang, text),
    }

    @validate_input
    def __init__(self, verbose: bool = False):
        """
        Initializes the SentenceSplitter.

        Args:
            verbose (bool, optional): If True, enables verbose logging for debugging and informational messages.
        """
        self.verbose = verbose
        self.custom_splitter_registry = CustomSplitterRegistry()
        self.fallback_splitter = FallbackSplitter()

        # Create a normalized identifier for langid
        self.identifier = LanguageIdentifier.from_pickled_model(
            MODEL_FILE, norm_probs=True
        )

    def _filter_sentences(self, sentences: list[str]) -> list[str]:
        """
        Post-processes split sentences by filtering empty strings and rejoining stray punctuation.

        Args:
            sentences (list[str]): Raw list of split sentences.

        Returns:
            list[str]: Cleaned list of sentences with proper punctuation handling.
        """
        processed_sentences = []
        for sent in sentences:
            stripped_sent = sent.strip()
            if stripped_sent:
                # If sentence is made of stray punctuation only
                if PUNCTUATION_ONLY_PATTERN.fullmatch(
                    stripped_sent
                ) and not THEMATIC_BREAK_PATTERN.match(stripped_sent):
                    if processed_sentences:
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
        if self.verbose:
            logger.info(
                "Language detection: '{}' with confidence {}.",
                lang_detected,
                f"{round(confidence) * 10}/10",
            )
        return lang_detected, confidence

    @validate_input
    def split(self, text: str, lang: str = "auto") -> list[str]:
        """
        Splits a given text into a list of sentences.

        Args:
            text (str): The input text to be split.
            lang (str, optional): The language of the text (e.g., 'en', 'fr'). Defaults to 'auto'

        Returns:
            list[str]: A list of sentences.

        Examples:
            >>> splitter = SentenceSplitter()
            >>> splitter.split("Hello world. How are you?", "en")
            ['Hello world.', 'How are you?']
            >>> splitter.split("Bonjour le monde. Comment allez-vous?", "fr")
            ['Bonjour le monde.', 'Comment allez-vous?']
            >>> splitter.split("Hello world. How are you?", "auto")
            ['Hello world.', 'How are you?']
        """
        if not text:
            if self.verbose:
                logger.info("Input text is empty. Returning empty list.")
            return []

        if lang == "auto":
            logger.warning(
                "The language is set to `auto`. Consider setting the `lang` parameter to a specific language to improve reliability."
            )
            lang_detected, confidence = self.detected_top_language(text)
            lang = lang_detected if confidence >= 0.7 else lang

        # Prioritize custom splitters from registry
        if self.custom_splitter_registry.is_registered(lang):
            sentences, splitter_name = self.custom_splitter_registry.split(text, lang)
            if self.verbose:
                logger.info("Using registered splitter: {}", splitter_name)
        else:
            # Find and use the appropriate handler
            sentences = None
            for lang_set, handler in self.LANGUAGE_HANDLERS.items():
                if lang in lang_set:
                    sentences = handler(lang, text)
                    break

            # If no handler found, use fallback
            if sentences is None:
                logger.warning(
                    "Using a universal rule-based splitter.\n"
                    "Reason: Language not supported or detected with low confidence."
                )
                sentences = self.fallback_splitter.split(text)

        # Apply post-processing filter
        processed_sentences = self._filter_sentences(sentences)

        if self.verbose:
            logger.info(
                "Text splitted into sentences. Total sentences detected: {}",
                len(processed_sentences),
            )

        return processed_sentences
