"""
Author: Speedyk-005 | Copyright (c) 2025 | License: MIT

Language-Agnostic Code Chunking Utility

This module provides a robust, convention-aware engine for segmenting source code into
semantic units ("chunks") such as functions, classes, namespaces, and logical blocks.
Unlike purely heuristic or grammar-dependent parsers, the `CodeChunker` relies on
anchored, multi-language regex patterns and indentation rules to identify structures
consistently across a variety of programming languages.

Limitations
-----------
`CodeChunker` assumes syntactically conventional code. Highly obfuscated, minified,
or macro-generated sources may not fully respect its boundary patterns, though such
cases fall outside its intended domain.

Inspired by:
    - Camel.utils.chunker.CodeChunker (@ CAMEL-AI.org)
    - code-chunker by JimAiMoment
    - whats_that_code by matthewdeanmartin
    - CintraAI Code Chunker
"""

import sys
from pathlib import Path
from typing import Any, Literal, Callable, Generator, Annotated
from functools import partial
from itertools import chain

from more_itertools import unique_everseen
from pydantic import Field
from box import Box

try:
    from charset_normalizer import from_path
    from littletree import Node
    import defusedxml.ElementTree as ET
except ImportError:
    from_path, Node, ET = None, None, None

from loguru import logger

from chunklet.base_chunker import BaseChunker
from chunklet.code_chunker._code_structure_extractor import CodeStructureExtractor
from chunklet.common.path_utils import is_path_like
from chunklet.common.batch_runner import run_in_batch
from chunklet.common.validation import validate_input, restricted_iterable
from chunklet.common.token_utils import count_tokens
from chunklet.exceptions import (
    InvalidInputError,
    MissingTokenCounterError,
    TokenLimitError,
)


class CodeChunker(BaseChunker):
    """
    Language-agnostic code chunking utility for semantic code segmentation.

    Extracts structural units (functions, classes, namespaces) from source code
    across multiple programming languages using pattern-based detection and
    token-aware segmentation.

    Key Features:
        - Cross-language support (Python, C/C++, Java, C#, JavaScript, Go, etc.)
        - Structural analysis with namespace hierarchy tracking
        - Configurable token limits with strict/lenient overflow handling
        - Flexible docstring and comment processing modes
        - Accurate line number preservation and source tracking
        - Parallel batch processing for multiple files
        - Comprehensive logging and progress tracking
    """

    @validate_input
    def __init__(
        self,
        verbose: bool = False,
        token_counter: Callable[[str], int] | None = None,
    ):
        """
        Initialize the CodeChunker with optional token counter and verbosity control.

        Args:
            verbose (bool): Enable verbose logging.
            token_counter (Callable[[str], int] | None): Function that counts tokens in text.
                If None, must be provided when calling chunk() methods.
        """
        self.token_counter = token_counter
        self._verbose = verbose
        self.extractor = CodeStructureExtractor(verbose=self._verbose)

    @property
    def verbose(self) -> bool:
        """Get the verbose setting."""
        return self._verbose

    @verbose.setter
    def verbose(self, value: bool) -> None:
        """Set the verbose setting and propagate to the extractor."""
        self._verbose = value
        self.extractor.verbose = value

    def _merge_tree(self, relations_list: list[list]) -> str:
        """
        Merges multiple sets of parent-child relation dictionaries into a single tree
        then returns its string representation.

        Args:
            relations_list (list[list]): A list containing relation lists.

        Returns:
            str: The string representation of the tree
        """
        if not relations_list:
            return "global"

        # Flatten the set of lists into a single iterable
        all_relations_flat = chain.from_iterable(relations_list)

        # Deduplicate relations
        def relation_key(relation: dict):
            return tuple(sorted(relation.items()))

        unique_relations = list(unique_everseen(all_relations_flat, key=relation_key))

        if not unique_relations:
            return "global"

        merged_tree = Node.from_relations(unique_relations, root="global")

        return merged_tree.to_string()

    def _split_oversized(
        self,
        snippet_dict: dict,
        max_tokens: int,
        max_lines: int,
        source: str | Path,
        token_counter: Callable | None,
        cumulative_lengths: tuple[int, ...],
    ):
        """
        Split an oversized structural block into smaller sub-chunks.

        This helper is used when a single code block exceeds the maximum
        token limit and `strict_mode` is disabled. It divides the block's
        content into token-bounded fragments while preserving line order
        and basic metadata.

        Args:
            snippet_dict (dict): The oversized snippet to split.
            max_tokens (int): Maximum tokens per sub-chunk.
            max_lines (int): Maximum lines per sub-chunk.
            source (str | Path): The source of the code.
            token_counter (Callable | None): The token counting function.
            cumulative_lengths (tuple[int, ...]): The cumulative lengths of the lines in the source code.

        Returns:
            list[Box]: A list of sub-chunks derived from the original block.
        """
        sub_boxes = []
        curr_chunk = []
        token_count = 0
        line_count = 0

        # Iterate through each line in the snippet_dict content
        for line_no, line in enumerate(
            snippet_dict["content"].splitlines(), start=snippet_dict["start_line"]
        ):
            line_tokens = (
                count_tokens(line, token_counter) if max_tokens != sys.maxsize else 0
            )

            # If adding this line would exceed either max_tokens or max_lines, commit current chunk
            if (token_count + line_tokens > max_tokens) or (line_count + 1 > max_lines):
                start_line = line_no - len(curr_chunk)
                end_line = line_no - 1
                start_span = cumulative_lengths[start_line - 1]
                end_span = cumulative_lengths[end_line]
                tree = Node.from_relations(snippet_dict["relations"]).to_string()
                sub_boxes.append(
                    Box(
                        {
                            "content": "\n".join(curr_chunk),
                            "metadata": {
                                "tree": tree,
                                "start_line": start_line,
                                "end_line": end_line,
                                "span": (start_span, end_span),
                                "source": (
                                    str(source)
                                    if isinstance(source, Path)
                                    or (
                                        isinstance(source, str) and is_path_like(source)
                                    )
                                    else "N/A"
                                ),
                            },
                        }
                    )
                )
                curr_chunk = [line]  # Add the overflow line!
                token_count = 0
                line_count = 0

            curr_chunk.append(line)
            token_count += line_tokens
            line_count += 1

        # Add any remaining chunk at the end
        if curr_chunk:
            start_line = snippet_dict["end_line"] - len(curr_chunk) + 1
            end_line = snippet_dict["end_line"]
            start_span = cumulative_lengths[start_line - 1]
            end_span = cumulative_lengths[end_line]
            tree = Node.from_relations(snippet_dict["relations"]).to_string()
            sub_boxes.append(
                Box(
                    {
                        "content": "\n".join(curr_chunk),
                        "metadata": {
                            "tree": tree,
                            "start_line": start_line,
                            "end_line": end_line,
                            "span": (start_span, end_span),
                            "source": (
                                str(source)
                                if (isinstance(source, Path) or is_path_like(source))
                                else "N/A"
                            ),
                        },
                    }
                )
            )

        return sub_boxes

    def _format_limit_msg(
        self,
        box_tokens: int,
        max_tokens: int,
        box_lines: int,
        max_lines: int,
        function_count: int,
        max_functions: int,
        content_preview: str,
    ) -> str:
        """
        Format a limit exceeded error message, only including limits that are not sys.maxsize.

        Args:
            box_tokens: Actual token count in the block
            max_tokens: Maximum allowed tokens
            box_lines: Actual line count in the block
            max_lines: Maximum allowed lines
            function_count: Actual function count in the block
            max_functions: Maximum allowed functions
            content_preview: Preview of the content that exceeded limits

        Returns:
            Formatted error message with applicable limits
        """
        limits = []

        if max_tokens != sys.maxsize:
            limits.append(f"tokens: {box_tokens} > {max_tokens}")
        if max_lines != sys.maxsize:
            limits.append(f"lines: {box_lines} > {max_lines}")
        if max_functions != sys.maxsize:
            limits.append(f"functions: {function_count} > {max_functions}")
        
        return (
            f"Limits: {', '.join(limits)}\n"
            f"Content starting with: \n```\n{content_preview}...\n```" 
        )
        
    def _group_by_chunk(
        self,
        snippet_dicts: list[dict],
        cumulative_lengths: tuple[int, ...],
        token_counter: Callable[[str], int] | None,
        max_tokens: int,
        max_lines: int,
        max_functions: int,
        strict: bool,
        source: str | Path,
    ) -> list[Box]:
        """
        Group code snippets into chunks based on specified constraints.

        Iteratively merges snippets into chunks while respecting token, line, and function limits.
        Handles oversized snippets by splitting them if strict mode is disabled.

        Args:
            snippet_dicts (list[dict]): List of extracted code snippet dictionaries.
            cumulative_lengths (tuple[int, ...]): Cumulative character lengths for span calculation.
            token_counter (Callable[[str], int] | None): Function to count tokens in text.
            max_tokens (int): Maximum tokens per chunk.
            max_lines (int): Maximum lines per chunk.
            max_functions (int): Maximum functions per chunk.
            strict (bool): If True, raise error on oversized snippets; if False, split them.
            source (str | Path): Original source for metadata.

        Returns:
            list[Box]: List of chunk boxes with content and metadata.
        """
        source = (
            str(source) if (isinstance(source, Path) or is_path_like(source)) else "N/A"
        )

        merged_content = []
        relations_list = []
        start_line = None
        end_line = None
        token_count = 0
        line_count = 0
        function_count = 0
        result_chunks = []

        index = 0
        while index < len(snippet_dicts):
            snippet_dict = snippet_dicts[index]
            box_tokens = (
                count_tokens(snippet_dict["content"], token_counter)
                if max_tokens != sys.maxsize
                else 0
            )
            box_lines = snippet_dict["content"].count("\n") + bool(
                snippet_dict["content"]
            )
            is_function = bool(snippet_dict.get("func_partial_signature"))

            # Check if adding this snippet exceeds any limits
            token_limit_reached = token_count + box_tokens > max_tokens
            line_limit_reached = line_count + box_lines > max_lines
            function_limit_reached = is_function and (
                function_count + 1 > max_functions
            )

            if not (
                token_limit_reached or line_limit_reached or function_limit_reached
            ):
                # Fits: merge normally
                merged_content.append(snippet_dict["content"])
                relations_list.append(snippet_dict["relations"])
                token_count += box_tokens
                line_count += box_lines
                if is_function:
                    function_count += 1

                if start_line is None:
                    start_line = snippet_dict["start_line"]
                end_line = snippet_dict["end_line"]
                index += 1

            elif not merged_content:
                # Too big and nothing merged yet: handle oversize
                limit_msg = self._format_limit_msg(
                    box_tokens,
                    max_tokens,
                    box_lines,
                    max_lines,
                    function_count,
                    max_functions,
                    snippet_dict["content"][:100],
                )
                if strict:
                    raise TokenLimitError(
                        f"Structural block exceeds maximum limit.\n{limit_msg}\n"
                        "Reason: Prevent splitting inside interest points (function, class, region, ...)\n"
                        "💡Hint: Consider increasing 'max_tokens', 'max_lines', or 'max_functions', "
                        "refactoring the oversized block, or setting 'strict=False' to allow automatic splitting of oversized blocks."
                    )
                else:  # Else split further
                    logger.warning(
                        "Splitting oversized block into sub-chunks.\n(%s)",
                        limit_msg,
                    )

                    sub_chunks = self._split_oversized(
                        snippet_dict,
                        max_tokens,
                        max_lines,
                        source,
                        token_counter,
                        cumulative_lengths,
                    )

                    for sub_chunk in sub_chunks:
                        sub_chunk.metadata.chunk_num = len(result_chunks) + 1
                        result_chunks.append(sub_chunk)
                    index += 1
            else:
                # Flush current merged content as a chunk
                start_span = cumulative_lengths[start_line - 1]
                end_span = cumulative_lengths[end_line]
                merged_chunk = Box(
                    {
                        "content": "\n".join(merged_content),
                        "metadata": {
                            "chunk_num": len(result_chunks) + 1,
                            "tree": self._merge_tree(relations_list),
                            "start_line": start_line,
                            "end_line": end_line,
                            "span": (start_span, end_span),
                            "source": source,
                        },
                    }
                )
                result_chunks.append(merged_chunk)

                # Reset for next chunk
                merged_content.clear()
                relations_list.clear()
                start_line = None
                end_line = None
                token_count = 0
                line_count = 0
                function_count = 0

        # Flush remaining content
        if merged_content:
            start_span = cumulative_lengths[start_line - 1]
            end_span = cumulative_lengths[end_line]
            merged_chunk = Box(
                {
                    "content": "\n".join(merged_content),
                    "metadata": {
                        "chunk_num": len(result_chunks) + 1,
                        "tree": self._merge_tree(relations_list),
                        "start_line": start_line,
                        "end_line": end_line,
                        "span": (start_span, end_span),
                        "source": source,
                    },
                }
            )
            result_chunks.append(merged_chunk)

        return result_chunks

    def _validate_constraints(
        self,
        max_tokens: int | None,
        max_lines: int | None,
        max_functions: int | None,
        token_counter: Callable[[str], int] | None,
    ):
        """
        Validates that at least one chunking constraint is provided and sets default values.

        Args:
            max_tokens (int | None): Maximum number of tokens per chunk.
            max_lines (int | None): Maximum number of lines per chunk.
            max_functions (int | None): Maximum number of functions per chunk.
            token_counter (Callable[[str], int] | None): Function that counts tokens in text.

        Raises:
            InvalidInputError: If no chunking constraints are provided.
            MissingTokenCounterError: If `max_tokens` is provided but no `token_counter` is provided.
        """
        if not any((max_tokens, max_lines, max_functions)):
            raise InvalidInputError(
                "At least one of 'max_tokens', 'max_lines', or 'max_functions' must be provided."
            )

        # If token_counter is required but not provided
        if max_tokens is not None and not (token_counter or self.token_counter):
            raise MissingTokenCounterError()

    @validate_input
    def chunk(
        self,
        source: str | Path,
        *,
        max_tokens: Annotated[int | None, Field(ge=12)] = None,
        max_lines: Annotated[int | None, Field(ge=5)] = None,
        max_functions: Annotated[int | None, Field(ge=1)] = None,
        token_counter: Callable[[str], int] | None = None,
        include_comments: bool = True,
        docstring_mode: Literal["summary", "all", "excluded"] = "all",
        strict: bool = True,
    ) -> list[Box]:
        """
        Extract semantic code chunks from source using multi-dimensional analysis.

        Processes source code by identifying structural boundaries (functions, classes,
        namespaces) and grouping content based on multiple constraints including
        tokens, lines, and logical units while preserving semantic coherence.

        Args:
            source (str | Path): Raw code string or file path to process.
            max_tokens (int, optional): Maximum tokens per chunk. Must be >= 12.
            max_lines (int, optional): Maximum number of lines per chunk. Must be >= 5.
            max_functions (int, optional): Maximum number of functions per chunk. Must be >= 1.
            token_counter (Callable, optional): Token counting function. Uses instance
                counter if None. Required for token-based chunking.
            include_comments (bool): Include comments in output chunks. Default: True.
            docstring_mode(Literal["summary", "all", "excluded"]): Docstring processing strategy:
                - "summary": Include only first line of docstrings
                - "all": Include complete docstrings
                - "excluded": Remove all docstrings
                Defaults to "all"
            strict (bool): If True, raise error when structural blocks exceed
                max_tokens. If False, split oversized blocks. Default: True.

        Returns:
            list[Box]: List of code chunks with metadata. Each Box contains:
                - content (str): Code content
                - tree (str): Namespace hierarchy
                - start_line (int): Starting line in original source
                - end_line (int): Ending line in original source
                - span (tuple[int, int]): Character-level span (start and end offsets) in the original source.
                - source_path (str): Source file path or "N/A"

        Raises:
            InvalidInputError: Invalid configuration parameters.
            MissingTokenCounterError: No token counter available.
            FileProcessingError: Source file cannot be read.
            TokenLimitError: Structural block exceeds max_tokens in strict mode.
            CallbackError: If the token counter fails or returns an invalid type.
        """
        self._validate_constraints(max_tokens, max_lines, max_functions, token_counter)

        # Adjust limits for internal use
        if max_tokens is None:
            max_tokens = sys.maxsize
        if max_lines is None:
            max_lines = sys.maxsize
        if max_functions is None:
            max_functions = sys.maxsize

        token_counter = token_counter or self.token_counter

        if isinstance(source, str) and not source.strip():
            self.log_info("Input source is empty. Returning empty list.")
            return []

        self.log_info(
            "Starting chunk processing for {}",
            (
                f"source: {source}"
                if isinstance(source, Path)
                or (isinstance(source, str) and is_path_like(source))
                else f"code starting with:\n```\n{source[:100]}...\n```\n"
            ),
        )

        snippet_dicts, cumulative_lengths = self.extractor.extract_code_structure(
            source, include_comments, docstring_mode
        )

        result_chunks = self._group_by_chunk(
            snippet_dicts=snippet_dicts,
            cumulative_lengths=cumulative_lengths,
            token_counter=token_counter,
            max_tokens=max_tokens,
            max_lines=max_lines,
            max_functions=max_functions,
            strict=strict,
            source=source,
        )

        self.log_info(
            "Generated {} chunk(s) for the {}",
            len(result_chunks),
            (
                f"source: {source}"
                if isinstance(source, Path)
                or (isinstance(source, str) and is_path_like(source))
                else f"code starting with:\n```\n{source[:100]}...\n```\n"
            ),
        )

        return result_chunks

    @validate_input
    def batch_chunk(
        self,
        sources: restricted_iterable(str | Path),
        *,
        max_tokens: Annotated[int | None, Field(ge=12)] = None,
        max_lines: Annotated[int | None, Field(ge=5)] = None,
        max_functions: Annotated[int | None, Field(ge=1)] = None,
        token_counter: Callable[[str], int] | None = None,
        separator: Any = None,
        include_comments: bool = True,
        docstring_mode: Literal["summary", "all", "excluded"] = "all",
        strict: bool = True,
        n_jobs: Annotated[int, Field(ge=1)] | None = None,
        show_progress: bool = True,
        on_errors: Literal["raise", "skip", "break"] = "raise",
    ) -> Generator[Box, None, None]:
        """
        Process multiple source files or code strings in parallel.

        Leverages multiprocessing to efficiently chunk multiple code sources,
        applying consistent chunking rules across all inputs.

        Args:
            sources (restricted_iterable[str | Path]): A restricted iterable of file paths or raw code strings to process.
            max_tokens (int, optional): Maximum tokens per chunk. Must be >= 12.
            max_lines (int, optional): Maximum number of lines per chunk. Must be >= 5.
            max_functions (int, optional): Maximum number of functions per chunk. Must be >= 1.
            token_counter (Callable | None): Token counting function. Uses instance
                counter if None. Required for token-based chunking.
            separator (Any): A value to be yielded after the chunks of each text are processed.
                Note: None cannot be used as a separator.
            include_comments (bool): Include comments in output chunks. Default: True.
            docstring_mode(Literal["summary", "all", "excluded"]): Docstring processing strategy:
                - "summary": Include only first line of docstrings
                - "all": Include complete docstrings
                - "excluded": Remove all docstrings
                Defaults to "all"
            strict (bool): If True, raise error when structural blocks exceed
                max_tokens. If False, split oversized blocks. Default: True.
            n_jobs (int | None): Number of parallel workers. Uses all available CPUs if None.
            show_progress (bool): Display progress bar during processing. Defaults to True.
            on_errors (Literal["raise", "skip", "break"]):
                How to handle errors during processing. Defaults to 'raise'.

        yields:
            Box: `Box` object, representing a chunk with its content and metadata.
                Includes:
                - content (str): Code content
                - tree (str): Namespace hierarchy
                - start_line (int): Starting line in original source
                - end_line (int): Ending line in original source
                - span (tuple[int, int]): Character-level span (start and end offsets) in the original source.
                - source_path (str): Source file path or "N/A"

        Raises:
            InvalidInputError: Invalid input parameters.
            MissingTokenCounterError: No token counter available.
            FileProcessingError: Source file cannot be read.
            TokenLimitError: Structural block exceeds max_tokens in strict mode.
            CallbackError: If the token counter fails or returns an invalid type.
        """
        chunk_func = partial(
            self.chunk,
            max_tokens=max_tokens,
            max_lines=max_lines,
            max_functions=max_functions,
            token_counter=token_counter or self.token_counter,
            include_comments=include_comments,
            docstring_mode=docstring_mode,
            strict=strict,
        )

        yield from run_in_batch(
            func=chunk_func,
            iterable_of_args=sources,
            iterable_name="sources",
            separator=separator,
            n_jobs=n_jobs,
            show_progress=show_progress,
            on_errors=on_errors,
            verbose=self.verbose,
        )
