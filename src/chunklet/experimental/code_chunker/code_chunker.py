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

Summary
-------
`CodeChunker` is not a naive regex heuristic — it's a **pattern-driven, convention-aware,
language-agnostic structural chunker** engineered for practical accuracy in real-world
projects. It trades full grammatical precision for flexibility, speed, and cross-language
adaptability.

Inspired by:
    - Camel.utils.chunker.CodeChunker (@ CAMEL-AI.org)
    - whats_that_code by matthewdeanmartin
    - code-chunker by JimAiMoment
    - ctags and similar structural code parsers

"""

import regex as re
from pathlib import Path
from typing import Any, Literal, Callable, Generator, Annotated
from functools import partial
from pydantic import Field
import defusedxml.ElementTree as ET
from collections import defaultdict, namedtuple
from box import Box
from anytree import Node, RenderTree
from loguru import logger

from chunklet.experimental.code_chunker.patterns import (
    SINGLE_LINE_COMMENT,
    MULTI_LINE_COMMENT,
    DOCSTRING_STYLE_ONE,
    DOCSTRING_STYLE_TWO,
    FUNCTION_DECLARATION,
    NAMESPACE_DECLARATION,
    METADATA,
    OPENER,
    CLOSURE,
)
from chunklet.experimental.code_chunker.helpers import is_binary_file, is_python_code
from chunklet.utils.path_utils import is_path_like   
from chunklet.utils.batch_runner import run_in_batch
from chunklet.utils.validation import validate_input, restricted_iterable
from chunklet.utils.token_utils import count_tokens
from chunklet.exceptions import (
    FileProcessingError,
    MissingTokenCounterError,
    TokenLimitError,
)


CodeLine = namedtuple(
    "CodeLine", ["line_number", "content", "indent_level", "func_partial_signature"]
)


class CodeChunker:
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
        self.verbose = verbose

    def _replace_with_newlines(self, match: re.Match) -> str:
        """Replaces the matched content with an equivalent number of newlines."""
        return "\n" * len(match.group(0).splitlines())

    def _read_source(self, source: str | Path) -> str:
        """Retrieve source code from file or treat input as raw string.

        Args:
            source (str | Path): File path or raw code string.

        Returns:
            str: Source code content.

        Raises:
            FileProcessingError: When file cannot be read or doesn't exist.
        """
        if isinstance(source, (str, Path)) and is_path_like(source):
            path = Path(source)
            if not path.exists():
                raise FileProcessingError(f"File does not exist: {path}")
            if is_binary_file(path):
                raise FileProcessingError(f"Binary file not supported: {path}")
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                    if self.verbose:
                        logger.info(
                            "Successfully read %d characters from {}",
                            len(content),
                            path,
                        )
                    return content
            except Exception as e:
                raise FileProcessingError(f"Failed to read file: {path}") from e
        return source

    def _annotate_block(self, tag: str, match: re.Match) -> str:
        """Prefix each line in a matched block with a tag for tracking.

        Args:
            tag (str): Tag identifier for the block type.
            match (re.Match): Regex match object for the block.

        Returns:
            str: Annotated block with tag prefixes.
        """
        lines = match.group(0).splitlines()
        return "\n".join(f"(-- {tag} -->) {line}" for line in lines)

    def _summarize_docstring_style_one(self, match: re.Match) -> str:
        """
        Extracts the first line from a block-style documentation string.

        Args:
            match (re.Match): Regex match object for the docstring with captured groups.

        Returns:
            str: The summarized docstring line.
        """
        newline_count = len(match.group(0).splitlines()) + 1

        # Because of the way we make the pattern, there will be multiple of None blocks
        # for the unmatched parts.
        # That is the only possible hack for now.
        groups = [g for g in match.groups() if g is not None]
        indent = groups[0]
        l_end = groups[1]
        doc = groups[2].strip()
        r_end = groups[3]

        first_line = doc.splitlines()[0] if doc else ""
        summarized_line_content = f"{indent}{l_end}{first_line}{r_end}\n"
        padding_count = newline_count - len(summarized_line_content.splitlines()) + 1
        return summarized_line_content + "\n" * padding_count

    def _summarize_docstring_style_two(self, match: re.Match) -> str:
        """
        Extracts a summary from line-prefixed documentation comments.

        Attempts to parse <summary> XML tags; falls back to the first meaningful ine if parsing fails.

        Args:
            match (re.Match): Regex match object for line-based docstring.

        Returns:
            str: The summarized docstring line(s).
        """
        indent = match.group(1)
        raw_doc = match.group(0)
        newline_count = len(raw_doc) + 1
        prefix = re.match(r"\s*(//[/!])\s*", raw_doc).group(1)

        # Remove leading '///' or '//!' and optional spaces at start of each line
        clean_doc = re.sub(rf"(?m)^\s*{prefix}\s*", "", raw_doc)
        try:
            # Try parsing it as XML
            wrapped = f"<root>{clean_doc}</root>"
            root = ET.fromstring(wrapped)
            summary_elem = root.find("summary")
            if summary_elem is not None:
                summary = ET.tostring(summary_elem, encoding="unicode")
            else:
                raise ET.ParseError
        except ET.ParseError:
            # Fallback: first meaningful line in plain text
            summary = ""
            for line in clean_doc.splitlines():
                # Skip lines that contain *only tags* (with optional whitespace)
                if line and not re.fullmatch(r"<.*>\s*", line.strip()):
                    summary = line
                    break

        # Construct the summarized docstring line
        summarized_line_content = "".join(
            f"{indent}{prefix} {line}" for line in summary.splitlines()
        )
        padding_count = newline_count - len(summarized_line_content.splitlines()) + 1
        return summarized_line_content + "\n" * padding_count

    def _preprocess(
        self, code: str, include_comments: bool, docstring_mode: str = "all"
    ) -> str:
        """
        Preprocess the code before extraction.

        Processing steps:
          - Optionally remove comments
          - Replace docstrings according to mode
          - Annotate comments, docstrings, and annotations for later detection

        Args:
            code (str): Source code to preprocess.
            include_comments (bool): Whether to include comments in output.
            docstring_mode (str): How to handle docstrings.

        Returns:
            str: Preprocessed code with annotations.
        """
        code = code.strip()

        # Remove comments if not required
        if not include_comments:
            code = SINGLE_LINE_COMMENT.sub(
                lambda m: self._replace_with_newlines(m), code
            )
            code = MULTI_LINE_COMMENT.sub(
                lambda m: self._replace_with_newlines(m), code
            )

        # Process docstrings according to mode
        if docstring_mode == "all":
            pass
        elif docstring_mode == "summary":
            code = DOCSTRING_STYLE_ONE.sub(
                lambda m: self._summarize_docstring_style_one(m), code
            )
            code = DOCSTRING_STYLE_TWO.sub(
                lambda m: self._summarize_docstring_style_two(m), code
            )
        else:  # "excluded"
            code = DOCSTRING_STYLE_ONE.sub(
                lambda m: self._replace_with_newlines(m), code
            )
            code = DOCSTRING_STYLE_TWO.sub(
                lambda m: self._replace_with_newlines(m), code
            )

        # List of all regex patterns with the tag to annotate them
        patterns_n_tags = [
            (SINGLE_LINE_COMMENT, "COMM"),
            (MULTI_LINE_COMMENT, "COMM"),
            (DOCSTRING_STYLE_ONE, "DOC"),
            (DOCSTRING_STYLE_TWO, "DOC"),
            (METADATA, "META"),
        ]

        # Apply _annotate_block to all matches for each pattern
        for pattern, tag in patterns_n_tags:
            code = pattern.sub(lambda match: self._annotate_block(tag, match), code)

        return code

    def _post_processing(self, snippet_dicts: list[dict]):
        """
        Attach a namespace tree structure to each snippet incrementally.

        Args:
            snippet_dicts (list[dict]): List of extracted code snippets.

        Returns:
            list[dict]: Snippets with attached namespace trees.
        """

        def render_tree(root):
            tree = []
            for pre, fill, node in RenderTree(root):
                tree.append(f"{pre}{node.name}")
            return "\n".join(tree)

        root = Node("global")
        namespaces_stack = [(root, -1)]

        for snippet_dict in snippet_dicts:
            # Pop namespaces until we find the appropriate parent level
            while (
                namespaces_stack
                and snippet_dict["indent_level"] <= namespaces_stack[-1][1]
            ):
                removed_node, _ = namespaces_stack.pop()
                removed_node.parent = None

            # If a Namespace line has been detected (e.g, class, module, namespace, ...)
            matched = NAMESPACE_DECLARATION.search(snippet_dict["content"])
            if matched:
                # Use the current parent from stack
                current_parent, _ = namespaces_stack[-1]
                new_node = Node(matched.group(1).strip(), parent=current_parent)
                namespaces_stack.append((new_node, snippet_dict["indent_level"]))

            # Include any partial func signature
            if snippet_dict.get("func_partial_signature"):
                current_parent, _ = namespaces_stack[-1]
                new_node = Node(
                    snippet_dict["func_partial_signature"], parent=current_parent
                )
                namespaces_stack.append((new_node, snippet_dict["indent_level"]))

            # Attach the rendered tree to the current snippet_dict
            snippet_dict["tree"] = render_tree(root)

        # Normalize newlines in chunk in place
        for snippet_dict in snippet_dicts:
            snippet_dict["content"] = re.sub(r"\n{3,}", "\n\n", snippet_dict["content"])

        return snippet_dicts

    def _flush_snippet(
        self,
        curr_struct: list[CodeLine],
        snippet_dicts: list[dict],
        buffer: dict[list],
    ) -> None:
        """
        Consolidate the current structure and any buffered content into a Box and append it to snippet_boxes.

        Args:
            curr_struct (list[tuple]): Accumulated code lines and metadata,
                where each element is a tuple containing:
                (line_number, line_content, indent_level, func_partial_signature).
            snippet_boxes (list[Box]): The list to which the newly created Box will be appended.
            buffer (dict[list]): Buffer for intermediate processing (default: empty list).
        """
        if not curr_struct:
            return

        candidates = [entry for v in buffer.values() for entry in v] + curr_struct
        sorted_candidates = sorted(candidates, key=lambda x: x.line_number)

        if not sorted_candidates:
            return

        content = "\n".join(c.content for c in sorted_candidates)
        start_line = sorted_candidates[0].line_number
        end_line = sorted_candidates[-1].line_number
        indent_level = max(sorted_candidates, key=lambda x: x.indent_level).indent_level

        # Capture the first func_partial_signature
        match = next(
            (c.func_partial_signature for c in curr_struct if c.func_partial_signature),
            None,
        )

        snippet_dicts.append(
            {
                "content": content,
                "indent_level": indent_level,
                "start_line": start_line,
                "end_line": end_line,
                "func_partial_signature": match,
            }
        )
        curr_struct.clear()
        buffer.clear()

    def _extract_code_structures(
        self,
        source: str | Path,
        include_comments: bool,
        docstring_mode: str,
    ) -> list[dict]:
        """
        Preprocess and parse source into individual snippet boxes.

        This function-first extraction identifies functions as primary units
        while implicitly handling other structures within the function context.

        Args:
            source (str | Path): Raw code string or Path to source file.
            include_comments (bool): Whether to include comments in output.
            docstring_mode (Literal["summary", "all", "excluded"]): How to handle docstrings.

        Returns:
            list[Box]: List of extracted code structure boxes.
        """
        source_code = self._read_source(source).strip()
        if not source_code:
            return []

        source_code = self._preprocess(source_code, include_comments, docstring_mode)

        curr_struct = []
        buffer = defaultdict(list)
        last_indent = -1
        inside_func = False
        snippet_dicts = []

        for line_no, line in enumerate(source_code.splitlines(), start=1):
            indent_level = len(line) - len(line.lstrip())

            # Detect annotated lines
            matched = re.search(r"\(-- ([A-Z]+) -->\) ", line)
            if matched:
                # Flush DOC buffer if not consecutive
                # Prevent storing multiple docstrings in the same buffer
                if buffer["DOC"] and buffer["DOC"][-1][0] != line_no - 1:
                    self._flush_snippet(curr_struct, snippet_dicts, buffer)
                    inside_func = False

                tag = matched.group(1)
                deannoted_line = re.sub(rf"{matched.group(0)}", "", line)
                deannoted_line = (
                    line[: matched.start()] + line[matched.end() :]
                )  # slice off the annotation
                buffer[tag].append(
                    CodeLine(line_no, deannoted_line, indent_level, None)
                )
                continue

            # Top-level block detection
            namespace_start = NAMESPACE_DECLARATION.match(line)
            func_start = FUNCTION_DECLARATION.match(line)
            if namespace_start or (func_start and not inside_func):
                last_indent = indent_level

                # If it is a Python code, we can flush everything, else we won't flush the docstring yet
                # This helps including the docstring that is on top of block definition in the other languages
                if curr_struct:
                    if is_python_code(source):
                        self._flush_snippet(curr_struct, snippet_dicts, buffer)
                    else:
                        doc = buffer.pop("DOC", [])
                        self._flush_snippet(curr_struct, snippet_dicts, buffer)
                        buffer.clear()
                        buffer["doc"] = doc

            # We don't want to extract nestled blocks
            if func_start:
                inside_func = True

            # Manage block accumulation
            if curr_struct:
                last_indent = last_indent or 0
                if (
                    line.strip()
                    and indent_level <= last_indent
                    and not (OPENER.match(line) or CLOSURE.match(line))
                ):  # Block end
                    self._flush_snippet(curr_struct, snippet_dicts, buffer)
                    curr_struct = [
                        CodeLine(
                            line_no,
                            line,
                            indent_level,
                            func_start.group(0) if func_start else None,
                        )
                    ]
                    last_indent = None
                    inside_func = False
                else:
                    curr_struct.append(CodeLine(line_no, line, indent_level, None))
            else:
                curr_struct = [
                    CodeLine(
                        line_no,
                        line,
                        indent_level,
                        func_start.group(0) if func_start else None,
                    )
                ]

        # Append last snippet
        if curr_struct:
            self._flush_snippet(curr_struct, snippet_dicts, buffer)

        return self._post_processing(snippet_dicts)

    def _split_oversized(
        self,
        snippet_dict: dict,
        max_tokens: int,
        source: str | Path,
        token_counter: Callable | None,
    ):
        """
        Split an oversized structural block into smaller sub-chunks.

        This helper is used when a single code block exceeds the maximum
        token limit and `strict_mode` is disabled. It divides the block's
        content into token-bounded fragments while preserving line order
        and basic metadata.

        Returns:
            list[Box]: A list of sub-chunks derived from the original block.
        """
        sub_boxes = []
        curr_chunk = []
        token_count = 0

        # Iterate through each line in the snippet_dict content
        for line_no, line in enumerate(
            snippet_dict["content"].splitlines(), start=snippet_dict["start_line"]
        ):
            line_tokens = count_tokens(line, token_counter)

            # If adding this line would exceed max_tokens, commit current chunk
            if token_count + line_tokens > max_tokens:
                if curr_chunk:  # avoid empty chunk creation
                    sub_boxes.append(
                        Box(
                            {
                                "content": "\n".join(curr_chunk),
                                "metadata": {
                                    "tree": f"• {snippet_dict['tree']}",
                                    "start_line": line_no - len(curr_chunk),
                                    "end_line": line_no - 1,
                                    "source_path": (
                                        str(source)
                                        if isinstance(source, (str, Path))
                                        else "N/A"
                                    ),
                                },
                            }
                        )
                    )
                curr_chunk.clear()
                token_count = 0

            curr_chunk.append(line)
            token_count += line_tokens

        # Add any remaining chunk at the end
        if curr_chunk:
            sub_boxes.append(
                Box(
                    {
                        "content": "\n".join(curr_chunk),
                        "metadata": {
                            "tree": f"• {snippet_dict['tree']}",
                            "start_line": snippet_dict["end_line"]
                            - len(curr_chunk)
                            + 1,
                            "end_line": snippet_dict["end_line"],
                            "source_path": (
                                str(source)
                                if (isinstance(source, Path) or is_path_like(source))
                                else "N/A"
                            ),
                        },
                    }
                )
            )

        return sub_boxes

    @validate_input
    def chunk(
        self,
        source: str | Path,
        *,
        max_tokens: Annotated[int, Field(ge=12)] = 256,
        token_counter: Callable[[str], int] | None = None,
        include_comments: bool = False,
        docstring_mode: Literal["summary", "all", "excluded"] = "summary",
        strict: bool = True,
    ) -> list[Box]:
        """
        Extract semantic code chunks from source using structural analysis.

        Processes source code by identifying structural boundaries (functions, classes,
        namespaces) and grouping content into token-limited chunks while preserving
        logical code units.

        Args:
            source (str | Path): Raw code string or file path to process.
            max_tokens (int): Maximum tokens per chunk. Default: 512.
            token_counter (Callable | None): Token counting function. Uses instance
                counter if None. Required for token-based chunking.
            include_comments (bool): Include comments in output chunks. Default: False.
            docstring_mode: Docstring processing strategy:
                - "summary": Include only first line of docstrings
                - "all": Include complete docstrings
                - "excluded": Remove all docstrings
            strict (bool): If True, raise error when structural blocks exceed
                max_tokens. If False, split oversized blocks. Default: True.

        Returns:
            list[Box]: List of code chunks with metadata. Each Box contains:
                - content (str): Code content
                - tree (str): Namespace hierarchy
                - start_line (int): Starting line in original source
                - end_line (int): Ending line in original source
                - source_path (str): Source file path or "N/A"

        Raises:
            InvalidInputError: Invalid configuration parameters.
            MissingTokenCounterError: No token counter available.
            FileProcessingError: Source file cannot be read.
            TokenLimitError: Structural block exceeds max_tokens in strict mode.
            CallbackError: If the token counter fails or returns an invalid type.
        """
        if self.verbose:
            logger.info(
                "Starting chunk processing for {}",
                (
                    f"source: {str(Path)}"
                    if (isinstance(str, Path) or is_path_like(source))
                    else f"code starting with:\n```\n{source[:100]}...\n```\n"
                ),
            )

        token_counter = token_counter or self.token_counter

        if not token_counter:
            raise MissingTokenCounterError()

        snippet_dicts = self._extract_code_structures(
            source, include_comments, docstring_mode
        )

        if self.verbose:
            logger.info(
                "Extracted {} structural blocks from source", len(snippet_dicts)
            )

        merged_content = []
        merged_tree_set = set()
        start_line = None
        end_line = None
        token_count = 0
        result_chunks = []

        i = 0
        while i < len(snippet_dicts):
            snippet_dict = snippet_dicts[i]
            box_tokens = count_tokens(snippet_dict["content"], token_counter)

            if not token_count + box_tokens > max_tokens:
                # Fits: merge normally
                merged_content.append(snippet_dict["content"])
                merged_tree_set.add(snippet_dict["tree"])
                token_count += box_tokens

                if start_line is None:
                    start_line = snippet_dict["start_line"]
                end_line = snippet_dict["end_line"]
                i += 1

            elif not merged_content:
                # too big and nothing merged yet: handle single oversize
                if strict:
                    raise TokenLimitError(
                        f"Structural block exceeds maximum token limit: {box_tokens} > {max_tokens}.\n"
                        f"Content starting with: \n```\n{snippet_dict['content'][:100]}...\n```\n"
                        f"Reason: Prevent splitting inside interest points (function, class, region, ...)\n"
                        f"💡Hint: Increase chunk_size or refactor the block to reduce its size."
                    )
                else:  # Else split further
                    if self.verbose:
                        logger.warning(
                            "Splitting oversized block ({} tokens) into sub-chunks",
                            box_tokens,
                        )

                    # Pass the dict as a Box object to _split_oversized
                    sub_chunks = self._split_oversized(
                        snippet_dict, max_tokens, source, token_counter
                    )

                    for sub_chunk in sub_chunks:
                        sub_chunk.metadata.chunk_num = len(result_chunks) + 1
                        result_chunks.append(sub_chunk)
                    i += 1
            else:
                # too big but some merged: flush
                merged_chunk = Box(
                    {
                        "content": "\n".join(merged_content),
                        "metadata": {
                            "chunk_num": len(result_chunks) + 1,
                            "tree": f"• {max(merged_tree_set, key=len)}",
                            "start_line": start_line,
                            "end_line": end_line,
                            "source_path": (
                                str(source)
                                if (isinstance(source, Path) or is_path_like(source))
                                else "N/A"
                            ),
                        },
                    }
                )
                result_chunks.append(merged_chunk)

                merged_content.clear()
                merged_tree_set.clear()
                start_line = None
                end_line = None
                token_count = 0

        # Flush remaining content
        if merged_content:
            merged_chunk = Box(
                {
                    "content": "\n".join(merged_content),
                    "metadata": {
                        "chunk_num": len(result_chunks) + 1,
                        "tree": f"• {max(merged_tree_set, key=len)}",
                        "start_line": start_line,
                        "end_line": end_line,
                        "source_path": (
                            str(source)
                            if (isinstance(source, Path) or is_path_like(source))
                            else "N/A"
                        ),
                    },
                }
            )
            result_chunks.append(merged_chunk)

        if self.verbose:
            logger.info(
                "Generated {} chunk(s) for the {}",
                len(result_chunks),
                (
                    f"source: {str(Path)}"
                    if (isinstance(str, Path) or is_path_like(source))
                    else f"code starting with:\n```\n{source[:100]}...\n```\n"
                ),
            )

        return result_chunks

    @validate_input
    def batch_chunk(
        self,
        sources: restricted_iterable(str | Path),
        *,
        max_tokens: Annotated[int, Field(ge=12)] = 256,
        token_counter: Callable[[str], int] | None = None,
        separator: Any = None,
        include_comments: bool = False,
        docstring_mode: Literal["summary", "all", "excluded"] = "summary",
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
            max_tokens (int): Maximum tokens per chunk. Defaults to 256.
            token_counter (Callable | None): Token counting function. Uses instance
                counter if None. Required for token-based chunking.
            separator (Any): A value to be yielded after the chunks of each text are processed.
                Note: None cannot be used as a separator.
            include_comments (bool): Include comments in output chunks. Default: False.
            docstring_mode: Docstring processing strategy:
                - "summary": Include only first line of docstrings
                - "all": Include complete docstrings
                - "excluded": Remove all docstrings
            strict (bool): If True, raise error when structural blocks exceed
                max_tokens. If False, split oversized blocks. Default: True.
            n_jobs (int | None): Number of parallel workers. Uses all available CPUs if None.
            show_progress (bool): Display progress bar during processing. Defaults to True.
            on_errors (Literal["raise", "skip", "break"]):
                How to handle errors during processing. Defaults to 'raise'.

        yields:
            Box: `Box` object, representing a chunk with its content and metadata.

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
