import re
import math
from collections import Counter
from mpire import WorkerPool
from functools import lru_cache
from typing import List, Tuple, Callable, Optional, Union, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from pysbd import Segmenter
from sentence_splitter import SentenceSplitter
from loguru import logger
from .utils.detect_text_language import detect_text_language
from .utils.regex_splitter import RegexSplitter

# Complete set of languages supported by pysbd (Python Sentence Boundary Disambiguation)
PYSBD_SUPPORTED_LANGUAGES = {
    "en",  # English
    "mr",  # Marathi
    "hi",  # Hindi
    "bg",  # Bulgarian
    "es",  # Spanish
    "ru",  # Russian
    "ar",  # Arabic
    "am",  # Amharic
    "hy",  # Armenian
    "fa",  # Persian (Farsi)
    "ur",  # Urdu
    "pl",  # Polish
    "zh",  # Chinese (Mandarin)
    "nl",  # Dutch
    "da",  # Danish
    "fr",  # French
    "it",  # Italian
    "el",  # Greek
    "my",  # Burmese (Myanmar)
    "ja",  # Japanese
    "de",  # German
    "kk",  # Kazakh
}

# Languages unique to SentenceSplitter that are NOT supported by pysbd
SENTENCESPLITTER_UNIQUE_LANGUAGES = {
    "ca",  # Catalan
    "cs",  # Czech
    "fi",  # Finnish
    "hu",  # Hungarian
    "is",  # Icelandic
    "lv",  # Latvian
    "lt",  # Lithuanian
    "no",  # Norwegian
    "pt",  # Portuguese
    "ro",  # Romanian
    "sk",  # Slovak
    "sl",  # Slovenian
    "sv",  # Swedish
    "tr",  # Turkish
}

CLAUSE_END_TRIGGERS = r";,’：—)&"


class ChunkingConfig(BaseModel):
    """Pydantic model for chunking configuration validation"""

    class Config:
        frozen = True

    lang: str = "auto"
    mode: Literal["sentence", "token", "hybrid"] = "sentence"
    max_tokens: Union[int, float] = Field(default=512, ge=10)
    max_sentences: Union[int, float] = Field(default=100, ge=0)
    overlap_percent: Union[int, float] = Field(default=10, ge=0, le=75)
    offset: int = Field(default=0, ge=0)
    verbose: bool = False
    use_cache: bool = True
    token_counter: Optional[Callable[[str], int]] = None

    @model_validator(mode="after")
    def validate_token_counter(self) -> "ChunkingConfig":
        if self.mode in {"token", "hybrid"} and self.token_counter is None:
            raise ValueError("A token_counter is required for token-based chunking.")
        return self


class Chunklet:
    """
    A powerful text chunking utility offering flexible strategies for optimal text segmentation.

    Key Features:
    - Multiple Chunking Modes: Split text by sentence count, token count, or a hybrid approach.
    - Clause-Level Overlap: Ensures semantic continuity between chunks by overlapping at natural clause boundaries.
    - Multilingual Support: Automatically detects language and uses appropriate splitting algorithms for over 30 languages.
    - Pluggable Token Counters: Integrate custom token counting functions (e.g., for specific LLM tokenizers).
    - Parallel Processing: Efficiently handles batch chunking of multiple texts using multiprocessing.
    - Caching: Speeds up repeated chunking operations with LRU caching.
    """

    def __init__(
        self,
        verbose: bool = False,
        use_cache: bool = True,
        token_counter: Optional[Callable[[str], int]] = None,
    ):
        """
        Initialize Chunklet settings.

        Args:
            verbose (bool): Enable verbose logging.
            use_cache (bool): Enable caching on chunking.
            token_counter (Callable): Counts tokens in a sentence for token-based chunking.
        """
        self.verbose = verbose
        self.use_cache = use_cache
        self.token_counter = token_counter

        if self.verbose:
            logger.debug(
                "Chunklet initialized with verbose={}, use_cache={}. Default token counter is {}provided.",
                self.verbose,
                self.use_cache,
                "not " if self.token_counter is None else "",
            )

        # Regex to split clauses inside sentences by clause-ending punctuation
        self.clause_end_regex = re.compile(rf"(?<=[{CLAUSE_END_TRIGGERS}])\s")

        #
        self.regex_splitter = RegexSplitter()

    def _split_by_sentence(self, text: str, lang: str) -> List[str]:
        """
        Splits text into sentences using language-specific algorithms.
        Automatically detects language and prioritizes specialized libraries,
        falling back to a universal regex splitter for broad coverage.

        Args:
            text (str): The input text to split.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto').

        Returns:
            List[str]: A list of sentences.
        """
        warnings = {}

        if lang == "auto":
            lang_detected, confidence = detect_text_language(text)
            if self.verbose:
                logger.debug("Attempting language detection.")
            if confidence < 0.7:
                warnings[
                    f"Low confidence in language detected. Detected: '{lang_detected}' with confidence {confidence:.2f}."
                ] = True
            lang = lang_detected if confidence >= 0.7 else lang

        if lang in PYSBD_SUPPORTED_LANGUAGES:
            if self.verbose:
                logger.debug("Using pysbd for language: {}.", lang)
            return Segmenter(language=lang).segment(text), warnings

        if lang in SENTENCESPLITTER_UNIQUE_LANGUAGES:
            if self.verbose:
                logger.debug("Using SentenceSplitter for language: {}.", lang)
            return SentenceSplitter(language=lang).split(text), warnings

        if self.verbose:
            logger.debug("Using a universal regex splitter.")
        warnings[
            "Language not supported or detected with low confidence. Universal regex splitter was used."
        ] = True
        return self.regex_splitter.split(text), warnings

    def _get_overlap_clauses(
        self,
        sentences: List[str],
        overlap_percent: Union[int, float],
    ) -> List[str]:
        """
        Extracts a specified number of clauses from the end of the previous chunk
        to create overlap for the next chunk.

        Args:
            sentences (List): A list of sentences to be chunked.
            overlap_percent (Union[int, float]): Percentage of overlap between chunks (0-75).

        Returns:
            List[str]: A list of clauses as overlap.
        """
        detected_clauses = []
        for sent in sentences:
            detected_clauses += self.clause_end_regex.split(sent)

        overlap_num = round(len(detected_clauses) * overlap_percent / 100)
        overlapped_clauses = detected_clauses[-overlap_num:]

        if overlapped_clauses and not (
            overlapped_clauses[0][0].isupper() or overlapped_clauses[0][1].isupper()
        ):
            overlapped_clauses[0] = "... " + overlapped_clauses[0]
        return overlapped_clauses

    def _find_clauses_that_fit(
        self,
        sentence: str,
        remaining_tokens: int,
        token_counter: Callable[[str], int],
    ) -> Tuple[List[str], List[str]]:
        """
        Splits a sentence into clauses and fits them into a token budget.

        This method takes a sentence and attempts to fit its component clauses
        into the number of remaining tokens available. It greedily adds clauses
        that fit and returns the fitted clauses and any that were left over.

        Args:
            sentence (str): The input string to be split into clauses.
            remaining_tokens (int): The number of tokens available to fit clauses into.
            token_counter (Callable): Counts tokens in a sentence for token-based chunking.
        Returns:
            Tuple[List[str], List[str]]: A tuple containing two list
            - The first list contains clauses that fit within the token budget.
            - The second list contains the remaining unfitted clauses.
        """
        clauses = self.clause_end_regex.split(sentence)

        fitted = []
        unfitted = []
        for i in range(len(clauses)):
            clause_tokens = token_counter(clauses[i])
            if clause_tokens <= remaining_tokens:
                fitted.append(clauses[i])
                remaining_tokens -= clause_tokens
            else:
                unfitted = clauses[i:]
                break

        return fitted, unfitted

    def _group_by_chunk(
        self,
        sentences: List[str],
        config: ChunkingConfig,
    ) -> List[List[str]]:
        """
        Groups sentences into chunks based on the specified mode and constraints.
        Applies overlap logic between consecutive chunks.

        Args:
            sentences (List): A list of sentences to be chunked.
            config (ChunkingConfig): Configuration for chunking.

        Returns:
            List[List[str]]: A list of chunks, where each chunk is a list of sentences.
        """
        chunks = []
        curr_chunk = []
        token_count = 0
        sentence_count = 0
        index = 0
        while index < len(sentences):
            sentence_tokens = config.token_counter(sentences[index])
            if (
                token_count + sentence_tokens > config.max_tokens
                or sentence_count + 1 > config.max_sentences
            ):
                if token_count + sentence_tokens > config.max_tokens:
                    remaining_tokens = config.max_tokens - token_count
                    fitted, unfitted = self._find_clauses_that_fit(
                        sentences[index], remaining_tokens, config.token_counter
                    )
                    chunks.append(curr_chunk + fitted)  # Complete
                    index += 1
                else:
                    chunks.append(curr_chunk)  # Complete
                    unfitted = []

                # Prepare data for next chunk
                overlap_clauses = self._get_overlap_clauses(
                    chunks[-1], config.overlap_percent
                )
                curr_chunk = overlap_clauses + unfitted

                token_count = sum(
                    self.token_counter(s) for s in curr_chunk
                )  # Calculate current token count
                # Estimation: 0 <= Residual capacity <= 2 (typical clauses per sentence)
                sentence_count = len(curr_chunk)

            curr_chunk.append(sentences[index])
            token_count += sentence_tokens
            sentence_count += 1
            index += 1

        # Add any remnants
        if curr_chunk:
            chunks.append(curr_chunk)

        # Flatten into strings
        final_chunks = ["".join(chunk) for chunk in chunks]
        return final_chunks

    def _chunk(
        self,
        text,
        lang,
        mode,
        max_tokens,
        max_sentences,
        overlap_percent,
        offset,
        token_counter,
    ) -> List[str]:
        """
        Internal method to chunk a given text based on specified parameters.
        Performs validation and orchestrates sentence splitting and chunk grouping.

        Args:
            text (str): The input text to chunk.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto').
            mode (str): Chunking mode ('sentence', 'token', or 'hybrid').
            max_tokens (int): Maximum number of tokens per chunk.
            max_sentences (int): Maximum number of sentences per chunk.
            overlap_percent (Union[int, float]): Percentage of overlap between chunks (0-75).
            offset (int): Starting sentence offset for chunking.
            token_counter (Optional[Callable[[str], int]]): callable that takes a string
                (sentence) and returns its token count. Required for token-based chunking
                if default token_counter is not set in init.

        Returns:
            List[str]: A list of text chunks.

        Raises:
            ValidationError: If any of the input parameters are invalid.
        """
        if self.verbose:
            logger.info("Chunking with mode **{}**", mode)

        # Adjust limits based on mode
        if mode == "sentence":
            max_tokens = math.inf
        elif mode == "token":
            max_sentences = math.inf

        # Validate all parameters through ChunkingConfig
        config = ChunkingConfig(
            lang=lang,
            mode=mode,
            max_tokens=max_tokens,
            max_sentences=max_sentences,
            overlap_percent=overlap_percent,
            offset=offset,
            token_counter=token_counter if token_counter else self.token_counter,
        )

        sentences, warnings = self._split_by_sentence(text, config.lang)
        if self.verbose:
            logger.debug(
                "Text splitted into sentences. Total sentences detected: {}",
                len(sentences),
            )
        if not sentences:
            return [], {}

        offset = round(config.offset)
        if offset >= len(sentences):
            if self.verbose:
                logger.info(
                    "Offset {} >= total sentences {}. Returning empty list.",
                    offset,
                    len(sentences),
                )
            return [], {}

        sentences = sentences[offset:]
        chunks = self._group_by_chunk(sentences, config)
        if self.verbose:
            logger.info("Finished chunking text. Generated {} chunks.\n", len(chunks))
        return chunks, warnings

    @lru_cache(maxsize=25)
    def _chunk_cached(
        self,
        text,
        lang,
        mode,
        max_tokens,
        max_sentences,
        overlap_percent,
        offset,
        token_counter,
    ) -> List[str]:
        """
        Cached version of the `_chunk` method, leveraging LRU caching for performance.

        Args:
            text (str): The input text to chunk.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto').
            mode (str): Chunking mode ('sentence', 'token', or 'hybrid').
            max_tokens (int): Maximum number of tokens per chunk.
            max_sentences (int): Maximum number of sentences per chunk.
            overlap_percent (Union[int, float]): Percentage of overlap between chunks (0-85).
            offset (int): Starting sentence offset for chunking.
            token_counter (Optional[Callable[[str], int]]): callable that takes a string
                (sentence) and returns its token count.

        Returns:
            List[str]: A list of text chunks.
        """
        params = locals()
        params.pop("self")
        return self._chunk(**params)

    def chunk(
        self,
        text: str,
        *,
        lang: str = "auto",
        mode: str = "sentence",
        max_tokens: int = 512,
        max_sentences: int = 100,
        overlap_percent: Union[int, float] = 20,
        offset: int = 0,
        token_counter: Optional[Callable[[str], int]] = None,
        _batch_context: bool = False,
    ) -> List[str]:
        """
        Chunks a single text into smaller pieces based on specified parameters.
        Supports multiple chunking modes (sentence, token, hybrid), clause-level overlap,
        and custom token counters.

        Args:
            text (str): The input text to chunk.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto'). Defaults to "auto".
            mode (str): Chunking mode ('sentence', 'token', or 'hybrid'). Defaults to "sentence".
            max_tokens (int): Maximum number of tokens per chunk. Defaults to 512.
            max_sentences (int): Maximum number of sentences per chunk. Defaults to 100.
            overlap_percent (Union[int, float]): Percentage of overlap between chunks (0-85).
                Defaults to 20
            offset (int): Starting sentence offset for chunking. Defaults to 0.

        Returns:
            List[str]: A list of text chunks.
        """
        if self.verbose:
            logger.info("Processing text - single run")

        if not text:
            if self.verbose:
                logger.info("Input text is empty. Returning empty list.")
            return []

        params = locals()
        params.pop("self")
        params.pop("_batch_context")
        params["token_counter"] = (
            token_counter if token_counter is not None else self.token_counter
        )

        if self.use_cache:
            chunks, warnings = self._chunk_cached(**params)
        else:
            chunks, warnings = self._chunk(**params)

        if _batch_context:
            return chunks, warnings

        for msg, triggered in warnings.items():
            if triggered:
                logger.warning(msg)
        return chunks

    def batch_chunk(
        self,
        texts: List[str],
        *,
        lang: str = "auto",
        mode: str = "sentence",
        max_tokens: int = 512,
        max_sentences: int = 100,
        overlap_percent: Union[int, float] = 20,
        offset: int = 0,
        n_jobs: Optional[int] = None,
        token_counter: Optional[Callable[[str], int]] = None,
    ) -> List[List[str]]:
        """
        Processes a batch of texts in parallel, splitting each into chunks.
        Leverages multiprocessing for efficient batch chunking.

        Args:
            texts: List of input texts to be chunked. Each text will be processed independently.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto'). Defaults to "auto".
            mode (str): Chunking mode ('sentence', 'token', or 'hybrid'). Defaults to "sentence".
            max_tokens (int): Maximum number of tokens per chunk. Defaults to 512.
            max_sentences (int): Maximum number of sentences per chunk. Defaults to 100.
            overlap_percent (Union[int, float]): Percentage of overlap between chunks (0-85).
                Defaults to 20.
            offset (int): Starting sentence offset for chunking. Defaults to 0.
            n_jobs: Number of parallel workers to use. If None, uses all available CPUs.
                   Must be >= 1 if specified.
            token_counter: Optional token counting function. Required for token-based modes.

        Returns:
            A list of lists, where each inner list contains the chunks for the corresponding input text.
            The order of texts is preserved in the output.
        """
        if self.verbose:
            logger.info(
                "Processing {} texts in batch mode with n_jobs={}.",
                len(texts),
                n_jobs if n_jobs is not None else "default",
            )

        if not texts:
            if self.verbose:
                logger.info("Input texts is empty. Returning empty list.")
            return []

        # Validate n_jobs parameter
        if n_jobs is not None and n_jobs < 1:
            raise ValueError("n_jobs must be >= 1 or None")

        params = {
            "lang": lang,
            "mode": mode,
            "max_tokens": max_tokens,
            "max_sentences": max_sentences,
            "overlap_percent": overlap_percent,
            "offset": offset,
            "token_counter": token_counter,
            "_batch_context": True,
        }

        with WorkerPool(n_jobs=n_jobs) as executor:
            results = list(executor.map(lambda text: self.chunk(text, **params), texts))

        collected_chunks, collected_warnings = zip(*results)
        warnings_counter = Counter()
        for warning_set in collected_warnings:
            for msg in warning_set:
                warnings_counter[msg] += 1

        if warnings_counter:
            # Build a multi-line warning message for the logger
            warning_message = [
                f"Found {len(warnings_counter)} unique warning(s) during batch processing of {len(texts)} texts:"
            ]
            for msg, count in warnings_counter.items():
                warning_message.append(f"  - ({count}/{len(texts)}) {msg}")
            # Log the entire formatted message as a single entry
            logger.warning("\n" + "\n".join(warning_message))
        return collected_chunks

    def preview_sentences(self, text: str, lang: str = "auto") -> List[str]:
        """
        Splits text into sentences for quick preview or inspection.

        Uses Chunklet’s multi-language sentence splitting logic without chunking.

        Args:
            text (str): Input text.
            lang (str): Language code ('en', 'fr', 'auto'). Defaults to 'auto'.

        Returns:
             List[str]: Sentences from the input text.
        """
        return self._split_by_sentence(text, lang)
