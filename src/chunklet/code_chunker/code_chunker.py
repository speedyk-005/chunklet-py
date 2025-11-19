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
from itertools import chain, accumulate
from more_itertools import unique_everseen
import regex as re
from pydantic import Field
from collections import defaultdict, namedtuple
from box import Box

try:
    from littletree import Node
    import defusedxml.ElementTree as ET
except ImportError:
    Node = None
    Et = None

from loguru import logger

from chunklet.code_chunker.patterns import (
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
from chunklet.code_chunker.helpers import is_binary_file, is_python_code
from chunklet.common.path_utils import is_path_like
from chunklet.common.batch_runner import run_in_batch
from chunklet.common.validation import validate_input, restricted_iterable
from chunklet.common.token_utils import count_tokens
from chunklet.exceptions import (
    InvalidInputError,
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
        matched_text = match.group(0)

        # To preserve the line count when replacing a multi-line block,
        # we need to replace N lines of content with N-1 newline characters.
        # This is because N-1 newlines create N empty lines in the context of the surrounding text.
        num_newlines = max(0, len(matched_text.splitlines()) - 1)

        return "\n" * num_newlines

    def _read_source(self, source: str | Path) -> str:
        """Retrieve source code from file or treat input as raw string.

        Args:
            source (str | Path): File path or raw code string.

        Returns:
            str: Source code content.

        Raises:
            FileProcessingError: When file cannot be read or doesn't exist.
        """
        if isinstance(source, Path) or is_path_like(source):
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
        # HACK: The `DOCSTRING_STYLE_ONE` regex contains multiple alternative patterns,
        # which results in `None` values for the capturing groups that did not match.
        # This list comprehension filters out the `None` values to reliably extract
        # the matched content (indent, delimiters, and docstring text).
        groups = [g for g in match.groups() if g is not None]
        indent = groups[0]
        l_end = groups[1]
        doc = groups[2].strip()
        r_end = groups[3]

        first_line = ""
        for line in doc.splitlines():
            stripped_line = line.strip()
            if stripped_line:
                first_line = stripped_line
                break

        summarized_line_content = f"{indent}{l_end}{first_line}{r_end}".strip()
        padding_count = len(match.group(0).splitlines()) - 1
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
        if not ET:
            raise ImportError(
                "The 'defusedxml' library is not installed. "
                "Please install it with 'pip install 'defusedxml>=0.7.1'' or install the code processing extras "
                "with 'pip install 'chunklet-py[code]''"
            )

        indent = match.group(1)
        raw_doc = match.group(0)
        prefix = re.match(r"^\s*(//[/!])\s*", raw_doc).group(1)

        # Remove leading '///' or '//!' and optional spaces at start of each line
        clean_doc = re.sub(rf"(?m)^\s*{prefix}\s*", "", raw_doc)
        try:
            # Try parsing it as XML
            wrapped = f"<root>{clean_doc}</root>"
            root = ET.fromstring(wrapped)
            summary_elem = root.find("summary")
            if summary_elem is not None:
                summary = ET.tostring(summary_elem, encoding="unicode").strip("\n")
            else:
                raise ET.ParseError
        except ET.ParseError:
            # Fallback: first meaningful line in plain text
            summary = ""
            for line in clean_doc.splitlines():
                # Skip lines that contain *only tags* (with optional whitespace)
                stripped_line = line.strip()
                if stripped_line and not re.fullmatch(r"<.*>\s*", stripped_line):
                    summary = stripped_line
                    break

        # Construct the summarized docstring line
        summarized_line_content = "".join(
            f"{indent}{prefix} {line}" for line in summary.splitlines() if line.strip()
        ).lstrip()

        padding_count = (
            len(raw_doc.splitlines()) - len(summarized_line_content.splitlines()) - 1
        )

        return summarized_line_content + "\n" * padding_count

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

        merged_tree = Node().from_relations(unique_relations, root="global")

        return merged_tree.to_string()

    def _preprocess(
        self, code: str, include_comments: bool, docstring_mode: str = "all"
    ) -> tuple[str, tuple[int, ...]]:
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
            tuple[str, tuple[int, ...]]: Preprocessed code with annotations and a tuple of cumulative line lengths.
                The `cumulative_lengths` are pre-calculated on the original code because altering the code
                (e.g., via removal, summary, or annotations) would cause character counts to vary.
        """
        # Call at first before any code altering
        cumulative_lengths = tuple(
            accumulate(len(line) for line in code.splitlines(keepends=True))
        )

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

        return code, cumulative_lengths

    def _post_processing(self, snippet_dicts: list[dict]):
        """
        Attach a namespace tree structure (as a list of relations) to each snippet incrementally.

        Args:
            snippet_dicts (list[dict]): List of extracted code snippets.

        Returns:
            list[dict]: Snippets with attached namespace trees (as relations).
        """
        if not Node:
            raise ImportError(
                "The 'littletree' library is not installed. "
                "Please install it with 'pip install littletree>=0.8.4' or install the code processing extras "
                "with 'pip install 'chunklet-py[code]''"
            )

        def _add_namespace_node(name, indent_level):
            new_node = Node(identifier=name)

            current_parent_node, _ = namespaces_stack[-1]
            current_parent_node.add_child(new_node)

            namespaces_stack.append((new_node, indent_level))

        # The root node will be 'global'
        tree_root = Node(identifier="global")

        # namespaces_stack: [ (node_reference, indent_level) ]
        namespaces_stack = [(tree_root, -1)]

        for snippet_dict in snippet_dicts:
            # Remove namespaces until we find the appropriate parent level
            while (
                namespaces_stack
                and snippet_dict["indent_level"] <= namespaces_stack[-1][1]
            ):
                node_to_detach, _ = namespaces_stack.pop()
                if node_to_detach is not tree_root:
                    node_to_detach.detach()

            # Handle Namespace Declaration
            matched = NAMESPACE_DECLARATION.search(snippet_dict["content"])
            if matched:
                namespace_name = matched.group(1)
                _add_namespace_node(
                    name=namespace_name, indent_level=snippet_dict["indent_level"]
                )

            # Handle Partial Function Signature
            if snippet_dict.get("func_partial_signature"):
                _add_namespace_node(
                    name=snippet_dict["func_partial_signature"].strip(),
                    indent_level=snippet_dict["indent_level"],
                )

            # Attach the current tree structure as relations
            snippet_dict["relations"] = list(tree_root.to_relations())

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
        indent_level = sorted_candidates[0].indent_level

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
    ) -> tuple[list[dict], tuple[int, ...]]:
        """
        Preprocess and parse source into individual snippet boxes.

        This function-first extraction identifies functions as primary units
        while implicitly handling other structures within the function context.

        Args:
            source (str | Path): Raw code string or Path to source file.
            include_comments (bool): Whether to include comments in output.
            docstring_mode (Literal["summary", "all", "excluded"]): How to handle docstrings.

        Returns:
            tuple[list[dict], tuple[int, ...]]: A tuple containing the list of extracted code structure boxes and the line lengths.
        """
        source_code = self._read_source(source)
        if not source_code:
            return [], ()

        source_code, cumulative_lengths = self._preprocess(
            source_code, include_comments, docstring_mode
        )

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

        return self._post_processing(snippet_dicts), cumulative_lengths

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
                if curr_chunk:  # avoid empty chunk creation
                    start_line = line_no - len(curr_chunk)
                    end_line = line_no - 1
                    start_span = (
                        0 if start_line == 1 else cumulative_lengths[start_line - 2]
                    )
                    end_span = cumulative_lengths[end_line - 1]
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
                                        if isinstance(source, (str, Path))
                                        else "N/A"
                                    ),
                                },
                            }
                        )
                    )
                curr_chunk.clear()
                token_count = 0
                line_count = 0

            curr_chunk.append(line)
            token_count += line_tokens
            line_count += 1

        # Add any remaining chunk at the end
        if curr_chunk:
            start_line = snippet_dict["end_line"] - len(curr_chunk) + 1
            end_line = snippet_dict["end_line"]
            start_span = 0 if start_line == 1 else cumulative_lengths[start_line - 2]
            end_span = cumulative_lengths[end_line - 1]
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

    def _validate_constraints(
        self,
        max_tokens: int | None,
        max_lines: int | None,
        max_functions: int | None,
        token_counter: Callable[[str], int] | None,
    ) -> tuple[int, int, int]:
        """
        Validates that at least one chunking constraint is provided and sets default values.

        Args:
            max_tokens (int | None): Maximum number of tokens per chunk.
            max_lines (int | None): Maximum number of lines per chunk.
            max_functions (int | None): Maximum number of functions per chunk.
            token_counter (Callable[[str], int] | None): Function that counts tokens in text.

        Returns:
            tuple[int, int, int]: Adjusted max_tokens, max_lines, and max_functions values.

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

        # Adjust limits for internal use
        if max_tokens is None:
            max_tokens = sys.maxsize
        if max_lines is None:
            max_lines = sys.maxsize
        if max_functions is None:
            max_functions = sys.maxsize

        return max_tokens, max_lines, max_functions

    @validate_input
    def chunk(
        self,
        source: str | Path,
        *,
        max_tokens: Annotated[int | None, Field(ge=12)] = None,
        max_lines: Annotated[int | None, Field(ge=5)] = None,
        max_functions: Annotated[int | None, Field(ge=1)] = None,
        token_counter: Callable[[str], int] | None = None,
        include_comments: bool = False,
        docstring_mode: Literal["summary", "all", "excluded"] = "all",
        strict: bool = True,
    ) -> list[Box]:
        """
        Extract semantic code chunks from source using structural analysis.

        Processes source code by identifying structural boundaries (functions, classes,
        namespaces) and grouping content into token-limited chunks while preserving
        logical code units.

        Args:
            source (str | Path): Raw code string or file path to process.
            max_tokens (int, optional): Maximum tokens per chunk. Must be >= 12.
            max_lines (int, optional): Maximum number of lines per chunk. Must be >= 5.
            max_functions (int, optional): Maximum number of functions per chunk. Must be >= 1.
            token_counter (Callable, optional): Token counting function. Uses instance
                counter if None. Required for token-based chunking.
            include_comments (bool): Include comments in output chunks. Default: False.
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
        max_tokens, max_lines, max_functions = self._validate_constraints(
            max_tokens, max_lines, max_functions, token_counter
        )
        token_counter = token_counter or self.token_counter

        if self.verbose:
            logger.info(
                "Starting chunk processing for {}",
                (
                    f"source: {str(Path)}"
                    if (isinstance(str, Path) or is_path_like(source))
                    else f"code starting with:\n```\n{source[:100]}...\n```\n"
                ),
            )

        if not source.strip():
            if self.verbose:
                logger.info("Input source is empty. Returning empty list.")
            return []

        snippet_dicts, cumulative_lengths = self._extract_code_structures(
            source, include_comments, docstring_mode
        )

        if self.verbose:
            logger.info(
                "Extracted {} structural blocks from source", len(snippet_dicts)
            )

        # Grouping logic

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
            box_lines = snippet_dict["content"].count("\n") + (
                1 if snippet_dict["content"] else 0
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
                if strict:
                    raise TokenLimitError(
                        f"Structural block exceeds maximum limit (tokens: {box_tokens} > {max_tokens}, "
                        f"lines: {box_lines} > {max_lines}, or functions: {int(is_function)} > {max_functions}).\n"
                        f"Content starting with: \n```\n{snippet_dict['content'][:100]}...\n```\n"
                        "Reason: Prevent splitting inside interest points (function, class, region, ...)\n"
                        "💡Hint: Consider increasing 'max_tokens', 'max_lines', or 'max_functions', "
                        "refactoring the oversized block, or setting 'strict=False' to allow automatic splitting of oversized blocks."
                    )
                else:  # Else split further
                    if self.verbose:
                        logger.warning(
                            "Splitting oversized block (tokens: {} lines: {}) into sub-chunks",
                            box_tokens,
                            box_lines,
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
                start_span = (
                    0 if start_line == 1 else cumulative_lengths[start_line - 2]
                )
                end_span = cumulative_lengths[end_line - 1]
                merged_chunk = Box(
                    {
                        "content": "\n".join(merged_content),
                        "metadata": {
                            "chunk_num": len(result_chunks) + 1,
                            "tree": self._merge_tree(relations_list),
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
            start_span = 0 if start_line == 1 else cumulative_lengths[start_line - 2]
            end_span = cumulative_lengths[end_line - 1]
            merged_chunk = Box(
                {
                    "content": "\n".join(merged_content),
                    "metadata": {
                        "chunk_num": len(result_chunks) + 1,
                        "tree": self._merge_tree(relations_list),
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
            result_chunks.append(merged_chunk)

        if self.verbose:
            logger.info(
                "Generated {} chunk(s) for the {}",
                len(result_chunks),
                (
                    f"source: {str(Path)}"
                    if (isinstance(str, Path) or is_path_like(source))
                    else f"code starting with:\n```\n{source[:100]}..\n```\n"
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
        include_comments: bool = False,
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
            include_comments (bool): Include comments in output chunks. Default: False.
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
