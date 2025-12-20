from typing import Any, Literal, Callable, Generator, Annotated
from collections.abc import Iterable
import sys
import copy
import regex as re
from box import Box
from functools import partial
from pydantic import Field
from loguru import logger

from chunklet.base_chunker import BaseChunker
from chunklet.sentence_splitter import SentenceSplitter, BaseSplitter
from chunklet.common.validation import validate_input, restricted_iterable
from chunklet.common.batch_runner import run_in_batch
from chunklet.common.token_utils import count_tokens
from chunklet.exceptions import (
    InvalidInputError,
    MissingTokenCounterError,
    CallbackError,
)


# Regex to split sentences into individual clauses
CLAUSE_END_PATTERN = re.compile(r"(?<=[;,’：—)&…])\s")

# Pattern to detect markdown headings
SECTION_BREAK_PATTERN = re.compile(
    r"^\s*#{1,6}\s*.+?$|"  # heading
    r"^\s*([\-\*_]\s*)(?:\1){2,}\s*$|"  # thematic Breaks
    r"\s*<details>",  # collapsed Sections opening
    re.M,
)


class PlainTextChunker(BaseChunker):
    """
    A powerful text chunking utility offering flexible strategies for optimal text segmentation.

    Key Features:
    - Flexible Constraint-Based Chunking: Segment text by specifying limits on sentence count, token count and section breaks or combination of them.
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
            sentence_splitter (BaseSplitter, optional): An optional BaseSplitter instance.
                If None, a default SentenceSplitter will be initialized.
            verbose (bool): Enable verbose logging.
            continuation_marker (str): The marker to prepend to unfitted clauses. Defaults to '...'.
            token_counter (Callable[[str], int], optional): Function that counts tokens in text.
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
        Find a multi-line substring inside a full text, ignoring separators
        like whitespace, newlines, and punctuation between lines.

        Args:
            text_portion: The substring (can be multi-line) to search for.
            full_text: The text to search within.

        Returns:
            A tuple (start, end) representing the span in full_text.
            Returns (-1, -1) if not found.
        """
        # Fast path for exact match
        if text_portion in full_text:
            start = full_text.find(text_portion)
            return start, start + len(text_portion)

        # Remove continuation marker from the beginning of text_portion first
        if text_portion.startswith(self.continuation_marker):
            text_portion = text_portion[len(self.continuation_marker) :].lstrip()

        lines = [line.strip() for line in text_portion.splitlines() if line.strip()]
        if not lines:
            return -1, -1

        budget = len(text_portion) // 5  # 20 %

        # Build flexible separator pattern that allows newlines, Unicode separators, and punctuation
        sep = rf"""
            [          # character class for allowed artifacts between lines
                \n     # newline characters
                \p{{Z}} # Unicode whitespace separators
                \p{{P}} # punctuation characters
            ]{{0,{budget}}}?  # bounded (0 to budget), lazy quantifier
        """

        # Join escaped lines with the separator
        pattern = sep.join(re.escape(line) for line in lines)

        m = re.search(pattern, full_text, re.M | re.VERBOSE)
        if m:
            return m.span()

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
            chunk_box.metadata["chunk_num"] = i
            chunk_box.metadata["span"] = self._find_span(chunk_str, text)
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
            clause for sent in sentences for clause in CLAUSE_END_PATTERN.split(sent)
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
    ) -> tuple[str, str]:
        """
        Splits a sentence into clauses and fits them into a token budget.

        This method takes a sentence and attempts to fit its component clauses
        into the number of remaining tokens available. It returns the fitted
        and unfitted portions as joined strings.

        Args:
            sentence (str): The input string to be split into clauses.
            remaining_tokens (int): The number of tokens available to fit clauses into.
            token_counter (Callable): The function needed for token counting.

        Returns:
            tuple[str, str]: A tuple containing two strings:
                - The clauses that fit within the token budget (joined as a string).
                - The remaining unfitted clauses (joined as a string).
        """
        clauses = CLAUSE_END_PATTERN.split(sentence)
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

    def _prepare_next_chunk(
        self,
        curr_chunk: list[str],
        overlap_percent: float,
        max_tokens: int,
        max_sentences: int,
        max_section_breaks: int,
        token_counter: Callable[[str], int] | None,
        state: dict,
    ) -> list[str]:
        """
        Prepare data for the next chunk after splitting.

        Applies overlap clauses and calculates counts for tokens, sentences, and headings
        based on the provided constraints, updating the state dict.

        Args:
            curr_chunk (list[str]): The current chunk sentences.
            overlap_percent (float): Percentage of overlap to apply.
            max_tokens (int): Maximum tokens per chunk.
            token_counter (Callable[[str], int], optional): Function to count tokens.
            max_sentences (int): Maximum sentences per chunk.
            max_section_breaks (int): Maximum section breaks per chunk.
            state (dict): State dict to update with counts.

        Returns:
            list[str]: The prepared next chunk.
        """
        next_chunk = self._get_overlap_clauses(curr_chunk, overlap_percent)

        state["token_count"] = 0
        if max_tokens != sys.maxsize:
            state["token_count"] = sum(
                count_tokens(s, token_counter) for s in next_chunk
            )

        state["sentence_count"] = 0
        if max_sentences != sys.maxsize:
            state["sentence_count"] = len(next_chunk)

        state["heading_count"] = 0
        if max_section_breaks != sys.maxsize:
            state["heading_count"] = sum(
                1 for s in next_chunk if SECTION_BREAK_PATTERN.match(s)
            )

        return next_chunk

    def _group_by_chunk(
        self,
        sentences: list[str],
        token_counter: Callable[[str], int] | None,
        max_tokens: int,
        max_sentences: int,
        max_section_breaks: int,
        overlap_percent: int | float,
    ) -> list[str]:
        """
        Groups sentences into chunks based on the specified constraints.
        Applies overlap logic between consecutive chunks.

        Args:
            sentences (list[str]): A list of sentences to be chunked.
            token_counter (Callable, optional): The token counting function.
            max_tokens (int): Maximum number of tokens per chunk.
            max_sentences (int): Maximum number of sentences per chunk.
            max_section_breaks (int, optional): Maximum number of section breaks per chunk.
            overlap_percent (int | float): Percentage of overlap between chunks.

        Returns:
            list[str]: A list of chunk strings.
        """
        chunks = []
        curr_chunk = []
        state = {
            "token_count": 0,
            "sentence_count": 0,
            "heading_count": 0,
        }

        index = 0
        while index < len(sentences):
            sentence = sentences[index]

            if SECTION_BREAK_PATTERN.match(sentence):
                is_heading = True
                sentence = "\n" + sentence
            else:
                is_heading = False

            sentence_tokens = (
                count_tokens(sentence + "\n", token_counter)
                if max_tokens != sys.maxsize
                else 0
            )

            sentence_limit_reached = state["sentence_count"] + 1 > max_sentences
            heading_limit_reached = (
                is_heading and state["heading_count"] + 1 > max_section_breaks
            )
            token_limit_reached = (
                max_tokens != sys.maxsize
                and state["token_count"] + sentence_tokens > max_tokens
            )

            if token_limit_reached or sentence_limit_reached or heading_limit_reached:
                # for token-based mode, try splitting further
                if token_limit_reached:
                    remaining_tokens = max_tokens - state["token_count"]
                    fitted, unfitted = self._find_clauses_that_fit(
                        sentence,
                        remaining_tokens,
                        token_counter,
                    )

                    # --- Handle long, unpunctuated sentences with Greedy Token Cutoff ---
                    # This applies if the sentence itself is too long for a single chunk
                    # This is likely a long string with no clause breaks
                    # and _find_clauses_that_fit would return it as unfitted.
                    # (e.g, urls, bad formated text, image uris).
                    if not curr_chunk and not fitted and unfitted:
                        curr_chunk = [
                            self._resolve_unpunctuated_text(
                                text=sentence,
                                max_tokens=max_tokens,
                                token_counter=token_counter,
                            )
                        ]
                        index += 1
                        continue

                    curr_chunk.append(fitted)

                    if unfitted:
                        # We need to process the remnants separately
                        sentences[index] = unfitted

                else:
                    unfitted = ""

                chunks.append("\n".join(curr_chunk))  # Considered complete

                curr_chunk = self._prepare_next_chunk(
                    curr_chunk=curr_chunk,
                    overlap_percent=overlap_percent,
                    max_tokens=max_tokens,
                    max_sentences=max_sentences,
                    max_section_breaks=max_section_breaks,
                    token_counter=token_counter,
                    state=state,
                )

            else:
                curr_chunk.append(sentence)
                state["token_count"] += sentence_tokens
                state["sentence_count"] += 1
                if is_heading:
                    state["heading_count"] += 1
                index += 1

        # Add the last chunk if it exists
        if curr_chunk:
            chunks.append("\n".join(curr_chunk))

        return chunks

    def _validate_constraints(
        self,
        max_tokens: int | None,
        max_sentences: int | None,
        max_section_breaks: int | None,
        token_counter: Callable[[str], int] | None,
    ) -> None:
        """
        Validate chunking constraints and raise errors if invalid.

        Ensures that at least one chunking limit is specified and that a token counter
        is available when token-based limits are used.

        Args:
            max_tokens (int | None): Maximum tokens per chunk.
            max_sentences (int | None): Maximum sentences per chunk.
            max_section_breaks (int | None): Maximum section breaks per chunk.
            token_counter (Callable[[str], int] | None): Token counting function.

        Raises:
            InvalidInputError: If no chunking limits are provided.
            MissingTokenCounterError: If token limits are set but no token counter is available.
        """
        # Validate that at least one limit is provided
        if not any((max_tokens, max_sentences, max_section_breaks)):
            raise InvalidInputError(
                "At least one of 'max_tokens', 'max_sentences', or 'max_section_break' must be provided."
            )

        # If token_counter is required but not provided
        if max_tokens is not None and not (token_counter or self.token_counter):
            raise MissingTokenCounterError()

    @validate_input
    def chunk(
        self,
        text: str,
        *,
        lang: str = "auto",
        max_tokens: Annotated[int | None, Field(ge=12)] = None,
        max_sentences: Annotated[int | None, Field(ge=1)] = None,
        max_section_breaks: Annotated[int | None, Field(ge=1)] = None,
        overlap_percent: Annotated[int, Field(ge=0, le=75)] = 20,
        offset: Annotated[int, Field(ge=0)] = 0,
        token_counter: Callable[[str], int] | None = None,
        base_metadata: dict[str, Any] | None = None,
    ) -> list[Box]:
        """
        Chunks a single text into smaller pieces based on specified parameters.
        Supports flexible constraint-based chunking, clause-level overlap,
        and custom token counters.

        Args:
            text (str): The input text to chunk.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto'). Defaults to "auto".
            max_tokens (int, optional): Maximum number of tokens per chunk. Must be >= 12.
            max_sentences (int, optional): Maximum number of sentences per chunk. Must be >= 1.
            max_section_breaks (int, optional): Maximum number of section breaks per chunk. Must be >= 1.
            overlap_percent (int | float): Percentage of overlap between chunks (0-75). Defaults to 20
            offset (int): Starting sentence offset for chunking. Defaults to 0.
            token_counter (callable, optional): Optional token counting function.
                Required for token-based modes only.
            base_metadata (dict[str, Any], optional): Optional dictionary to be included with each chunk.

        Returns:
            list[Box]: A list of `Box` objects, each containing the chunk content and metadata.

        Raises:
            InvalidInputError: If any chunking configuration parameter is invalid.
            MissingTokenCounterError: If `max_tokens` is provided but no `token_counter` is provided.
            CallbackError: If an error occurs during sentence splitting or token counting within a chunking task.
        """
        self._validate_constraints(
            max_tokens, max_sentences, max_section_breaks, token_counter
        )

        self.log_info(
            "Starting chunk processing for text starting with: {}.",
            f"{text[:100]}...",
        )

        # Adjust limits for _group_by_chunk's internal use
        if max_tokens is None:
            max_tokens = sys.maxsize
        if max_sentences is None:
            max_sentences = sys.maxsize
        if max_section_breaks is None:
            max_section_breaks = sys.maxsize

        if not text.strip():
            self.log_info("Input text is empty. Returning empty list.")
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
            token_counter=token_counter or self.token_counter,
            max_tokens=max_tokens,
            max_sentences=max_sentences,
            max_section_breaks=max_section_breaks,
            overlap_percent=overlap_percent,
        )

        # Leave the user's original dict untouched
        base_metadata = (base_metadata or {}).copy()

        return self._create_chunk_boxes(chunks, base_metadata, text)

    @validate_input
    def batch_chunk(
        self,
        texts: restricted_iterable(str),
        *,
        lang: str = "auto",
        max_tokens: Annotated[int | None, Field(ge=12)] = None,
        max_sentences: Annotated[int | None, Field(ge=1)] = None,
        max_section_breaks: Annotated[int | None, Field(ge=1)] = None,
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
            max_tokens (int, optional): Maximum number of tokens per chunk. Must be >= 12.
            max_sentences (int, optional): Maximum number of sentences per chunk. Must be >= 1.
            max_section_breaks (int, optional): Maximum number of section breaks per chunk. Must be >= 1.
            overlap_percent (int | float): Percentage of overlap between chunks (0-85).
            offset (int): Starting sentence offset for chunking. Defaults to 0.
            token_counter (callable, optional): The token counting function.
                Required if `max_tokens` is set.
            separator (Any): A value to be yielded after the chunks of each text are processed.
                Note: None cannot be used as a separator.
            base_metadata (dict[str, Any], optional): Optional dictionary to be included with each chunk.
            n_jobs (int | None): Number of parallel workers to use. If None, uses all available CPUs.
                Must be >= 1 if specified.
            show_progress (bool): Flag to show or disable the loading bar.
            on_errors (Literal["raise", "skip", "break"]): How to handle errors during processing.
                Defaults to 'raise'.

        Yields:
            Any: A `Box` object containing the chunk content and metadata, or any separator object.

        Raises:
            InvalidInputError: If `texts` is not an iterable of strings, or if `n_jobs` is less than 1.
            MissingTokenCounterError: If `max_tokens` is provided but no `token_counter` is provided.
            CallbackError: If an error occurs during sentence splitting
                or token counting within a chunking task.
        """
        chunk_func = partial(
            self.chunk,
            lang=lang,
            max_tokens=max_tokens,
            max_sentences=max_sentences,
            overlap_percent=overlap_percent,
            max_section_breaks=max_section_breaks,
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
