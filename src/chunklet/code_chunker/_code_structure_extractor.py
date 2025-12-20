"""
Code Structure Extractor

Internal module for extracting code structures from source code.
Split from CodeChunker for modularity.
"""

from pathlib import Path
from itertools import accumulate
import regex as re
from collections import defaultdict, namedtuple

try:
    from charset_normalizer import from_path
    from littletree import Node
    import defusedxml.ElementTree as ET
except ImportError:
    from_path, Node, ET = None, None, None

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
from chunklet.common.validation import validate_input
from chunklet.exceptions import FileProcessingError


CodeLine = namedtuple(
    "CodeLine", ["line_number", "content", "indent_level", "func_partial_signature"]
)


class CodeStructureExtractor:
    """
    Internal class for extracting structural units from source code.
    """

    @validate_input
    def __init__(self, verbose: bool = False):
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
        if from_path is None:
            raise ImportError(
                "The 'charset-normalizer' library is not installed. "
                "Please install it with 'pip install charset-normalizer>=3.4.0' "
                "or install the code processing extras with 'pip install chunklet-py[code]'"
            )

        if isinstance(source, Path) or is_path_like(source):
            path = Path(source)
            if not path.exists():
                raise FileProcessingError(f"File does not exist: {path}")
            if is_binary_file(path):
                raise FileProcessingError(f"Binary file not supported: {path}")

            match = from_path(str(path)).best()
            content = str(match) if match else ""
            if self.verbose:
                logger.info(
                    "Successfully read %d characters from {} using charset detection",
                    len(content),
                    path,
                )
            return content
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
                if stripped_line and not re.fullmatch(r"\s*<[^>]*>\s*", stripped_line):
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
        # Call at first to preserve span accurary befire any altering
        # Pad with 0 so cumulative_lengths[line_number - 1] == start_char_offset
        cumulative_lengths = (0,) + tuple(
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
        if docstring_mode == "summary":
            code = DOCSTRING_STYLE_ONE.sub(
                lambda m: self._summarize_docstring_style_one(m), code
            )
            code = DOCSTRING_STYLE_TWO.sub(
                lambda m: self._summarize_docstring_style_two(m), code
            )
        elif docstring_mode == "excluded":
            code = DOCSTRING_STYLE_ONE.sub(
                lambda m: self._replace_with_newlines(m), code
            )
            code = DOCSTRING_STYLE_TWO.sub(
                lambda m: self._replace_with_newlines(m), code
            )
        # Else "all": do nothing

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
            code = pattern.sub(
                lambda match, tag=tag: self._annotate_block(tag, match), code
            )

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

    def _handle_annotated_line(
        self,
        line: str,
        line_no: int,
        matched: re.Match,
        indent_level: int,
        buffer: dict[list],
        state: dict,
    ):
        """
        Handle processing of annotated lines (comments, docstrings, etc.).

        Args:
            line (str): The annotated line detected.
            line_no (int): The number of the line based on one index.
            indent_level (int):
            matched(re.Match): Regex match object for the annotated line.
            buffer (dict[list]): Buffer for intermediate processing.
            state (dict): The state dictionary that holds info about current structure, last indentation level,
                function scope, and the snippet dicts (extracted blocks).
        """
        # Flush if DOC buffered lines are not consecutive
        if (
            len(buffer["META"]) == 1  # First decorator/attribute
            or buffer["DOC"]
            and buffer["DOC"][-1].line_number != line_no - 1
        ):
            self._flush_snippet(state["curr_struct"], state["snippet_dicts"], buffer)
            state["inside_func"] = False

        tag = matched.group(1)
        deannoted_line = (
            line[: matched.start()] + line[matched.end() :]
        )  # slice off the annotation
        buffer[tag].append(CodeLine(line_no, deannoted_line, indent_level, None))

    def _handle_block_start(
        self,
        line: str,
        indent_level: int,
        buffer: dict[list],
        state: dict,
        source: str | Path,
        func_start: str | None = None,
    ):
        """
        Detects top-level namespace or function starts and performs language-aware flushing.

        Args:
            line (str): The annotated line detected.
            indent_level (int):
            buffer (dict[list]): Buffer for intermediate processing.
            state (dict): The state dictionary that holds info about current structure, last indentation level,
                function scope, and the snippet dicts (extracted blocks).
            source (str | Path): Raw code string or Path to source file.
            func_start (str, optional): Line corresponds to a function partial signature
        """
        namespace_start = NAMESPACE_DECLARATION.match(line)

        if (
            namespace_start
            # If decorator/attribute exists in buffer, skip flushing
            or (func_start and not (state["inside_func"] or buffer["META"]))
        ):
            state["last_indent"] = indent_level

            # If it is a Python code, we can flush everything, else we won't flush the docstring yet
            # This helps including the docstring that is on top of block definition in the other languages
            if state["curr_struct"]:
                if is_python_code(source):
                    self._flush_snippet(
                        state["curr_struct"], state["snippet_dicts"], buffer
                    )
                else:
                    doc = buffer.pop("DOC", [])
                    self._flush_snippet(
                        state["curr_struct"], state["snippet_dicts"], buffer
                    )
                    buffer.clear()
                    buffer["doc"] = doc

        # Nestled blocks are not to be extracted
        if func_start:
            state["inside_func"] = True

    def extract_code_structure(
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

        state = {
            "curr_struct": [],
            "last_indent": 0,
            "inside_func": False,
            "snippet_dicts": [],
        }
        buffer = defaultdict(list)

        for line_no, line in enumerate(source_code.splitlines(), start=1):
            indent_level = len(line) - len(line.lstrip())

            # Detect annotated lines
            matched = re.search(r"\(-- ([A-Z]+) -->\) ", line)
            if matched:
                self._handle_annotated_line(
                    line=line,
                    line_no=line_no,
                    indent_level=indent_level,
                    matched=matched,
                    buffer=buffer,
                    state=state,
                )
                continue

            # Manage block accumulation

            func_start = FUNCTION_DECLARATION.match(line)
            func_start = func_start.group(0) if func_start else None

            self._handle_block_start(
                line=line,
                indent_level=indent_level,
                buffer=buffer,
                state=state,
                source=source,
                func_start=func_start,
            )

            if not state["curr_struct"]:  # Fresh block
                state["curr_struct"] = [
                    CodeLine(
                        line_no,
                        line,
                        indent_level,
                        func_start,
                    )
                ]
                continue

            if (
                line.strip()
                and indent_level <= state["last_indent"]
                and not (OPENER.match(line) or CLOSURE.match(line))
            ):  # Block end
                self._flush_snippet(
                    state["curr_struct"], state["snippet_dicts"], buffer
                )
                state["last_indent"] = 0
                state["inside_func"] = False

            state["curr_struct"].append(
                CodeLine(line_no, line, indent_level, func_start)
            )

        # Append last snippet
        if state["curr_struct"]:
            self._flush_snippet(state["curr_struct"], state["snippet_dicts"], buffer)

        snippet_dicts = self._post_processing(state["snippet_dicts"])
        if self.verbose:
            logger.info(
                "Extracted {} structural blocks from source", len(snippet_dicts)
            )

        return snippet_dicts, cumulative_lengths
