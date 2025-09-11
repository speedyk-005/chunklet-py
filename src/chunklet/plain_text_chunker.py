from __future__ import annotations
import re
import sys
from collections import Counter
from functools import lru_cache, partial
from typing import Callable, Optional
from box import Box
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from pysbd import Segmenter
from sentence_splitter import SentenceSplitter
from loguru import logger
from pydantic import ValidationError
from chunklet.libs.universal_splitter import UniversalSplitter
from chunklet.utils.detect_text_language import detect_text_language
from chunklet.utils.error_utils import pretty_errors
from chunklet.models import (
    CustomSplitterConfig,
    PlainTextChunkerConfig,
    TextChunkingConfig,
)
from chunklet.exceptions import (
    InvalidInputError,
    TextProcessingError,
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


class PlainTextChunker:
    """
    A powerful text chunking utility offering flexible strategies for optimal text segmentation.

    Key Features:
    - Multiple Chunking Modes: Split text by sentence count, token count, or a hybrid approach.
    - Clause-Level Overlap: Ensures semantic continuity between chunks by overlapping
    at natural clause boundaries with Customizable continuation marker.
    - Multilingual Support: Automatically detects language and uses appropriate splitting algorithms for over 30 languages.
    - Pluggable Token Counters: Integrate custom token counting functions (e.g., for specific LLM tokenizers).
    - Pluggable Sentence splitters: Integrate custom splitters for languages or requirements.
    - Parallel Processing: Efficiently handles batch chunking of multiple texts using multiprocessing.
    - Caching: Speeds up repeated chunking operations with LRU caching.
    """

    def __init__(
        self,
        verbose: bool = False,
        use_cache: bool = True,
        token_counter: Callable[[str], int] | None = None,
        custom_splitters: CustomSplitterConfig = None,
        continuation_marker: str = "...",
    ):
        """
        Initialize Chunklet settings.

        Args:
            verbose (bool): Enable verbose logging.
            use_cache (bool): Enable caching on chunking.
            token_counter (Callable): Counts tokens in a sentence for token-based chunking.
            custom_splitters [list[dict]] | None: A list of custom sentence splitters.
                Each splitter should be a dictionary with 'name' (str),
                'languages' (str or Iterable[str]) (e.g., 'en', ['en', 'fr'])."),
                and a 'callback' (Callable[[str], list[str]])
                (Where the input is a path string) keys.
            continuation_marker (str): The marker to prepend to unfitted clauses. Defaults to '...'.
        """
        # Validate parameters
        try:
            config = PlainTextChunkerConfig(
                verbose=verbose,
                use_cache=use_cache,
                token_counter=token_counter,
                custom_splitters=custom_splitters,
                continuation_marker=continuation_marker
            )
        except ValidationError as e:
            pretty_err = pretty_errors(e)
            raise InvalidInputError(f"Invalid configuration.\n Details: {pretty_err}") from e

        self.verbose = config.verbose
        self.use_cache = config.use_cache
        self.token_counter = config.token_counter
        self.custom_splitters = config.custom_splitters
        self.continuation_marker = config.continuation_marker

        # Prepare a set of supported extensions from custom processors
        self.custom_splitters_languages = set()
        if self.custom_splitters:
            for splitter in self.custom_splitters:
                if isinstance(processor.languages, str):
                    self.custom_splitters_languages.add(processor.languages)
                else:
                    self.custom_splitters_languages.update(set(processor.languages))
                        
        if self.verbose:
            logger.debug(
                "Initialized with verbose={}, use_cache={}. Default token counter is {}provided.",
                self.verbose,
                self.use_cache,
                "not " if self.token_counter is None else "",
            )

        # Regex to split clauses inside sentences by clause-ending punctuation
        self.clause_end_regex = re.compile(rf"(?<=[{CLAUSE_END_TRIGGERS}])\s") 

        # Universal sentence splitter for fallback
        self.universal_splitter = UniversalSplitter()

    def _use_custom_splitter(self, text: str, lang: str) -> list[str]:
        """
        Processes a text using a custom splitter registered for the given language.

        Args:
            text (str): The text to split.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto').

        Returns:
            list[str]: A list of sentences.

        Raises:
             TextProcessingError: If a custom splitter fails during execution.
        """
        for splitter in self.custom_splitters:
            supported_languages = (
                [splitter.languages]
                if isinstance(splitter.languages, str)
                else splitter.languages
            )
            if lang in supported_languages:
                try:
                    return splitter.callback(text), warnings
                except Exception as e:
                    raise TextProcessingError(
                        f"Custom splitter '{splitter.name}' failed for text: '{text[:100]}'.\n Details: {e}"
                    ) from e
                    
    def _split_by_sentence(self, text: str, lang: str) -> tuple[list[str], set[str]]:
        """
        Splits text into sentences using language-specific algorithms.
        Automatically detects language and prioritizes specialized libraries,
        falling back to a universal regex splitter for broad coverage.

        Args:
            text (str): The input text to split.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto').

        Returns:
            Tuple[list[str], set[str]]: A tuple consists of a list of sentences and a set of warnings.
        """
        warnings = set()

        if lang == "auto":
            warnings.add(
                "The language is set to `auto`. Consider setting the `lang` parameter to a specific language to improve performance."
            )
            lang_detected, confidence = detect_text_language(text)
            if self.verbose:
                logger.debug("Attempting language detection.")
            if confidence < 0.7:
                warnings.add(
                    f"Low confidence in language detected. Detected: '{lang_detected}' with confidence {confidence:.2f}."
                )
            lang = lang_detected if confidence >= 0.7 else lang

        # Prioritize custom splitters
        if lang in self.custom_splitters_languages:
            if self.verbose:
                logger.debug(
                    "Using {} for language: {}. (Custom Splitter)",
                    splitter.name,
                    lang,
                )
            return self._use_custom_splitter(text, lang), warnings

                    
        if lang in PYSBD_SUPPORTED_LANGUAGES:
            if self.verbose:
                logger.debug("Using pysbd for language: {}.", lang)
            return Segmenter(language=lang).segment(text), warnings
        elif lang in SENTENCESPLITTER_UNIQUE_LANGUAGES:
            if self.verbose:
                logger.debug(
                    "Using SentenceSplitter for language: {}. (SentenceSplitter)", lang
                )
            return SentenceSplitter(language=lang).split(text), warnings
        else:  # Fallback to universal regex splitter
            warnings.add(
                "Language not supported or detected with low confidence. Universal regex splitter was used."
            )
            if self.verbose:
                logger.debug("Using a universal regex splitter.")
            return self.universal_splitter.split(text), warnings

    def _get_overlap_clauses(
        self,
        sentences: list[str],
        overlap_percent: int | float,
    ) -> list[str]:
        """
        Extracts a specified number of clauses from the end of the previous chunk
        to create overlap for the next chunk.
        It optionally prepends a continuation marker in some cases.

        Args:
            sentences (List): A list of sentences to be chunked.
            overlap_percent (Union[int, float]): Percentage of overlap between chunks (0-75).

        Returns:
            list[str]: A list of clauses as overlap.
        """
        detected_clauses = []
        for sent in sentences:
            detected_clauses += self.clause_end_regex.split(sent)

        overlap_num = round(len(detected_clauses) * overlap_percent / 100)

        if overlap_num == 0:
            return []

        overlapped_clauses = detected_clauses[-overlap_num:]

        if overlapped_clauses and (
            len(overlapped_clauses[0]) < 2
            or not (
                overlapped_clauses[0][0].isupper() or overlapped_clauses[0][1].isupper()
            )
        ):
            overlapped_clauses[0] = (
                f"{self.continuation_marker} " + overlapped_clauses[0]
            )
        return overlapped_clauses

    def _count_tokens(self, text: str, token_counter: Callable[[str], int]) -> int:
        """
        Safely count tokens, handling potential errors from the token_counter.
        Returns the count or raises a TextProcessingError, if the counter fails.
        """
        try:
            return token_counter(text)
        except Exception as e:
            raise TextProcessingError(
                f"Token counter failed for text: '{text[:100]}'.\n Details: {e}"
            ) from e

    def _find_clauses_that_fit(
        self,
        sentence: str,
        remaining_tokens: int,
        token_counter: Callable[[str], int],
    ) -> tuple[list[str], list[str]]:
        """
        Splits a sentence into clauses and fits them into a token budget.

        This method takes a sentence and attempts to fit its component clauses
        into the number of remaining tokens available.

        Args:
            sentence (str): The input string to be split into clauses.
            remaining_tokens (int): The number of tokens available to fit clauses into.
            token_counter (Callable): The function needed for token counting.
        Returns:
            list[str]: A List containing two strings:
            - The clauses that fit within the token budget.
            - The remaining unfitted clauses.
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

        if len(unfitted) == 1:
            # Ignore last chars if longer than 100.
            # case: links, images embeddings uris, text with no punctuations
            unfitted = unfiited[100:] 

        return " ".join(fitted), " ".join(unfitted)

    
    def _group_by_chunk(
        self,
        sentences: list[str],
        config: TextChunkingConfig,
    ) -> list[str]:
        """
        Groups sentences into chunks based on the specified mode and constraints.
        Applies overlap logic between consecutive chunks.

        Args:
            sentences lList): A list of sentences to be chunked.
            config (TextChunkingConfig): Configuration for chunking.

        Returns:
            list[str]: A list of chunk strings.
        """
        # length of the curr_chunk overlaps + optional(unfitted text), Used to prevent oversized chunk in rare cases.
        # for instance: the original text to chunk has parts not well written.
        #(e.g. long paragrapth without punctuations, embeded images urls, ...)
        chunk_base_count = 0

        chunks = []
        curr_chunk = []
        curr_token_count = 0
        sentence_count = 0
        
        index = 0
        while index < len(sentences):
            if config.mode in {"token", "hybrid"}:
                sentence_tokens = self._count_tokens(
                    sentences[index], config.token_counter
                )
            else:
                sentence_tokens = 0

            if (
                curr_token_count + sentence_tokens > config.max_tokens
                or sentence_count + 1 > config.max_sentences
            ):
                # If curr_chunk contains only the base but limit is reached
                # That might mean a long text without punctuation.
                if chunk_base_count == sentence_count:
                    sent_head = (
                        # Ignore last chars
                        sentences[index][100:] + self.continuation_marker
                    )
                    curr_chunk.append(sent_head)
                    continue
                
                if curr_token_count + sentence_tokens > config.max_tokens:
                    remaining_tokens = config.max_tokens - curr_token_count
                    fitted, unfitted = self._find_clauses_that_fit(
                        sentences[index],
                        remaining_tokens,
                        config.token_counter,
                    )
                    if fitted:
                        curr_chunk.append(fitted)
                        chunks.append(curr_chunk)  # Considered complete
                        index += 1
                    else:
                        unfitted = ""
                else:
                    chunks.append(curr_chunk)  # Considered complete
                    unfitted = ""
                
                # Prepare data for next chunk
                overlap_clauses = self._get_overlap_clauses(
                    chunks[-1], config.overlap_percent
                )
                curr_chunk = overlap_clauses + [unfitted]

                # Incrementally update token_count for the new curr_chunk_sentences
                if config.mode in {"token", "hybrid"}:
                    curr_token_count = sum(
                        self._count_tokens(s, config.token_counter)
                        for s in overlap_clauses + [unfitted]
                    )
                sentence_count = len(curr_chunk)
                chunk_base_count = sentence_count
            else:
                if index < len(sentences):
                    curr_chunk.append(sentences[index])
                curr_token_count += sentence_tokens
                sentence_count += 1
                index += 1

        # Add any remnants
        if curr_chunk:
            chunks.append(curr_chunk)

        final_chunks = []
        for i, chunk_sentences in enumerate(chunks):
            if not chunk_sentences:
                continue

            content = "\n".join(chunk_sentences)
            final_chunks.append(content)

        return final_chunks

    def _chunk(
        self,
        config: TextChunkingConfig,
    ) -> tuple[tuple[str], tuple[str]]:
        """
        Internal method to chunk a given text based on specified parameters.
        Performs sentence splitting and chunk grouping.

        Args:
            config (TextChunkingConfig): The configuration for chunking.

        Returns:
            tuple[Tuple[str], tuple[str]]: A tuple of chunk strings and a tuple of warning messages.
        """
        all_warnings = set()
        sentences, split_warnings = self._split_by_sentence(config.text, config.lang)
        sentences = [sent.rstrip() for sent in sentences if sent.strip()]
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
        config: TextChunkingConfig,
    ) -> tuple[tuple[Box], tuple[str]]:
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
        max_tokens: int = 256,
        max_sentences: int = 12,
        overlap_percent: int | float = 20,
        offset: int = 0,
        token_counter: Callable[[str], int] | None = None,
        _batch_context: bool = False,
    ) -> list[str]:
        """
        Chunks a single text into smaller pieces based on specified parameters.
        Supports multiple chunking modes (sentence, token, hybrid), clause-level overlap,
        and custom token counters.

        Args:
            text (str): The input text to chunk.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto'). Defaults to "auto".
            mode (str): Chunking mode ('sentence', 'token', or 'hybrid'). Defaults to "sentence".
            max_tokens (int): Maximum number of tokens per chunk. Defaults to 512.
            max_sentences (int): Maximum number of sentences per chunk. Defaults to 12.
            overlap_percent (int | float): Percentage of overlap between chunks (0-85).
                Defaults to 20
            offset (int): Starting sentence offset for chunking. Defaults to 0.
            token_counter (callable | None): Optional token counting function. Required for token-based modes only.

        Returns:
            list[str]: A list of chunk strings.

        Raises:
            InvalidInputError: If any chunking configuration parameter is invalid.
            MissingTokenCounterError: If `mode` is "token" or "hybrid" but no `token_counter` is provided.
            TextProcessingError: If the provided `token_counter` callable raises an exception during token counting.
        """
        if self.verbose:
            logger.info("Processing text - single run")

        # Adjust limits based on mode
        if mode == "sentence":
            max_tokens = sys.maxsize
        elif mode == "token":
            max_sentences = sys.maxsize

        # Validate all parameters through TextChunkingConfig
        try:
            config = TextChunkingConfig(
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
            pretty_err = pretty_errors(e)
            raise InvalidInputError(f"Invalid chunking configuration.\n Details: {pretty_err}") from e

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
        texts: list[str],
        *,
        lang: str = "auto",
        mode: str = "sentence",
        max_tokens: int = 256,
        max_sentences: int = 12,
        overlap_percent: int | float = 20,
        offset: int = 0,
        token_counter: Callable[[str], int] | None = None,
        n_jobs: Optional[int] = None,
        show_progress: bool = True,
    ) -> list[list[str]]:
        """
        Processes a batch of texts in parallel, splitting each into chunks.
        Leverages multiprocessing for efficient batch chunking.

        If a task fails, `chunklet` will now stop processing and return the results
        of the tasks that completed successfully, preventing wasted work.

        Args:
            texts: List of input texts to be chunked. Each text will be processed independently.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto'). Defaults to "auto".
            mode (str): Chunking mode ('sentence', 'token', or 'hybrid'). Defaults to "sentence".
            max_tokens (int): Maximum number of tokens per chunk.
            max_sentences (int): Maximum number of sentences per chunk.
            overlap_percent (int | float): Percentage of overlap between chunks (0-85).
            offset (int): Starting sentence offset for chunking. Defaults to 0.
            token_counter (callable | None): The token counting function. Required for token-based modes only.
            n_jobs (int | None): Number of parallel workers to use. If None, uses all available CPUs.
                   Must be >= 1 if specified.
            show_progress (bool): Flag to show to enable or disable the loading bar.

        Returns:
            List[list[str]]: A list of lists of chunk strings, where each inner list contains
            the chunks for the corresponding input text.

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

        if show_progress:
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
                            logger.error(
                                f"A task in batch_chunk failed. Returning partial results.\n Reason:{e}."
                            )
                            break
                else:
                    from mpire import WorkerPool  # Lazy import, only needed there.

                    with WorkerPool(n_jobs=n_jobs) as executor:
                        for result in executor.imap(chunk_func, texts):
                            results.append(result)
                            progress.update(task, advance=1)
        else:  # No progress bar
            if n_jobs == 1:
                for text in texts:
                    try:
                        results.append(chunk_func(text))
                    except Exception as e:
                        logger.error(
                                f"A task in batch_chunk failed. Returning partial results.\n Reason:{e}."
                            )
                        break
            else:
                from mpire import WorkerPool  # Lazy import, only needed there.

                with WorkerPool(n_jobs=n_jobs) as executor:
                    for result in executor.imap(chunk_func, texts):
                        results.append(result)

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

    def preview_sentences(
        self, text: str, lang: str = "auto"
    ) -> tuple[list[str], set[str]]:
        """
        Splits text into sentences for quick preview or inspection.

        Uses Chunklet’s multi-language sentence splitting logic without chunking.

        Args:
            text (str): Input text.
            lang (str): Language code ('en', 'fr', 'auto'). Defaults to 'auto'.

        Returns:
             tuple[list[str], set[str]]:
                 - A list of sentences from the input text.
                 - A set of wanings if any.
        """
        return self._split_by_sentence(text, lang)
