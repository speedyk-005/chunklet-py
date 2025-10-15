from abc import ABC, abstractmethod
import regex as re
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
from chunklet.sentence_splitter.registry import use_registered_splitter, is_registered
from chunklet.sentence_splitter._fallback_splitter import FallbackSplitter
from chunklet.utils.detect_text_language import detect_text_language
from chunklet.utils.validation import validate_input
from chunklet.exceptions import InvalidInputError


class BaseSplitter(ABC):
    """
    Abstract base class for sentence splitting.
    Defines the interface that all sentence splitter implementations must adhere to.
    """

    @abstractmethod
    def split(self, text: str) -> list[str]:
        """
        Splits the given text into a list of sentences.

        Args:
            text (str): The input text to be segmented.
            s
        Returns:
            list[str]: A list of sentences extracted from the text.
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

    def __init__(self, verbose: bool = True):
        """
        Initializes the SentenceSplitter.

        Args:
            verbose (bool): If True, enables verbose logging for debugging and informational messages.
        """
        if not isinstance(verbose, bool):
            raise InvalidInputError("The 'verbose' flag must be a boolean value.")

        self.verbose = verbose
        self.fallback_splitter = FallbackSplitter()

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
                if re.fullmatch(r"[\p{P}\p{S}]+", stripped_sent):
                    if (
                        processed_sentences
                    ):  # Ensure there's a previous sentence to append to
                        processed_sentences[-1] += stripped_sent[
                            :5
                        ]  # Limits to the first 5 ones
                    else:  # If no previous sentence, just add it
                        processed_sentences.append(stripped_sent[:2])
                else:
                    processed_sentences.append(sent.rstrip())  # Use sent.rstrip() here
        return processed_sentences

    @validate_input
    def split(self, text: str, lang: str) -> list[str]:
        """
        Splits text into sentences using language-specific algorithms.
        Automatically detects language and prioritizes specialized libraries,
        falling back to a universal rule-based splitter for broad coverage.

        Args:
            text (str): The input text to split.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto').

        Returns:
            list[str]: A list of sentences.
        """
        sentences = []

        if lang == "auto":
            lang_detected, confidence = detect_text_language(text)
            if self.verbose:
                logger.info(
                    "Language detection: '{}' with confidence {}",
                    lang_detected,
                    f"{round(confidence)  * 10}/10",
                )
            lang = lang_detected if confidence >= 0.7 else lang

        # Prioritize custom splitters from registry
        if is_registered(lang):
            if self.verbose:
                logger.info("Using registered splitter for {}", lang)
            sentences, splitter_name = use_registered_splitter(text, lang)
            if self.verbose:
                logger.info("Using registered splitter: {}", splitter_name)

        elif lang in PYSBD_SUPPORTED_LANGUAGES:
            if self.verbose:
                logger.info("Using pysbd splitter")
            sentences = Segmenter(language=lang).segment(text)

        elif lang in SENTSPLIT_UNIQUE_LANGUAGES:
            if self.verbose:
                logger.info("Using sentsplit splitter")
            sentences = SentSplit(lang).segment(text)

        elif lang in INDIC_NLP_UNIQUE_LANGUAGES:
            if self.verbose:
                logger.info("Using indic-nlp-library splitter")
            sentences = sentence_tokenize.sentence_split(text, lang)

        elif lang in SENTENCEX_UNIQUE_LANGUAGES:
            if self.verbose:
                logger.info("Using sentencex splitter")
            sentences = segment(lang, text)

        else:  # Fallback to universal rule-based splitter
            if self.verbose:
                logger.info("Using a universal rule-based splitter")
                sentences = self.fallback_splitter.split(text)

        # Apply post-processing filter
        processed_sentences = self._filter_sentences(sentences)

        if self.verbose:
            logger.info(
                "Text splitted into sentences. Total sentences detected: {}",
                len(processed_sentences),
            )

        return processed_sentences
