import sys
import regex as re
from itertools import tee
from typing import Any, Optional, Literal, Callable, Generator
from collections.abc import Iterable, Iterator
from pydantic import conint
import enlighten   
from loguru import logger
# mpire is lazy imported

from chunklet.sentence_splitter import SentenceSplitter, BaseSplitter
from chunklet.utils.validation import validate_input
from chunklet.utils.token_utils import count_tokens
from chunklet.exceptions import (
    InvalidInputError,
    MissingTokenCounterError,
    CallbackExecutionError,
)

# for clauses overlapping and fitting
CLAUSE_END_TRIGGERS = r";,’：—)&…"

# Sentinel to serve as the default value for the separator args in batch chunking
_sentinel = object()


class PlainTextChunker:
    """
    A powerful text chunking utility offering flexible strategies for optimal text segmentation.

    Key Features:
    - Multiple Chunking Modes: Split text by sentence count, token count, or a hybrid approach.
    - Clause-Level Overlap: Ensures semantic continuity between chunks by overlapping
    at natural clause boundaries with Customizable continuation marker.
    - Multilingual Support: Leverages language-specific algorithms and detection for broad coverage.
    - Pluggable Token Counters: Integrate custom token counting functions (e.g., for specific LLM tokenizers).
    - Parallel Processing: Efficiently handles batch chunking of multiple texts using multiprocessing.
    - Memory friendly batching: Yields chunks one at a time, reducing memory usage, especially for very large documents.
    """

    @validate_input
    def __init__(
        self,
        verbose: bool = True,
        continuation_marker: str = "...",
        token_counter: Callable[[str], int] | None = None,
        sentence_splitter: Any | None = None,
    ):
        """
        Initialize Chunklet settings.

        Args:
            verbose (bool): Enable verbose logging.
            continuation_marker (str): The marker to prepend to unfitted clauses. Defaults to '...'.
            token_counter (Callable[[str], int] | None): Function that counts tokens in text.
                If None, must be provided when calling chunk() methods.
            sentence_splitter (BaseSplitter | None): An optional BaseSplitter instance.
                If None, a default SentenceSplitter will be initialized.

        Raises:
            InvalidInputError: If any of the input arguments are invalid or if the provided `sentence_splitter` is not an instance of `BaseSplitter`.
        """
        self._verbose = verbose
        self.token_counter = token_counter
        self.continuation_marker = continuation_marker

        if sentence_splitter is not None and not isinstance(
            sentence_splitter, BaseSplitter
        ):
            raise InvalidInputError(
                f"The provided sentence_splitter must be an instance of BaseSplitter, "
                f"but got {type(sentence_splitter).__name__}."
            )

        if self._verbose:
            logger.debug(
                "PlainTextChunker initialized with verbose={}, Default token counter is {}provided.",
                self._verbose,
                "not " if self.token_counter is None else "",
            )

        # Regex to split clauses inside sentences by clause-ending punctuation
        self.clause_end_regex = re.compile(rf"(?<=[{CLAUSE_END_TRIGGERS}])\s")

        # Initialize SentenceSplitter
        self.sentence_splitter = (
            sentence_splitter
            if sentence_splitter
            else SentenceSplitter(verbose=self._verbose)
        )

    @property
    def verbose(self) -> bool:
        """Get the verbosity status."""
        return self._verbose

    @verbose.setter
    def verbose(self, value: bool):
        """Set the verbosity and propagate to sentence_splitter."""
        self._verbose = value
        self.sentence_splitter.verbose = value

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
            clause_tokens = count_tokens(clauses[i], token_counter)

            if clause_tokens <= remaining_tokens:
                fitted.append(clauses[i])
                remaining_tokens -= clause_tokens
            else:
                unfitted = clauses[i:]
                break

        return " ".join(fitted), " ".join(unfitted)

    def _resolve_unpunctuated_text(
        self,
        text: str,
        max_tokens: int,
        token_counter: Callable[[str], int],
    ) -> str:
        """
        Applies greedy token cutoff to a long, unpunctuated string.

        Splits the text into segments (words/parts) and greedily adds them
        to a 'fitted' part until the max_tokens limit is reached.

        Args:
            text (str): The input string to be processed.
            max_tokens (int): The maximum number of tokens allowed in the fitted part.
            token_counter (Callable): The function used to count tokens.

        Returns:
            str: The fitted part of the text, truncated to fit within max_tokens.
        """
        segments = re.split(r"[ /\\]", text)
        token_count = 0
        parts = []
        for part in segments:
            part_tokens = count_tokens(part + "...", token_counter)
            if token_count + part_tokens > max_tokens:
                break
            parts.append(part)
        return " ".join(parts) + "..."

    def _group_by_chunk(
        self,
        sentences: list[str],
        mode: str,
        token_counter: Callable[[str], int],
        max_tokens: int,
        max_sentences: int,
        overlap_percent: int | float,
    ) -> list[str]:
        """
        Groups sentences into chunks based on the specified mode and constraints.
        Applies overlap logic between consecutive chunks.

        Args:
            sentences lList): A list of sentences to be chunked.
            mode (str): Chunking mode ('sentence', 'token', or 'hybrid').
            token_counter (Callable): The token counting function.
            max_tokens (int): Maximum number of tokens per chunk.
            max_sentences (int): Maximum number of sentences per chunk.
            overlap_percent (int | float): Percentage of overlap between chunks.

        Returns:
            list[str]: A list of chunk strings.
        """
        chunks = []
        curr_chunk = []
        token_count = 0
        sentence_count = 0

        index = 0
        while index < len(sentences):
            if mode in {"token", "hybrid"}:
                sentence_tokens = count_tokens(sentences[index], token_counter)
            else:
                sentence_tokens = 0

            sentence_limit_reached = sentence_count + 1 > max_sentences
            token_limit_reached = token_count + sentence_tokens > max_tokens

            if sentence_limit_reached or token_limit_reached:
                # for token-based mode, try splitting further
                if token_limit_reached:
                    remaining_tokens = max_tokens - token_count
                    fitted, unfitted = self._find_clauses_that_fit(
                        sentences[index],
                        remaining_tokens,
                        token_counter,
                    )

                    # --- Handle long, unpunctuated sentences with Greedy Token Cutoff ---
                    # This applies if the sentence itself is too long for a single chunk
                    # This is likely a long string with no clause breaks
                    # and _find_clauses_that_fit would return it as unfitted.
                    # (e.g, urls, bad formated text, image uris).
                    if not curr_chunk and not fitted and unfitted:
                        chunks.append(
                            self._resolve_unpunctuated_text(
                                text=sentences[index],
                                max_tokens=max_tokens,
                                token_counter=token_counter,
                            )
                        )
                        index += 1
                        continue  # Move to next iteration

                    curr_chunk.append(fitted)
                    chunks.append("\n".join(curr_chunk))  # Considered complete

                else:  # If in mode sentence
                    chunks.append("\n".join(curr_chunk))  # Considered complete
                    unfitted = ""
                    index += 1

                # Prepare data for next chunk
                overlap_clauses = self._get_overlap_clauses(curr_chunk, overlap_percent)
                # New current chunk
                unfitted = [unfitted] if unfitted else []
                curr_chunk = overlap_clauses + unfitted

                # Incrementally update token_count for the new curr_chunk
                if mode in {"token", "hybrid"}:
                    token_count = sum(
                        count_tokens(s, token_counter)
                        for s in overlap_clauses + unfitted
                    )
                sentence_count = len(curr_chunk)  # considered as sentences

            else:
                if index < len(sentences):
                    curr_chunk.append(sentences[index])
                token_count += sentence_tokens
                sentence_count += 1
                index += 1

        # Add any remnants
        if curr_chunk:
            chunks.append("\n".join(curr_chunk))

        return chunks

    @validate_input
    def chunk(
        self,
        text: str,
        *,
        lang: str = "auto",
        mode: Literal["sentence", "token", "hybrid"] = "sentence",
        max_tokens: conint(ge=30) = 256,
        max_sentences: conint(ge=1) = 12,
        overlap_percent: conint(ge=0, le=75) = 20,
        offset: conint(ge=0) = 0,
        token_counter: Callable[[str], int] | None = None,
    ) -> list[str]:
        """
        Chunks a single text into smaller pieces based on specified parameters.
        Supports multiple chunking modes (sentence, token, hybrid), clause-level overlap,
        and custom token counters.

        Args:
            text (str): The input text to chunk.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto'). Defaults to "auto".
            mode (Literal["sentence", "token", "hybrid"]): Chunking mode. Defaults to "sentence".
            max_tokens (int): Maximum number of tokens per chunk. Defaults to 512.
            max_sentences (int): Maximum number of sentences per chunk. Defaults to 12.
            overlap_percent (int | float): Percentage of overlap between chunks (0-75). Defaults to 20
            offset (int): Starting sentence offset for chunking. Defaults to 0.
            token_counter (callable | None): Optional token counting function. Required for token-based modes only.

        Returns:
            list[str]: A list of chunk strings.

        Raises:
            InvalidInputError: If any chunking configuration parameter is invalid.
            MissingTokenCounterError: If `mode` is "token" or "hybrid" but no `token_counter` is provided.
            CallbackExecutionError: If an error occurs during sentence splitting
            or token counting within a chunking task.
        """
        if mode in {"token", "hybrid"} and not (token_counter or self.token_counter):
            raise MissingTokenCounterError()

        if self.verbose:
            logger.info("Starting chunk processing for text: {}. .", f"{text[:150]}...")

        # Adjust limits based on mode
        if mode == "sentence":
            max_tokens = sys.maxsize
        elif mode == "token":
            max_sentences = sys.maxsize

        if not text:
            if self.verbose:
                logger.info("Input text is empty. Returning empty list.")
            return []

        try:
            sentences = self.sentence_splitter.split(
                text,
                lang,
            )
        except Exception as e:
            raise CallbackExecutionError(
                f"An error occurred during the sentence splitting process.\nDetails: {e}\n"
                "💡 Hint: This may be due to an issue with the underlying sentence splitting library."
            ) from e

        if not sentences:
            return []

        offset = round(offset)
        if offset >= len(sentences):
            logger.warning(
                "Offset {} >= total sentences {}. Returning empty list.",
                offset,
                len(sentences),
            )
            return []

        sentences = sentences[offset:]
        chunks = self._group_by_chunk(
            sentences,
            mode=mode,
            token_counter=token_counter or self.token_counter,
            max_tokens=max_tokens,
            max_sentences=max_sentences,
            overlap_percent=overlap_percent,
        )
        if self.verbose:
            logger.info(
                "Generated {} chunks for text: {}. .\n", len(chunks), f"{text[:150]}..."
            )
        return chunks

    @validate_input
    def batch_chunk(
        self,
        texts: Iterable[str],
        *,
        lang: str = "auto",
        mode: Literal["sentence", "token", "hybrid"] = "sentence",
        max_tokens: conint(ge=30) = 256,
        max_sentences: conint(ge=1) = 12,
        overlap_percent: conint(ge=0, le=75) = 20,
        offset: conint(ge=0) = 0,
        token_counter: Callable[[str], int] | None = None,
        n_jobs: Optional[int] = None,
        show_progress: bool = True,
        on_errors: Literal["raise", "skip", "break"] = "raise",
        separator: Any = _sentinel,
        _document_context: bool = False,
    ) -> Generator[Any, None, None]:
        """
        Processes a batch of texts in parallel, splitting each into chunks.
        Leverages multiprocessing for efficient batch chunking.

        If a task fails, `chunklet` will now stop processing and return the results
        of the tasks that completed successfully, preventing wasted work.

        Args:
            texts (Iterable[str]): An list or generator of input texts to be chunked. Each text will be processed independently.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto'). Defaults to "auto".
            mode (Literal["sentence", "token", "hybrid"]): Chunking mode. Defaults to "sentence".
            max_tokens (int): Maximum number of tokens per chunk.
            max_sentences (int): Maximum number of sentences per chunk.
            overlap_percent (int | float): Percentage of overlap between chunks (0-85).
            offset (int): Starting sentence offset for chunking. Defaults to 0.
            token_counter (callable | None): The token counting function. Required for token-based modes only.
            n_jobs (int | None): Number of parallel workers to use. If None, uses all available CPUs.
                   Must be >= 1 if specified.
            show_progress (bool): Flag to show or disable the loading bar.
            on_errors (Literal["raise", "skip", "break"]):
                How to handle errors during processing. Defaults to 'raise'.
            separator (Any): A value to be yielded after the chunks of each text are processed.

        yields:
            str: A chunk string.
            Any: The separator value, if provided.

        Raises:
            InvalidInputError: If `texts` is not an iterable of strings, or if `n_jobs` is less than 1.
            MissingTokenCounterError: If `mode` is "token" or "hybrid" but no `token_counter` is provided.
            CallbackExecutionError: If an error occurs during sentence splitting or token counting within a chunking task.
        """
        if isinstance(texts, str):
            raise InvalidInputError(
                "Invalid input for [texts]: Single string must be passed to the .chunk() method, not .batch_chunk()."
            )

        def _validate_entry(entry):
            if not isinstance(entry, str):
                raise InvalidInputError(
                    f"The 'texts' iterable should only contain strings, "
                    f"but found the value '{entry}' [type={type(entry).__name__}].\n"
                    "💡 Hint: Please make sure all items provided to 'batch_chunk' are strings."
                )
            return 1

        if n_jobs is not None and n_jobs < 1:
            raise InvalidInputError(
                "The 'n_jobs' parameter must be an integer greater than or equal to 1, or None.\n"
                "💡 Hint: Use `n_jobs=None` to use all available CPU cores."
            )

        # Use tee to create two independent iterators, so we can count safely to prevent exhaustion.
        if isinstance(texts, Iterator):
            texts_for_total, texts_for_processing = tee(texts)

        else:
            texts_for_processing, texts_for_total = texts, texts

        # Calculate while validating each entry
        total_texts = sum(_validate_entry(entry) for entry in texts_for_total)

        if self.verbose:
            logger.info(
                "Processing {} text(s) in batch mode with n_jobs={}.",
                total_texts,
                n_jobs if n_jobs is not None else "default",
            )

        if total_texts == 0:
            if self.verbose:
                logger.info("Input texts is empty. Returning empty iterator.")
            return iter([])

        # Wrapper to capture result/exception
        def chunk_func(text: str):
            try:
                res = self.chunk(
                    text=text,
                    lang=lang,
                    mode=mode,
                    max_tokens=max_tokens,
                    max_sentences=max_sentences,
                    overlap_percent=overlap_percent,
                    offset=offset,
                    token_counter=token_counter or self.token_counter,
                )
                return res, None
            except Exception as e:
                return None, e
        
        from mpire import WorkerPool  # Lazy import

        manager = enlighten.get_manager()
        pbar = manager.counter(total=total_texts, desc="Chunking texts...", unit="ticks", color="green")
        if not show_progress:
            manager.stop()
                
        successful_texts = 0
        failed_texts = 0
        try:    
            with WorkerPool(n_jobs=n_jobs) as executor:
                task_iter = executor.imap(
                    func=chunk_func,
                    iterable_of_args=texts_for_processing,
                    iterable_len=total_texts,  # Provided for Iterators
                )

                for result, error in task_iter:
                    pbar.update()
                        
                    if error:
                        failed_texts += 1
                        if on_errors == "raise":
                            raise error
                        elif on_errors == "break":
                            logger.error(
                                "A task in 'batch_chunk' failed. Returning partial results.\n"
                                f"💡 Hint: Check the logs for more details about the failed task. \nReason: {error}"
                            )
                            break
                        else:  # skip
                            logger.warning(f"Skipping a failed task. \nReason: {error}")
                            continue

                    if _document_context:  # Needed by document chunker
                        yield result
                    else:
                        yield from result
                        if separator is not _sentinel:
                            yield separator
                    successful_texts += 1
                    
        finally:
            if self.verbose:
                logger.info(
                    "Batch processing completed: {} successful, {} failed, {} total",
                    successful_texts, failed_texts, total_texts
                )
            manager.stop() # Ensure manager is stopped

