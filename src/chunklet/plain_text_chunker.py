from typing import Any, Literal, Callable, Generator, Annotated
from collections.abc import Iterable
import sys
import copy
import regex as re
from box import Box
from functools import partial
from pydantic import Field
from loguru import logger

from chunklet.sentence_splitter import SentenceSplitter, BaseSplitter
from chunklet.utils.validation import validate_input, restricted_iterable
from chunklet.utils.batch_runner import run_in_batch
from chunklet.utils.token_utils import count_tokens
from chunklet.exceptions import (
    InvalidInputError,
    MissingTokenCounterError,
    CallbackError,
)


# for clauses overlapping and fitting
CLAUSE_END_TRIGGERS = r";,’：—)&…"


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
        sentence_splitter: Any | None = None,
        verbose: bool = False,
        continuation_marker: str = "...",
        token_counter: Callable[[str], int] | None = None,
    ):
        """
        Initialize The PlainTextChunker.

        Args:
            sentence_splitter (BaseSplitter | None): An optional BaseSplitter instance.
                If None, a default SentenceSplitter will be initialized.
            verbose (bool): Enable verbose logging.
            continuation_marker (str): The marker to prepend to unfitted clauses. Defaults to '...'.
            token_counter (Callable[[str], int] | None): Function that counts tokens in text.
                If None, must be provided when calling chunk() methods.

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

        # Initialize SentenceSplitter
        self.sentence_splitter = sentence_splitter or SentenceSplitter()
        self.sentence_splitter.verbose = self._verbose
        
        # Regex to split clauses inside sentences by clause-ending punctuation
        self.clause_end_regex = re.compile(rf"(?<=[{CLAUSE_END_TRIGGERS}])\s")

    @property
    def verbose(self) -> bool:
        """Get the verbosity status."""
        return self._verbose

    @verbose.setter
    def verbose(self, value: bool):
        """Set the verbosity and propagate to sentence_splitter."""
        self._verbose = value
        self.sentence_splitter.verbose = value

    def _find_span(self, text_portion: str, full_text: str) -> tuple[int, int]:
        """
        Finds the start and end indices of a text portion within a larger text,
        using a fuzzy match that ignores punctuation and extra whitespace.

        Args:
            text_portion (str): The smaller text to find.
            full_text (str): The larger text to search within.

        Returns:
            tuple[int, int]: A tuple containing the start and end indices of the match,
                or (-1, -1) if no match is found.
        """
        # Split the portion text by punctuation and whitespace
        words = [w for w in re.split(r"[\p{P}\p{Z}\n]+", text_portion) if w.strip()]

        if not words:
            return -1, -1

        # Build a fuzzy match pattern, allowing for punctuation and whitespace between words
        pattern = r"".join(rf"{word}[\p{{P}}\p{{Z}}\n]{{0,4}}" for word in words)

        # Search for the pattern in the full text
        match = re.search(pattern, full_text, re.I)

        if match:
            return match.span()
        return -1, -1

    def _create_chunk_boxes(
        self,
        chunks: Iterable[str],
        base_metadata: dict[str, Any],
        text: str,
    ) -> list[Box]:
        """
        Helper to create a list of Box objects for chunks with embedded metadata and auto-assigned chunk numbers.

        Args:
            chunks (Iterable[str]): An iterable (e.g., list or generator) of raw text strings,
                each representing a chunk of content.
            base_metadata (dict[str, Any]): A dictionary containing document-level metadata
                (e.g., 'source' file path, 'page_count' for PDFs) to be embedded
                into each chunk's metadata.
            text (str): The full original text to find the span of the chunk within.

        Returns:
            list[Box]: A list of `Box` objects. Each `Box` contains:
                - 'content' (str): The text of the chunk.
                - 'metadata' (dict): A dictionary including 'chunk_num' (int)
                    and all key-value pairs from `base_metadata`.
        """
        chunk_boxes = []
        for i, chunk_str in enumerate(chunks, start=1):
            chunk_box = Box()
            chunk_box.content = chunk_str.strip()
            chunk_box.metadata = copy.deepcopy(base_metadata)
            chunk_box.metadata.chunk_num = i
            chunk_box.metadata.span = self._find_span(chunk_str, text)
            chunk_boxes.append(chunk_box)
        return chunk_boxes

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
        detected_clauses = [
            clause for sent in sentences for clause in self.clause_end_regex.split(sent)
        ]

        overlap_num = round(len(detected_clauses) * overlap_percent / 100)

        if overlap_num == 0:
            return []

        overlapped_clauses = detected_clauses[-overlap_num:]

        # The Condition to add the continuation marker
        if ( 
            overlapped_clauses 
            and overlapped_clauses[0] 
            and not overlapped_clauses[0][0].isupper()
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
        parts = re.split(r"[ /\\]", text)
        token_count = 0
        fitted_parts = []
        for part in parts:
            part_tokens = count_tokens(part + "...", token_counter)
            if token_count + part_tokens > max_tokens:
                break
            fitted_parts.append(part)
        return " ".join(fitted_parts) + "..."

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
                        curr_chunk = [self._resolve_unpunctuated_text(
                            text=sentences[index],
                            max_tokens=max_tokens,
                            token_counter=token_counter,
                        )]
                        index += 1
                        continue
                        
                    curr_chunk.append(fitted)
                    should_move_forward = fitted and not unfitted

                else:  # If in mode sentence
                    should_move_forward = True
                    unfitted = ""

                chunks.append("\n".join(curr_chunk))  # Considered complete 
                
                # Prepare data for next chunk
                curr_chunk = self._get_overlap_clauses(curr_chunk, overlap_percent)

                if mode in {"token", "hybrid"}:
                    token_count = sum(count_tokens(s, token_counter) for s in curr_chunk)
                    
                sentence_count = len(curr_chunk)  # considered as sentences
            
                if should_move_forward:  
                    index += 1 
                else:
                    sentences[index] = unfitted

            else:
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
        max_tokens: Annotated[int, Field(ge=12)] = 256,
        max_sentences: Annotated[int, Field(ge=1)] = 12,
        overlap_percent: Annotated[int, Field(ge=0, le=75)] = 20,
        offset: Annotated[int, Field(ge=0)] = 0,
        token_counter: Callable[[str], int] | None = None,
        base_metadata: dict[str, Any] | None = None,
    ) -> list[Box]:
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
            token_counter (callable | None): Optional token counting function.
                Required for token-based modes only.
            base_metadata (dict[str, Any] | None): Optional dictionary to be included with each chunk.

        Returns:
            list[Box]: A list of `Box` objects, each containing the chunk content and metadata.

        Raises:
            InvalidInputError: If any chunking configuration parameter is invalid.
            MissingTokenCounterError: If `mode` is "token" or "hybrid" but no `token_counter` is provided.
            CallbackError: If an error occurs during sentence splitting or token counting within a chunking task.
        """
        if self.verbose:
            logger.info(
                "Starting chunk processing for text starting with: {}.",
                f"{text[:100]}...",
            )

        if mode in {"token", "hybrid"} and not (token_counter or self.token_counter):
            raise MissingTokenCounterError()

        # Adjust limits based on mode
        if mode == "sentence":
            max_tokens = sys.maxsize
        elif mode == "token":
            max_sentences = sys.maxsize

        if not text.strip():
            if self.verbose:
                logger.info("Input text is empty. Returning empty list.")
            return []

        try:
            sentences = self.sentence_splitter.split(
                text,
                lang,
            )
        except Exception as e:
            raise CallbackError(
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

        chunks = self._group_by_chunk(
            sentences[offset:],
            mode=mode,
            token_counter=token_counter or self.token_counter,
            max_tokens=max_tokens,
            max_sentences=max_sentences,
            overlap_percent=overlap_percent,
        )

        if base_metadata is None:
            base_metadata = {}

        return self._create_chunk_boxes(chunks, base_metadata, text)

    @validate_input
    def batch_chunk(
        self,
        texts: restricted_iterable(str),
        *,
        lang: str = "auto",
        mode: Literal["sentence", "token", "hybrid"] = "sentence",
        max_tokens: Annotated[int, Field(ge=12)] = 256,
        max_sentences: Annotated[int, Field(ge=1)] = 12,
        overlap_percent: Annotated[int, Field(ge=0, le=75)] = 20,
        offset: Annotated[int, Field(ge=0)] = 0,
        token_counter: Callable[[str], int] | None = None,
        separator: Any = None,
        base_metadata: dict[str, Any] | None = None,
        n_jobs: Annotated[int, Field(ge=1)] | None = None,
        show_progress: bool = True,
        on_errors: Literal["raise", "skip", "break"] = "raise",
    ) -> Generator[Any, None, None]:
        """
        Processes a batch of texts in parallel, splitting each into chunks.
        Leverages multiprocessing for efficient batch chunking.

        If a task fails, `chunklet` will now stop processing and return the results
        of the tasks that completed successfully, preventing wasted work.

        Args:
            texts (restricted_iterable[str]): A restricted iterable of input texts to be chunked.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto'). Defaults to "auto".
            mode (Literal["sentence", "token", "hybrid"]): Chunking mode. Defaults to "sentence".
            max_tokens (int): Maximum number of tokens per chunk.
            max_sentences (int): Maximum number of sentences per chunk.
            overlap_percent (int | float): Percentage of overlap between chunks (0-85).
            offset (int): Starting sentence offset for chunking. Defaults to 0.
            token_counter (callable | None): The token counting function.
            separator (Any): A value to be yielded after the chunks of each text are processed.
                Note: None cannot be used as a separator.
            base_metadata (dict[str, Any] | None): Optional dictionary to be included with each chunk.
                Required for token-based modes only.
            n_jobs (int | None): Number of parallel workers to use. If None, uses all available CPUs.
                Must be >= 1 if specified.
            show_progress (bool): Flag to show or disable the loading bar.
            on_errors (Literal["raise", "skip", "break"]): How to handle errors during processing.
                Defaults to 'raise'.

        Yields:
            Any: A `Box` object containing the chunk content and metadata, or any separator object.

        Raises:
            InvalidInputError: If `texts` is not an iterable of strings, or if `n_jobs` is less than 1.
            MissingTokenCounterError: If `mode` is "token" or "hybrid" but no `token_counter` is provided.
            CallbackError: If an error occurs during sentence splitting
                or token counting within a chunking task.
        """
        chunk_func = partial(
            self.chunk,
            lang=lang,
            mode=mode,
            max_tokens=max_tokens,
            max_sentences=max_sentences,
            overlap_percent=overlap_percent,
            offset=offset,
            base_metadata=base_metadata,
            token_counter=token_counter or self.token_counter,
        )

        yield from run_in_batch(
            func=chunk_func,
            iterable_of_args=texts,
            iterable_name="texts",
            n_jobs=n_jobs,
            show_progress=show_progress,
            on_errors=on_errors,
            separator=separator,
            verbose=self.verbose,
        )
