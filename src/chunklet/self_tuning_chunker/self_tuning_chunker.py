"""
A self-tuning chunker inspired by the "Adaptive Chunking" technique (Machine
Learning Mastery, "Essential Chunking Techniques for Building Better LLM
Applications"): chunking parameters are adjusted dynamically based on measured
content characteristics instead of using fixed limits.
"""

import copy
import os
from collections import defaultdict
from collections.abc import Iterator
from functools import partial
from itertools import pairwise
from pathlib import Path
from typing import Annotated, Any, Callable, Generator, Literal

from pydantic import Field

from chunklet import CodeChunker, DocumentChunker
from chunklet.code_chunker.patterns import FUNCTION_DECLARATION
from chunklet.common.batch_runner import run_in_batch
from chunklet.common.dotdict import DotDict
from chunklet.common.logging_utils import log_info
from chunklet.common.path_utils import is_binary_file, read_text_file
from chunklet.common.token_utils import count_tokens
from chunklet.common.validation import IterableOfPath, IterableOfStr, validate_input
from chunklet.document_chunker._plain_text_chunker import SECTION_BREAK_PATTERN
from chunklet.exceptions import UnsupportedFileTypeError
from chunklet.self_tuning_chunker.utils import is_code_like
from chunklet.sentence_splitter._universal_splitter import UniversalSplitter

COMMON_CODE_FILE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".java",
    ".c",
    ".h",
    ".cpp",
    ".cs",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".swift",
    ".kt",
    ".scala",
    ".sh",
    ".sql",
    ".lua",
    ".r",
    ".jl",
    ".dart",
    ".zig",
    ".bash",
}

# Constant for KAMA
ER_PERIOD = 10
FAST_SC = 2 / 3
SLOW_SC = 2 / 31

# Metric constants
IDEAL_LINES_PER_FUNCTION = 15
TOKEN_SAMPLE_SIZE = 5
MIN_SENTENCES_PER_PARAGRAPH = 2.0
MAX_SENTENCES_PER_PARAGRAPH = 25.0
SECTION_DENSITY_THRESHOLD = 0.75
N_JOBS = 4

DEFAULT_LEARNED_STATE = {
    "document": {
        "max_sentences": 7.0,
        "header_density_ratio": 0.05,
        "max_section_breaks": 1,
        "max_tokens": 512.0,
    },
    "code": {"max_lines": 15.0, "max_functions": 1, "max_tokens": 512.0},
}


class SelfTuningChunker:
    """Self-tune chunk boundaries for mixed text/code corpora from learned profiles.

    The chunker maintains an Kaufman Adaptive Moving Average of structural metrics per
    content profile and uses the resulting estimates to size the chunk boundaries
    for each source it processes.

    Key Features:
        - Profile-based dispatch: classifies each source as code or document via heuristic.
        - Learning memory (KAMA profiles): persists per-profile stats via Kaufman Adaptive Moving Average.
        - Self-tuning limits: derives constraints from the learned profile each time instead of using fixed values.
        - Enriched chunk metadata: adds inferred_type to each chunk.
    """

    @validate_input
    def __init__(
        self,
        lang: str,
        token_counter: Callable[[str], int] | None = None,
        hard_token_limit: int = 1024,
        initial_state: dict | None = None,
        verbose: bool = False,
    ):
        """
        Initializes the SelfTuningChunker.

        Args:
            lang: Language code (e.g., 'en', 'fr', 'auto'). Required; pass 'auto'
                to auto-detect per source (needs the `[self-tuning]` extra).
            token_counter: Function that counts tokens in text.
                If None, token-based limits and max_tokens learning are disabled.
            hard_token_limit: Ceiling for the dynamically grown ``max_tokens``.
            initial_state: Optional pre-calculated running average to seed the learned
                profiles (e.g. exported from a previous ``learned_state``). Missing
                profiles or metrics fall back to the built-in defaults.
            verbose: Enable verbose logging.
        """
        self._verbose = verbose
        self._lang = lang
        self.token_counter = token_counter
        self.hard_token_limit = hard_token_limit

        self.histories = defaultdict(list)
        self.learned_state = self._merge_initial_state(initial_state)

        self._sentence_splitter = UniversalSplitter()

        # Initialize chunkers with sensible defaults; constraint attributes are
        # mutated per request from the learned params.
        self.document_chunker = DocumentChunker(
            lang=self._lang,
            max_sentences=7,
            token_counter=self.token_counter,
            verbose=self._verbose,
        )
        self.code_chunker = CodeChunker(
            max_lines=15,
            token_counter=self.token_counter,
            verbose=self._verbose,
        )

    @property
    def lang(self) -> str:
        """Get the chunking language code."""
        return self._lang

    @lang.setter
    def lang(self, value: str) -> None:
        """Set the chunking language and propagate to the document chunker."""
        self._lang = value
        self.document_chunker.lang = value

    @property
    def verbose(self) -> bool:
        """Get the verbosity status."""
        return self._verbose

    @verbose.setter
    def verbose(self, value: bool) -> None:
        """Set the verbosity and propagate to the underlying chunkers."""
        self._verbose = value
        self.document_chunker.verbose = value
        self.code_chunker.verbose = value

    def _update_kama(self, profile_type: str, key: str, current_value: float) -> None:
        """Update the given profile metric with an Kaufman Adaptive Moving Average."""
        history = self.histories[(profile_type, key)]
        previous_kama = self.learned_state[profile_type][key]

        history.append(current_value)

        # KAMA needs ER_PERIOD + 1 observations to measure efficiency
        if len(history) <= ER_PERIOD:
            smoothing_constant = SLOW_SC
        else:
            net_movement = abs(history[-1] - history[-1 - ER_PERIOD])
            recent_values = history[-(ER_PERIOD + 1) :]
            total_movement = sum(
                abs(curr - prev) for prev, curr in pairwise(recent_values)
            )

            # Map efficiency onto the fast/slow smoothing range
            # to obtain KAMA's adaptive smoothing constant
            efficiency_ratio = (
                (net_movement / total_movement) if total_movement else 0.0
            )
            smoothing_constant = (efficiency_ratio * (FAST_SC - SLOW_SC) + SLOW_SC) ** 2

        # Move only a fraction of the gap toward the new observation
        self.learned_state[profile_type][key] = previous_kama + smoothing_constant * (
            current_value - previous_kama
        )

    @staticmethod
    def _merge_initial_state(initial_state: dict | None) -> dict:
        """Build a learned-state dict from defaults, overlaying a provided baseline.

        Args:
            initial_state: Optional profile mapping to seed the learned state with.
                Profiles or metrics not present fall back to the built-in defaults.

        Returns:
            A fresh learned-state dict safe to mutate per instance.

        Raises:
            ValueError: If initial_state contains an unknown profile name.
        """
        state = copy.deepcopy(DEFAULT_LEARNED_STATE)
        if initial_state is None:
            return state

        for profile, metrics in initial_state.items():
            if profile not in state:
                raise ValueError(
                    f"Unknown profile '{profile}' in initial_state. "
                    f"Supported profiles: {sorted(state)}"
                )
            state[profile].update(metrics)

        return state

    def _detect_file_type(
        self, text_or_file: str | Path
    ) -> Literal["document", "code"]:
        """Detect a text/file's type by extension, binary sniffing, and content.

        Fast extension-based routing first: known document formats and common code
        extensions are decided without reading the file. Anything else is sniffed
        for binary content and otherwise read as text and classified by
        :func:`is_code_like`.

        Args:
            text_or_file: Text or path to the file to classify.

        Returns:
            "document" or "code".

        Raises:
            UnsupportedFileTypeError: If the file is binary and has neither a
                document nor a code extension.
        """
        if isinstance(text_or_file, str):
            file_type = "code" if is_code_like(text_or_file) else "document"
            log_info(
                self._verbose, "Detected text type '{}' for {}", file_type, text_or_file
            )
            return file_type

        file = text_or_file
        ext = file.suffix
        if ext in self.document_chunker.BUILTIN_SUPPORTED_EXTENSIONS:
            file_type = "document"
        elif ext in COMMON_CODE_FILE_EXTENSIONS:
            file_type = "code"
        elif is_binary_file(file):
            raise UnsupportedFileTypeError(
                f"File type '{ext}' is not supported.\nSupported extensions are: "
                f"{self.document_chunker.BUILTIN_SUPPORTED_EXTENSIONS} + any code files"
            )
        else:
            text = read_text_file(file)
            file_type = "code" if is_code_like(text) else "document"

        log_info(self._verbose, "Detected file type '{}' for {}", file_type, file)
        return file_type

    def _fit_max_lines(self, text: str, fx_matches: list) -> None:
        """Fold the average spacing between functions into the code max_lines KAMA."""
        if len(fx_matches) < 2:
            return

        starts = [text[:start].count("\n") + 1 for _, start, _ in fx_matches]
        diffs = [abs(b - a) for a, b in pairwise(starts)]
        avg_diff = sum(diffs) / len(diffs)
        self._update_kama("code", key="max_lines", current_value=avg_diff)

    def _fit_max_functions(self, fx_matches: list) -> None:
        """Fold the 1-or-2 function-per-chunk signal into the code max_functions KAMA."""
        starts = [start for _, start, _ in fx_matches]

        if len(starts) < 2:
            return

        diffs = [abs(b - a) for a, b in pairwise(starts)]
        avg_diff = sum(diffs) / len(diffs)
        functions_per_chunk = 1 if avg_diff > IDEAL_LINES_PER_FUNCTION / 2 else 2
        self._update_kama(
            "code", key="max_functions", current_value=functions_per_chunk
        )

    def _fit_sentences_per_para(self, paragraphs: list[str]) -> None:
        """Fold the average sentences-per-paragraph into the document KAMA."""
        sentence_counts = [len(self._sentence_splitter.split(p)) for p in paragraphs]
        if not sentence_counts:
            return

        avg_sent = sum(sentence_counts) / len(sentence_counts)
        self._update_kama(
            "document",
            key="max_sentences",
            current_value=min(
                MAX_SENTENCES_PER_PARAGRAPH,
                max(MIN_SENTENCES_PER_PARAGRAPH, avg_sent),
            ),
        )

    def _fit_section_breaks(self, lines: list[str], paragraphs: list[str]) -> None:
        """Fold header density and the section-break signal into the document KAMA."""
        marker_count = sum(1 for line in lines if SECTION_BREAK_PATTERN.match(line))
        density = marker_count / max(1, len(paragraphs))
        self._update_kama(
            "document",
            key="header_density_ratio",
            current_value=density,
        )
        self._update_kama(
            "document",
            key="max_section_breaks",
            current_value=2 if density > SECTION_DENSITY_THRESHOLD else 1,
        )

    def _fit_max_tokens_code(self, text: str, starts: list[int]) -> None:
        """Fold the average token span between functions into the code max_tokens KAMA."""
        if self.token_counter is None:
            return

        if len(starts) < 2:
            return

        spans = [text[a:b] for a, b in pairwise(starts[:TOKEN_SAMPLE_SIZE])]
        self._update_kama(
            "code",
            key="max_tokens",
            current_value=(
                sum(count_tokens(s, self.token_counter) for s in spans) / len(spans)
            ),
        )

    def _fit_max_tokens_document(self, paragraphs: list[str]) -> None:
        """Fold the average paragraph token count into the document max_tokens KAMA."""
        if self.token_counter is None:
            return

        paras = paragraphs[:TOKEN_SAMPLE_SIZE]
        if not paras:
            return

        self._update_kama(
            "document",
            key="max_tokens",
            current_value=(
                sum(count_tokens(p, self.token_counter) for p in paras) / len(paras)
            ),
        )

    def _fit(self, text: str, profile_type: Literal["code", "document"]) -> None:
        """Measure structural metrics from text and fold them into the KAMA state."""
        if not text or text.isspace():
            return

        if profile_type == "code":
            fx_matches = [
                (m.group(), m.start(), m.end())
                for m in FUNCTION_DECLARATION.finditer(text)
            ]
            self._fit_max_lines(text, fx_matches)
            self._fit_max_functions(fx_matches)
            starts = [start for _, start, _ in fx_matches]
            self._fit_max_tokens_code(text, starts)
        else:
            lines = text.splitlines()
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            self._fit_sentences_per_para(paragraphs)
            self._fit_section_breaks(lines, paragraphs)
            self._fit_max_tokens_document(paragraphs)

    @validate_input
    def chunk_text(
        self,
        text: str,
        base_metadata: dict[str, Any] | None = None,
        file_type: Literal["document", "code"] | None = None,
        _already_fitted: bool = False,
    ) -> list[DotDict]:
        """Chunks raw text content using the constraints configured at initialization.

        Args:
            text: The raw text to fit and chunk.
            base_metadata: Optional dictionary to be included with each chunk.
            file_type: Optional file type.
            _already_fitted: internal param to avoid double fitting.

        Returns:
            A list of `DotDict` objects, each representing a chunk.
        """

        file_type = file_type or self._detect_file_type(text)
        if not _already_fitted:
            self._fit(text, file_type)

        learned_state = self.learned_state[file_type]
        if file_type == "code":
            self.code_chunker.token_counter = self.token_counter
            self.code_chunker.max_tokens = (
                min(self.hard_token_limit, learned_state["max_tokens"])
                if self.token_counter
                else None
            )
            self.code_chunker.max_lines = learned_state["max_lines"]
            self.code_chunker.max_functions = round(learned_state["max_functions"])

            chunks = self.code_chunker.chunk_text(
                text,
                token_counter=self.token_counter,
                strict=False,
                base_metadata=base_metadata,
            )
        else:
            self.document_chunker.max_tokens = (
                min(self.hard_token_limit, learned_state["max_tokens"])
                if self.token_counter
                else None
            )
            self.document_chunker.max_sentences = int(learned_state["max_sentences"])
            self.document_chunker.max_section_breaks = round(
                learned_state["max_section_breaks"]
            )

            chunks = self.document_chunker.chunk_text(
                text, token_counter=self.token_counter, base_metadata=base_metadata
            )

        for chunk in chunks:
            chunk["metadata"]["inferred_type"] = file_type

        return chunks

    @validate_input
    def chunk_texts(
        self,
        texts: IterableOfStr,
        *,
        base_metadata: dict[str, Any] | None = None,
        separator: Any = None,
        n_jobs: Annotated[int, Field(ge=1)] | None = None,
        show_progress: bool = False,
        on_errors: Literal["raise", "skip", "break"] = "raise",
    ) -> Generator[DotDict, None, None]:
        """
        Chunks multiple text contents using the constraints configured
        at initialization.

        Args:
            texts: A non-string iterable of texts to chunk.
            base_metadata: Optional dictionary to be included with each chunk.
            separator: A value to be yielded after the chunks of each text are processed.
            n_jobs: Number of parallel workers.
            show_progress: Display progress bar during processing. Defaults to False.
            on_errors: How to handle errors.

        yields:
            `DotDict` object, representing a chunk with its content and metadata.

        Raises:
            InvalidInputError: If the input arguments aren't valid.
            UnsupportedFileTypeError: If the file extension is not supported or is missing.
        """

        def fit_and_stream_pairs(texts: IterableOfStr) -> Iterator:
            for text in texts:
                file_type = self._detect_file_type(text)
                self._fit(text, file_type)
                yield text, base_metadata, file_type

        chunk_func = partial(self.chunk_text, _already_fitted=True)

        yield from run_in_batch(
            func=chunk_func,
            iterable_of_args=fit_and_stream_pairs(texts),
            iterable_name="texts",
            separator=separator,
            n_jobs=n_jobs,
            show_progress=show_progress,
            on_errors=on_errors,
            verbose=self.verbose,
        )

    @validate_input
    def chunk_file(
        self,
        path: str | Path,
        file_type: Literal["document", "code"] | None = None,
        _already_fitted: bool = False,
    ) -> list[DotDict]:
        """
        Chunks a single document/code from a given path using the constraints
        configured at initialization.

        Args:
            path: The path to the document file.
            file_type: Optional file type.
            _already_fitted: internal param to avoid double fitting.

        Returns:
            A list of `DotDict` objects, each representing a chunk with its content and metadata.

        Raises:
            InvalidInputError: If the input arguments aren't valid.
            FileNotFoundError: If provided file path not found.
            UnsupportedFileTypeError: If the file extension is not supported or is missing.
        """
        path = Path(path)
        file_type = file_type or self._detect_file_type(path)

        text_or_gen, metadata = self.document_chunker.extract_text_and_metadata(
            path, path.suffix
        )

        if isinstance(text_or_gen, str):
            return self.chunk_text(
                text_or_gen,
                file_type=file_type,
                base_metadata=metadata,
                _already_fitted=_already_fitted,
            )

        chunk_func = partial(
            self.chunk_text, base_metadata=metadata, _already_fitted=True
        )

        return list(
            run_in_batch(
                func=chunk_func,
                iterable_of_args=text_or_gen,
                iterable_name="texts",
                file_type=file_type,
                n_jobs=os.cpu_count() - 1,
                verbose=self.verbose,
            )
        )

    @validate_input
    def chunk_files(
        self,
        paths: IterableOfPath,
        *,
        token_counter: Callable[[str], int] | None = None,
        separator: Any = None,
        n_jobs: Annotated[int, Field(ge=1)] | None = None,
        show_progress: bool = False,
        on_errors: Literal["raise", "skip", "break"] = "raise",
    ) -> Generator[DotDict, None, None]:
        """
        Chunks multiple documents/codes from a list of file paths using the constraints
        configured at initialization.

        This method is a memory-efficient generator that yields chunks as they
        are processed, without loading all documents into memory at once. It
        handles various file types.

        Args:
            paths: A non-string iterable of paths to the document files.
            token_counter: Optional token counting function.
            separator: A value to be yielded after the chunks of each text are processed.
                Note: None cannot be used as a separator.

            n_jobs: Number of parallel workers to use. If None, uses all available CPUs.
                   Must be >= 1 if specified.
            show_progress: Display progress bar during processing. Defaults to False.
            on_errors: How to handle errors during processing. Can be 'raise', 'ignore', or 'break'.

        yields:
            `DotDict` object, representing a chunk with its content and metadata.

        Raises:
            InvalidInputError: If the input arguments aren't valid.
            FileNotFoundError: If provided file path not found.
            UnsupportedFileTypeError: If the file extension is not supported or is missing.
            MissingTokenCounterError: If `max_tokens` is provided but no `token_counter` is provided.
            CallbackError: If a callback function (e.g., custom processors callbacks) fails during execution.
        """

        def fit_and_stream_tuples(paths: IterableOfPath) -> Iterator:
            for path in paths:
                path = Path(path)
                file_type = self._detect_file_type(path)
                text_or_gen, metadata = self.document_chunker.extract_text_and_metadata(
                    path, path.suffix
                )

                if isinstance(text_or_gen, str):
                    text_or_gen = [text_or_gen]

                for text in text_or_gen:
                    self._fit(text, file_type)
                    yield text, metadata, file_type

        chunk_func = partial(self.chunk_text, _already_fitted=True)
        yield from run_in_batch(
            func=chunk_func,
            iterable_of_args=fit_and_stream_tuples(paths),
            iterable_name="paths",
            separator=separator,
            n_jobs=n_jobs,
            show_progress=show_progress,
            on_errors=on_errors,
            verbose=self.verbose,
        )
