"""
A lightweight adaptive chunking prototype inspired by the "Adaptive Chunking"
technique (Machine Learning Mastery, "Essential Chunking Techniques for Building
Better LLM Applications"): chunking parameters are adjusted dynamically based on
measured content characteristics instead of using fixed limits.
"""

from collections import deque
from itertools import pairwise
from pathlib import Path
from typing import Annotated, Any, Callable, Generator, Literal

from pydantic import Field

from chunklet import CodeChunker, DocumentChunker
from chunklet.adaptive_chunker.utils import is_code_like
from chunklet.code_chunker.patterns import FUNCTION_DECLARATION
from chunklet.common.dotdict import DotDict
from chunklet.common.path_utils import is_binary_file, read_text_file
from chunklet.common.token_utils import count_tokens
from chunklet.common.validation import IterableOfPath, validate_input
from chunklet.document_chunker._plain_text_chunker import SECTION_BREAK_PATTERN
from chunklet.exceptions import UnsupportedFileTypeError
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

IDEAL_LINES_PER_FUNCTION = 15


class AdaptiveChunker:
    """Adaptively chunk mixed text/code corpora based on learned content profiles.

    The chunker maintains an exponential moving average of structural metrics per
    content profile and uses the resulting estimates to size the chunk boundaries
    for each source it processes.

    Key Features:
        - Profile-based dispatch: classifies each source as code or document via heuristic.
        - Learning memory (EMA profiles): persists per-profile stats via exponential moving average.
        - Adaptive limits: derives constraints from the learned profile each time instead of using fixed values.
        - Enriched chunk metadata: adds inferred_type, active_max_functions to each chunk.
    """

    @validate_input
    def __init__(
        self,
        lang: str = "auto",
        token_counter: Callable[[str], int] | None = None,
        hard_token_limit: int = 1024,
        ema_alpha: Annotated[float, Field(ge=0, le=1)] = 0.3,
        verbose: bool = False,
    ):
        """
        Initializes the AdaptativeChunker.

        Args:
            lang: Language code (e.g., 'en', 'fr', 'auto'). Defaults to auto
            token_counter: Function that counts tokens in text.
                If None, must be provided (or token-based limits disabled).
            hard_token_limit: Ceiling for the dynamically grown ``max_tokens``.
            ema_alpha: Smoothing factor in [0, 1] for the exponential moving average;
                higher values react faster to recent sources.
            verbose: Enable verbose logging.
        """
        self._verbose = verbose
        self._lang = lang
        self.token_counter = token_counter

        self.hard_token_limit = hard_token_limit
        self.ema_alpha = ema_alpha

        self.learned_state = {
            "document": {
                "max_sentences": 7.0,
                "header_density_ratio": 0.05,
                "max_section_breaks": 1,
                "max_tokens": 512.0,
            },
            "code": {"max_lines": 15.0, "max_functions": 1, "max_tokens": 512.0},
        }

        self._pending_sources = deque()
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

    def _update_ema(self, profile_type: str, key: str, current_value: float) -> None:
        """Update the given profile metric with an Exponential Moving Average.

        Args:
            profile_type: Which profile to update, "document" or "code".
            key: Metric name within the profile.
            current_value: Fresh measurement for the metric.
        """
        previous_ema = self.learned_state[profile_type][key]
        self.learned_state[profile_type][key] = (self.ema_alpha * current_value) + (
            (1.0 - self.ema_alpha) * previous_ema
        )

    def _detect_file_type(self, file: Path) -> Literal["document", "code"]:
        """Detect a file's type by extension, binary sniffing, and content.

        Fast extension-based routing first: known document formats and common code
        extensions are decided without reading the file. Anything else is sniffed
        for binary content and otherwise read as text and classified by
        :func:`is_code_like`.

        Args:
            file: Path to the file to classify.

        Returns:
            "document" or "code".

        Raises:
            UnsupportedFileTypeError: If the file is binary and has neither a
                document nor a code extension.
        """
        ext = file.suffix
        if ext in self.document_chunker.BUILTIN_SUPPORTED_EXTENSIONS:
            return "document"

        if ext in COMMON_CODE_FILE_EXTENSIONS:
            return "code"

        if is_binary_file(file):
            raise UnsupportedFileTypeError(
                f"File type '{ext}' is not supported.\nSupported extensions are: "
                f"{self.document_chunker.BUILTIN_SUPPORTED_EXTENSIONS} + any code files"
            )

        text = read_text_file(file)
        if is_code_like(text):
            return "code"

        return "document"

    def _fit_max_lines(self, text: str, fx_matches: list) -> None:
        """Fold the average spacing between functions into the code max_lines EMA.

        The pairwise gaps between consecutive function starts are collected and
        their mean is EMA-folded into max_lines.

        `text` is only used to convert each match start offset to a 1-based line
        number. Files with fewer than two functions are skipped, as no gap exists.
        """
        if len(fx_matches) < 2:
            return
        starts = [text[:start].count("\n") + 1 for _, start, _ in fx_matches]
        diffs = [abs(b - a) for a, b in pairwise(starts)]
        avg_diff = sum(diffs) / len(diffs)
        self._update_ema("code", key="max_lines", current_value=avg_diff)

    def _fit_max_functions(self, fx_matches: list) -> None:
        """Fold the 1-or-2 function-per-chunk signal into the code max_functions EMA.

        When the mean pairwise gap between function starts exceeds half of
        IDEAL_LINES_PER_FUNCTION the functions are spread out enough to allow
        two per chunk, so 2 is folded in; otherwise 1 is folded in.

        Files with fewer than two functions are skipped, as no gap exists.
        """
        starts = [start for _, start, _ in fx_matches]
        if len(starts) < 2:
            return
        diffs = [abs(b - a) for a, b in pairwise(starts)]
        avg_diff = sum(diffs) / len(diffs)
        signal = 1 if avg_diff > IDEAL_LINES_PER_FUNCTION / 2 else 2
        self._update_ema("code", key="max_functions", current_value=signal)

    def _fit_sentences_per_para(self, paragraphs: list[str]) -> None:
        """Fold the average sentences-per-paragraph into the document EMA.

        Each paragraph is cut into sentences with the fallback `UniversalSplitter`
        and the mean of the per-paragraph sentence counts is EMA-folded into
        max_sentences, clamped to the [2, 25] range.
        """
        sentence_counts = [len(self._sentence_splitter.split(p)) for p in paragraphs]
        if not sentence_counts:
            return
        avg_sent = sum(sentence_counts) / len(sentence_counts)
        self._update_ema(
            "document",
            key="max_sentences",
            current_value=min(25.0, max(2.0, avg_sent)),
        )

    def _fit_section_breaks(self, lines: list[str], paragraphs: list[str]) -> None:
        """Fold header density and the section-break signal into the document EMA.

        Lines carrying a section marker (markdown headings, thematic breaks, and
        HTML sectioning tags, per `SECTION_BREAK_PATTERN`) are counted and divided
        by the paragraph count. That density is EMA-folded into
        header_density_ratio, and max_section_breaks receives 2 when more than 75%
        of paragraphs carry a marker, otherwise 1.
        """
        marker_count = sum(1 for line in lines if SECTION_BREAK_PATTERN.match(line))
        density = marker_count / max(1, len(paragraphs))
        self._update_ema(
            "document",
            key="header_density_ratio",
            current_value=density,
        )
        self._update_ema(
            "document",
            key="max_section_breaks",
            current_value=2 if density > 0.75 else 1,
        )

    def _fit_max_tokens_code(self, text: str, starts: list[int]) -> None:
        """Fold the average token span between functions into the code max_tokens EMA.

        Each of the first five function declarations is treated as a span end; the
        text between consecutive starts is token-counted with `count_tokens` and
        the mean of those spans is EMA-folded into code max_tokens.

        Files with fewer than two functions are skipped, as no span exists.
        """
        if len(starts) < 2:
            return
        spans = [text[a:b] for a, b in pairwise(starts[:5])]
        self._update_ema(
            "code",
            key="max_tokens",
            current_value=(
                min(
                    self.hard_token_limit,
                    sum(count_tokens(s, self.token_counter) for s in spans)
                    / len(spans),
                )
            ),
        )

    def _fit_max_tokens_document(self, paragraphs: list[str]) -> None:
        """Fold the average paragraph token count into the document max_tokens EMA.

        The first five paragraphs are token-counted with `count_tokens` and their
        mean is EMA-folded into document max_tokens.
        """
        paragraphs = paragraphs[:5]
        if not paragraphs:
            return
        self._update_ema(
            "document",
            key="max_tokens",
            current_value=(
                min(
                    self.hard_token_limit,
                    sum(count_tokens(p, self.token_counter) for p in paragraphs)
                    / len(paragraphs),
                )
            ),
        )

    def _fit(self, text: str, profile_type: Literal["code", "document"]) -> None:
        """Measure structural metrics from text and fold them into the EMA state."""
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
    def add_file(self, file_path: str | Path) -> None:
        """Enqueue a single local system file if exists

        Note:
            Only the path is queued here so `add_file`/`add_files` stay cheap.

        Args:
            file_path: Path to the file to process.

        Raises:
            FileNotFoundError: If the given path doesn't exist.
        """
        path_obj = Path(file_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Source file path not found: {file_path}")
        self._pending_sources.append(file_path)

    @validate_input
    def add_files(self, file_paths: IterableOfPath) -> None:
        """Enqueue a batch list of local system files.

        Args:
            file_paths: A non-string iterable of paths to the document files.

        Raises:
            FileNotFoundError: If any given path doesn't exist.
        """
        for path in file_paths:
            self.add_file(path)

    @validate_input
    def process(
        self,
        *,
        separator: Any = None,
        on_errors: Literal["raise", "skip", "break"] = "raise",
    ) -> Generator[DotDict, None, None]:
        """Process the queue, extracting and chunking each source on the spot.

        Every returned chunk is enriched with inferred_type metadata

         Args:
            separator: A value to be yielded after the chunks of each text are processed.
                Note: None cannot be used as a separator.

            n_jobs: Number of parallel workers to use. If None, uses all available CPUs.
                   Must be >= 1 if specified.
            show_progress: Flag to show or disable the loading bar.
            on_errors: How to handle errors during processing. Can be 'raise', 'ignore', or 'break'.

        yields:
            `DotDict` object, representing a chunk with its content and metadata.
        """

        def fit_and_stream_text(text_or_gen):
            if isinstance(text_or_gen, str):
                text_or_gen = [text_or_gen]

            for text in text_or_gen:
                self._fit(text, "document")
                yield text

        while self._pending_sources:
            origin = self._pending_sources.popleft()

            path_obj = Path(origin)
            file_type = self._detect_file_type(path_obj)
            learned_state = self.learned_state[file_type]

            if file_type == "code":
                content = read_text_file(path_obj)
                self._fit(content, file_type)

                self.code_chunker.token_counter = self.token_counter
                self.code_chunker.max_tokens = (
                    learned_state["max_tokens"] if self.token_counter else None
                )
                self.code_chunker.max_lines = learned_state["max_lines"]
                self.code_chunker.max_functions = round(learned_state["max_functions"])

                chunks = self.code_chunker.chunk_text(
                    content, token_counter=self.token_counter, strict=False
                )
            else:
                text_or_gen, metadata = self.document_chunker.extract_text_and_metadata(
                    path_obj, path_obj.suffix
                )

                self.document_chunker.max_tokens = (
                    learned_state["max_tokens"] if self.token_counter else None
                )
                self.document_chunker.max_sentences = int(
                    learned_state["max_sentences"]
                )
                self.document_chunker.max_section_breaks = round(
                    learned_state["max_section_breaks"]
                )

                gen = fit_and_stream_text(text_or_gen)
                chunks = self.document_chunker.chunk_texts(
                    gen, token_counter=self.token_counter, n_jobs=4, on_errors=on_errors
                )

            for i, chunk in enumerate(chunks):
                if i != 0 and separator is not None:
                    yield separator
                chunk["metadata"]["inferred_type"] = file_type
                yield chunk
