from __future__ import annotations
from typing import List, Set, Dict
import regex as re
from pydantic import ValidationError
from pysbd import Segmenter
from sentsplit.segment import SentSplit
from sentencex import segment
from indicnlp.tokenize import sentence_tokenize

from chunklet.sentence_splitter.languages import (
    PYSBD_SUPPORTED_LANGUAGES,
    SENTSPLIT_UNIQUE_LANGUAGES,
    SENTENCEX_UNIQUE_LANGUAGES,
    INDIC_NLP_UNIQUE_LANGUAGES,
)
from chunklet.sentence_splitter.fallback_splitter import FallbackSplitter
from chunklet.utils.detect_text_language import detect_text_language
from chunklet.models import CustomSplitterConfig
from chunklet.utils.logger import logger
from chunklet.exceptions import InvalidInputError, CallbackExecutionError
from chunklet.utils.error_utils import pretty_errors


class SentenceSplitter:
    """
    A robust and versatile utility dedicated to precisely segmenting text into individual sentences.

    Key Features:
    - Multilingual Support: Leverages language-specific algorithms and detection for broad coverage.
    - Custom Splitters: Allows integration of user-defined splitting logic.
    - Fallback Mechanism: Employs a universal regex splitter for unsupported languages.
    - Robust Error Handling: Provides clear error reporting for issues with custom splitters.
    - Intelligent Post-processing: Cleans up split sentences by filtering empty strings and rejoining stray punctuation.
    """
    def __init__(
        self,
        custom_splitters: List[Dict] | None = None,
        verbose: bool = True
    ):
        """
        Initializes the SentenceSplitter.

        Args:
            custom_splitters (List[Dict] | None): A list of dictionaries, where each dictionary
                defines a custom sentence splitter. Each splitter dictionary must contain:
                - 'name' (str): A unique name for the splitter.
                - 'languages' (str or Iterable[str]): Language(s) supported by the splitter.
                - 'callback' (Callable[[str], List[str]]): A callable function that takes
                  a string and returns a list of strings (sentences).
            verbose (bool): If True, enables verbose logging for debugging and informational messages.
        """
        if not isinstance(verbose, bool):
            raise InvalidInputError("The 'verbose' flag must be a boolean value.")

        try:
            # Validate custom_splitters against the Pydantic model
            self._custom_splitters = (
                [CustomSplitterConfig(**splitter) for splitter in custom_splitters]
                if custom_splitters
                else None
            )
        except ValidationError as e:
            pretty_err = pretty_errors(e)
            raise InvalidInputError(
                f"Invalid custom_splitters configuration.\n Details: {pretty_err}"
            ) from e

        self.verbose = verbose
        self.fallback_splitter = FallbackSplitter()

        # Prepare a set of supported extensions from custom splitters
        self.custom_splitters_languages = set()
        if self._custom_splitters:
            for splitter in self._custom_splitters:
                if isinstance(splitter.languages, str):
                    self.custom_splitters_languages.add(splitter.languages)
                else:
                    self.custom_splitters_languages.update(set(splitter.languages))

    @property
    def custom_splitters(self) -> List[CustomSplitterConfig] | None:
        """
        Returns the list of custom splitter configurations.
        """
        return self._custom_splitters

    def _use_custom_splitter(self, text: str, lang: str) -> list[str]:
        """
        Processes a text using a custom splitter registered for the given language.

        Args:
            text (str): The text to split.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto').

        Returns:
            list[str]: A list of sentences.

        Raises:
             CallbackExecutionError: If a custom splitter fails during execution.
        """
        for splitter in self._custom_splitters:
            supported_languages = (
                [splitter.languages]
                if isinstance(splitter.languages, str)
                else splitter.languages
            )
            if lang in supported_languages:
                if self.verbose:
                    logger.debug(
                        "Using %s for language: %s. (Custom Splitter)",
                        splitter.name,
                        lang,
                    )
                    
                # Handle validation and error wrapping.
                try:
                    result = splitter.callback(text)
                except Exception as e:
                    raise CallbackExecutionError(
                        f"Custom splitter '{splitter.name}' callback failed for text starting with: '{text[:100]}...'.\n"
                        f"Details: {e}"
                    ) from e

                if not isinstance(result, list) or not all(isinstance(item, str) for item in result):
                    raise CallbackExecutionError(
                        f"Custom splitter '{splitter.name}' callback returned an invalid type. "
                        f"Expected a list of strings, but got {type(result)} with elements of mixed types."
                    )
                return result

    def split(
        self,
        text: str,
        lang: str,
        _return_warnings: bool = False
    ) -> list[str]:
        """
        Splits text into sentences using language-specific algorithms.
        Automatically detects language and prioritizes specialized libraries,
        falling back to a universal regex splitter for broad coverage.

        Args:
            text (str): The input text to split.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto').

        Returns:
            list[str]: A list of sentences.

        Raises:
             CallbackExecutionError: If a custom splitter fails during execution.
        """
        if not isinstance(text, str):
            raise InvalidInputError("The 'text' argument must be a string.")
        if not isinstance(lang, str):
            raise InvalidInputError("The 'lang' argument must be a string.")             
 
        warnings = set()
        sentences = []

        if lang == "auto":
            lang_detected, confidence = detect_text_language(text)
            if self.verbose:
                logger.debug("Attempting language detection.")
            if confidence < 0.7:
                warnings.add(
                    f"Low confidence in language detected. Detected: '{lang_detected}' with confidence {confidence:.2f}."
                )
            lang = lang_detected if confidence >= 0.7 else lang

        # Prioritize custom splitters
        if lang in self.custom_splitters_languages and self._custom_splitters:
            sentences = self._use_custom_splitter(text, lang)

        elif lang in PYSBD_SUPPORTED_LANGUAGES:
            if self.verbose:
                logger.debug("Using pysbd for language: %s.", lang)
            sentences = Segmenter(language=lang).segment(text)

        elif lang in SENTSPLIT_UNIQUE_LANGUAGES:
            if self.verbose:
                logger.debug(
                    "Using SentSplit for language: %s. (sentsplit)",
                    lang,
                )
            sentences = SentSplit(lang).segment(text)

        elif lang in INDIC_NLP_UNIQUE_LANGUAGES:
            if self.verbose:
                logger.debug(
                    "Using Indic NLP for language: %s. (indic-nlp-library)",
                    lang,
                )
            sentences = sentence_tokenize.sentence_split(text, lang)

        elif lang in SENTENCEX_UNIQUE_LANGUAGES:
            if self.verbose:
                logger.debug(
                    "Using Sentencex for language: %s. (sentencex)",
                    lang,
                )
            sentences = segment(lang, text)

        else:  # Fallback to universal regex splitter
            warnings.add(
                "Language not supported or detected with low confidence. Universal regex splitter was used."
            )
            if self.verbose:
                logger.debug("Using a universal regex splitter.")
            sentences = self.fallback_splitter.split(text)

        # Post-processing: Filters empty string and rejoin some left over punctuations.
        processed_sentences = []
        for sent in sentences: 
            stripped_sent = sent.strip()
            if stripped_sent:
                if re.fullmatch(r"[\p{P}\p{S}]+", stripped_sent):
                    if processed_sentences: # Ensure there's a previous sentence to append to
                        processed_sentences[-1] += stripped_sent[:5] # Limits to the first 5 ones
                    else: # If no previous sentence, just add it
                        processed_sentences.append(stripped_sent[:2])
                else:
                    processed_sentences.append(sent.rstrip()) # Use sent.rstrip() here

        if self.verbose:
            logger.debug(
                "Text splitted into sentences. Total sentences detected: %s",
                len(processed_sentences),
            )

        if _return_warnings:
            return processed_sentences, warnings

        if warnings:
            warning_message = [
                f"Found {len(warnings)} unique warning(s) during sentence splitting:"
            ]
            for msg in warnings:
                warning_message.append(f"  - {msg}")
            logger.warning("\n" + "\n".join(warning_message))

        return processed_sentences
