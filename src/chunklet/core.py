import re
import sys
from collections import Counter
from mpire import WorkerPool
from functools import lru_cache, partial
from typing import List, Dict, Any, Tuple, Callable, Optional, Union, Set
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from pysbd import Segmenter
from sentence_splitter import SentenceSplitter
from loguru import logger
from pydantic import ValidationError
from .utils.detect_text_language import detect_text_language
from .utils.universal_splitter import UniversalSplitter
from .models import CustomSplitterConfig, ChunkletInitConfig, ChunkingConfig
from .exceptions import (
    ChunkletError,
    InvalidInputError,
    TokenNotProvidedError,
)

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


class Chunklet:
    """
    A powerful text chunking utility offering flexible strategies for optimal text segmentation.

    Key Features:
    - Multiple Chunking Modes: Split text by sentence count, token count, or a hybrid approach.
    - Clause-Level Overlap: Ensures semantic continuity between chunks by overlapping at natural clause boundaries.
    - Multilingual Support: Automatically detects language and uses appropriate splitting algorithms for over 30 languages.
    - Pluggable Token Counters: Integrate custom token counting functions (e.g., for specific LLM tokenizers).
    - Pluggable Sentence splitters: Integrate custom splitters for more specific languages.
    - Parallel Processing: Efficiently handles batch chunking of multiple texts using multiprocessing.
    - Caching: Speeds up repeated chunking operations with LRU caching.
    """

    def __init__(
        self,
        verbose: bool = False,
        use_cache: bool = True,
        token_counter: Optional[Callable[[str], int]] = None,
        custom_splitters: CustomSplitterConfig = None,
    ):
        """
        Initialize Chunklet settings.

        Args:
            verbose (bool): Enable verbose logging.
            use_cache (bool): Enable caching on chunking.
            token_counter (Callable): Counts tokens in a sentence for token-based chunking.
            custom_splitters (CustomSplitterConfig): A list of custom sentence splitters.
                Each splitter should be a dictionary with 'name' (str), 'languages' (str or Iterable[str]), and a 'callback' (Callable[[str], List[str]]) keys. 
        """
        # Validate parameters
        try:
            config = ChunkletInitConfig(
                verbose=verbose,
                use_cache=use_cache,
                token_counter=token_counter,
                custom_splitters=custom_splitters,
            )
        except ValidationError as e:
            raise InvalidInputError(f"Invalid chunking configuration: {e}")
            
        self.verbose = config.verbose
        self.use_cache = config.use_cache
        self.token_counter = config.token_counter
        self.custom_splitters = config.custom_splitters

        if self.verbose:
            logger.debug(
                "Chunklet initialized with verbose={}, use_cache={}. Default token counter is {}provided.",
                self.verbose,
                self.use_cache,
                "not " if self.token_counter is None else "",
            )

        # Regex to split clauses inside sentences by clause-ending punctuation
        self.clause_end_regex = re.compile(rf"(?<=[{CLAUSE_END_TRIGGERS}])\s")

        # Universal sentence splitter for fallback
        self.universal_splitter = UniversalSplitter()

    def _split_by_sentence(self, text: str, lang: str) -> Tuple[List[str], Set[str]]:
        """
        Splits text into sentences using language-specific algorithms.
        Automatically detects language and prioritizes specialized libraries,
        falling back to a universal regex splitter for broad coverage.

        Args:
            text (str): The input text to split.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto').

        Returns:
            Tuple[List[str], Set[str]]: A tuple consists of a list of sentences and a set of warnings.
        """
        warnings = set()

        if lang == "auto":
            warnings.add("The language is set to `auto`. Consider setting the `lang` parameter to a specific language to improve performance.")
            lang_detected, confidence = detect_text_language(text)
            if self.verbose:
                logger.debug("Attempting language detection.")
            if confidence < 0.7:
                warnings.add(f"Low confidence in language detected. Detected: '{lang_detected}' with confidence {confidence:.2f}.") 
            lang = lang_detected if confidence >= 0.7 else lang

        # Prioritize custom splitters
        if self.custom_splitters:
            for splitter in self.custom_splitters:
                supported_languages = [splitter.languages] if isinstance(splitter.languages, str) else splitter.languages
                if lang in supported_languages:
                    if self.verbose:
                        logger.debug("Using {} for language: {}. (Custom Splitter)", splitter.name, lang)
                    return splitter.callback(text), warnings

        if lang in PYSBD_SUPPORTED_LANGUAGES:
            if self.verbose:
                logger.debug("Using pysbd for language: {}.", lang)
            return Segmenter(language=lang).segment(text), warnings
        elif lang in SENTENCESPLITTER_UNIQUE_LANGUAGES:
            if self.verbose:
                logger.debug("Using SentenceSplitter for language: {}. (SentenceSplitter)", lang)
            return SentenceSplitter(language=lang).split(text), warnings
        else: # Fallback to universal regex splitter
            warnings.add("Language not supported or detected with low confidence. Universal regex splitter was used.")
            if self.verbose:
                logger.debug("Using a universal regex splitter.")
            return self.universal_splitter.split(text), warnings

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
        
        if overlap_num == 0:
            return []

        overlapped_clauses = detected_clauses[-overlap_num:]

        if overlapped_clauses and (
            len(overlapped_clauses[0]) < 2 or not (overlapped_clauses[0][0].isupper() or overlapped_clauses[0][1].isupper())
        ):
            overlapped_clauses[0] = "... " + overlapped_clauses[0]
        return overlapped_clauses

    def _count_tokens(self, text: str, token_counter: Callable[[str], int]) -> int:
        """
        Safely count tokens, handling potential errors from the token_counter.
        Returns the count or raises a ChunkletError if the counter fails.
        """
        try:
            return token_counter(text)
        except Exception as e:
            raise ChunkletError(
                f"Token counter failed for text: '{text[:100]}'. Error: {e}"
            ) from e

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
        clauses = [cl for cl in clauses if cl.strip()]

        fitted = []
        unfitted = []
        for i in range(len(clauses)):
            clause_tokens = self._count_tokens(clauses[i], token_counter)

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
    ) -> Tuple[List[str], Set[str]]:
        """
        Groups sentences into chunks based on the specified mode and constraints.
        Applies overlap logic between consecutive chunks.

        Args:
            sentences (List): A list of sentences to be chunked.
            config (ChunkingConfig): Configuration for chunking.

        Returns:
            Tuple[List[str], Set[str]]: A list of chunks, where each chunk is a list of sentences, and a set of warning messages.
        """
        chunks = []
        curr_chunk = []
        token_count = 0
        sentence_count = 0
        index = 0
        while index < len(sentences):
            # Only calculate sentence_tokens if needed for token-based chunking
            if config.mode in {"token", "hybrid"}:
                sentence_tokens = self._count_tokens(
                    sentences[index], config.token_counter
                )
            else:  # mode is "sentence"
                sentence_tokens = 0  # Not used for chunking logic in sentence mode

            if (
                token_count + sentence_tokens > config.max_tokens
                or sentence_count + 1 > config.max_sentences
            ):
                if token_count + sentence_tokens > config.max_tokens:
                    remaining_tokens = config.max_tokens - token_count
                    fitted, unfitted = (
                        self._find_clauses_that_fit(
                            sentences[index], remaining_tokens, config.token_counter
                        )
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

                if config.mode in {"token", "hybrid"}:
                    token_count = sum(
                        self._count_tokens(s, config.token_counter) for s in curr_chunk
                    )  # Calculate current token count
                else:  # mode is "sentence"
                    token_count = 0  # Not used in sentence mode
                    
                # Treat clasuses as sentences
                # Estimation: 0 <= Residual capacity per chunk <= 2 (typical clauses per sentence)
                sentence_count = len(curr_chunk)

            if index < len(sentences):
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
        config: ChunkingConfig,
    ) -> Tuple[Tuple[str], Tuple[str]]:
        """
        Internal method to chunk a given text based on specified parameters.
        Performs sentence splitting and chunk grouping.

        Args:
            config (ChunkingConfig): The configuration for chunking.

        Returns:
            Tuple[Tuple[str], Tuple[str]]: A tuple of text chunks and a tuple of warning messages.
        """
        all_warnings = set()
        sentences, split_warnings = self._split_by_sentence(config.text, config.lang)
        all_warnings.update(split_warnings)

        if self.verbose:
            logger.debug(
                "Text splitted into sentences. Total sentences detected: {}",
                len(sentences),
            )
        if not sentences:
            return (), tuple(all_warnings)

        offset = round(config.offset)
        if offset >= len(sentences):
            if self.verbose:
                logger.info(
                    "Offset {} >= total sentences {}. Returning empty list.",
                    offset,
                    len(sentences),
                )
                
            return (), tuple(all_warnings)

        sentences = sentences[offset:]
        chunks = self._group_by_chunk(sentences, config)
        if self.verbose:
            logger.info("Finished chunking text. Generated {} chunks.\n", len(chunks))
        # Make them immutable to be safe with caching if enabled.
        return tuple(chunks), tuple(all_warnings)

    @lru_cache(maxsize=256)
    def _chunk_cached(
        self,
        config: ChunkingConfig,
    ) -> Tuple[Tuple[str], Tuple[str]]:
        """
        Cached version of the `_chunk` method, leveraging LRU caching for performance.
        """
        return self._chunk(config)

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

        Raises:
            InvalidInputError: If any chunking configuration parameter is invalid.
            TokenNotProvidedError: If `mode` is "token" or "hybrid" but no `token_counter` is provided.
            ChunkletError: If the provided `token_counter` callable raises an exception during token counting.
        """
        if self.verbose:
            logger.info("Processing text - single run")

        # Adjust limits based on mode
        if mode == "sentence":
            max_tokens = sys.maxsize
        elif mode == "token":
            max_sentences = sys.maxsize

        # Validate all parameters through ChunkingConfig
        try:
            config = ChunkingConfig(
                text=text,
                lang=lang,
                mode=mode,
                max_tokens=max_tokens,
                max_sentences=max_sentences,
                overlap_percent=overlap_percent,
                offset=offset,
                token_counter=token_counter if token_counter else self.token_counter,
                verbose=self.verbose,
                use_cache=self.use_cache,
            )
        except ValidationError as e:
            raise InvalidInputError(f"Invalid chunking configuration: {e}")

        if not config.text:
            if self.verbose:
                logger.info("Input text is empty. Returning empty list.")
            return [] if not _batch_context else ([], ())

        if self.use_cache:
            chunks, warnings = self._chunk_cached(config)
        else:
            chunks, warnings = self._chunk(config)

        if _batch_context:
            return list(chunks), warnings

        if warnings:
            warning_message = [
                f"Found {len(warnings)} unique warning(s) during chunking:"
            ]
            for msg in warnings:
                warning_message.append(f"  - {msg}")
            logger.warning("\n" + "\n".join(warning_message))

        return list(chunks)

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

        Raises:
            InvalidInputError: If `texts` is not a list or if `n_jobs` is less than 1.
        """
        if not isinstance(texts, list):
            raise InvalidInputError("Input 'texts' must be a list.")

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
            raise InvalidInputError("n_jobs must be >= 1 or None")

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

        chunk_func = partial(self.chunk, **params)
        results = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            transient=True,
        ) as progress:
            task = progress.add_task("[green]Processing...", total=len(texts))

            if n_jobs == 1:
                for text in texts:
                    try:
                        results.append(chunk_func(text))
                        progress.update(task, advance=1)
                    except Exception as e:
                        logger.error(f"A task in batch_chunk failed: {e}. Returning partial results.")
                        break
            else:
                with WorkerPool(n_jobs=n_jobs) as executor:
                    for result in executor.imap(chunk_func, texts):
                        results.append(result)
                        progress.update(task, advance=1)
        
        if not results:
            return []

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
        return list(collected_chunks)

    def preview_sentences(self, text: str, lang: str = "auto") -> Tuple[List[str], Set[str]]:
        """
        Splits text into sentences for quick preview or inspection.

        Uses Chunklet’s multi-language sentence splitting logic without chunking.

        Args:
            text (str): Input text.
            lang (str): Language code ('en', 'fr', 'auto'). Defaults to 'auto'.

        Returns:
             Tuple[List[str], Set[str]]:
                 - A list of sentences from the input text.
                 - A set of wanings if any.
        """
        return self._split_by_sentence(text, lang)
