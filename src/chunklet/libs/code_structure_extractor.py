from __future__ import annotations
import regex as re
import json5
from pathlib import Path


class CodeStructureExtractor:
    """
    Stateless, multilingual extractor that organizes code into structured chunks.

    This class detects imports, classes, functions, methods, comments, and statements.
    It does not tokenize like a lexer or build a full AST like a compiler parser,
    but instead organizes code into useful blocks for documentation, analysis, or tooling.
    """

    def __init__(
        self, language: str, include_comments: bool = True, include_docstrings: bool = True
    ):
        """
        Initialize the extractor with language settings.

        Args:
            language (str): The target programming language (e.g., "python").
            include_comments (bool): Whether to include comments in the output chunks.
            include_docstrings (bool): Whether to include docstrings in the output chunks.

        Raises:
            ValueError: If the provided language is not supported.
        """
        self.language = language.lower()
        self.include_comments = include_comments
        self.include_docstrings = include_docstrings
        self.language_map = self._load_language_map()

        if self.language not in self.language_map:
            raise ValueError(f"Unsupported language: {language}")

        self.patterns = self.language_map[self.language]
        self.block_type = self.patterns.get("block_type", "indent")

        # Compile regex patterns for efficiency
        self.docstring_pattern = re.compile(
            r'(\"\"\"[\s\S]*?\"\"\"|\'\'\'[\s\S]*?\'\'\')',
            re.MULTILINE,
        )
        self.comment_single_pattern = re.compile(self.patterns.get("comment_single", ""))
        self.comment_multi_pattern = (
            re.compile(self.patterns.get("comment_multi", ""), re.MULTILINE)
            if self.patterns.get("comment_multi")
            else None
        )

    def _load_language_map(self) -> dict:
        """
        Load regex patterns for supported languages from a JSON5 config file.
        """
        path = Path(__file__).parent.parent / "static" / "language_map.json5"
        with open(path, "r", encoding="utf-8") as f:
            return json5.load(f)

    def dispatch(self, code: str) -> list[dict]:
        """
        Extract structured chunks from the given source code.
        This is the main orchestrator for the entire extraction process.
        """
        lines = code.splitlines()
        chunks = []
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            if not stripped:
                i += 1
                continue

            # Skip special language-specific headers (like PHP's opening tag)
            if self.language == "php" and stripped.startswith("<?php"):
                i += 1
                continue

            # Identify top-level elements and process their blocks
            matched = False
            for kind in ["import", "comment", "class", "function"]:
                if kind == "import" and self._match("import", line):
                    chunks.append(self._build_chunk("import", line, None, None, i, i))
                    i += 1
                    matched = True
                    break
                
                if kind == "comment" and self.include_comments and self._is_comment(line):
                    chunks.append(self._build_chunk("comment", line, None, None, i, i))
                    i += 1
                    matched = True
                    break

                if kind in ["class", "function"]:
                    m = self._match(kind, line, return_match=True)
                    if m:
                        name = m.group(1)
                        block_lines, end_index = self._extract_block(lines, i)
                        
                        # Split the block into its header, body, docstring, etc.
                        header, docstring, body_lines, comments_str = self._split_block_content(block_lines)

                        methods = []
                        if kind == "class":
                            methods = self._extract_methods(body_lines, i + (len(block_lines) - len(body_lines)))

                        # Reassemble the body without the methods for the main class body
                        body_text = self._rebuild_body_text(body_lines, methods)
                        
                        chunks.append(
                            self._build_chunk(
                                kind,
                                header,
                                docstring,
                                body_text,
                                i,
                                end_index,
                                name,
                                methods,
                                comments=comments_str,
                            )
                        )
                        i = end_index + 1
                        matched = True
                        break

            if not matched:
                # If no structural element was found, it's a statement
                chunks.append(self._build_chunk("statement", line, None, None, i, i))
                i += 1

        return chunks

    def _is_comment(self, line: str) -> bool:
        """Check if a line is a single or multi-line comment."""
        stripped = line.strip()
        return (
            (self.comment_single_pattern and self.comment_single_pattern.match(stripped))
            or (
                self.comment_multi_pattern
                and self.comment_multi_pattern.match(stripped)
            )
        )

    def _match(self, kind: str, line: str, return_match: bool = False):
        """Match a line against a regex pattern for a specific kind of element."""
        pattern = self.patterns.get(kind)
        if not pattern or not pattern.strip():
            return None
        regex = re.compile(pattern)
        match = regex.search(line)
        return match if return_match else bool(match)

    def _extract_block(self, lines: list[str], start: int) -> tuple[list[str], int]:
        """Extract a block of code starting from a given line, using indentation or braces."""
        if self.block_type == "indent":
            return self._extract_indent_block(lines, start)
        return self._extract_brace_block(lines, start)

    def _extract_indent_block(self, lines: list[str], start: int) -> tuple[list[str], int]:
        """Extract a block of code based on indentation (Python/Ruby style)."""
        base_indent = self._indent_level(lines[start])
        block = [lines[start]]
        i = start + 1
        
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                block.append(line)
                i += 1
                continue
            
            current_indent = self._indent_level(line)
            
            if self.language == "ruby" and line.strip() == "end":
                if current_indent < base_indent:
                    break
                block.append(line)
                i += 1
                continue
                
            if current_indent <= base_indent:
                break
                
            block.append(line)
            i += 1
            
        return block, i - 1

    def _extract_brace_block(self, lines: list[str], start: int) -> tuple[list[str], int]:
        """Extract a block of code based on curly braces (C/Java style)."""
        block = [lines[start]]
        depth = lines[start].count("{") - lines[start].count("}")
        i = start + 1
        
        while i < len(lines) and depth > 0:
            line = lines[i]
            block.append(line)
            depth += line.count("{") - line.count("}")
            i += 1
            
        return block, i - 1

    def _indent_level(self, line: str) -> int:
        """Calculate the indentation level of a line."""
        return len(line) - len(line.lstrip())

    def _split_block_content(self, block: list[str]) -> tuple[str, str | None, list[str], str | None]:
        """Split a block into header, docstring, comments, and body lines."""
        header = block[0]
        docstring, comments, start_body_idx = self._get_initial_doc_and_comments(block)
        body_lines = block[start_body_idx:]
        
        comments_str = "\n".join(comments) if comments else None
        
        return header, docstring, body_lines, comments_str

    def _get_initial_doc_and_comments(self, lines: list[str]) -> tuple[str | None, list[str], int]:
        """
        Extract the docstring and initial comments immediately following a header.
        Returns the docstring, a list of comment lines, and the index where the body begins.
        """
        docstring = None
        comments = []
        i = 1 # Start after the header line
        
        while i < len(lines):
            line = lines[i]
            stripped_line = line.strip()

            is_docstring = self.include_docstrings and not docstring and self.docstring_pattern.match(stripped_line)
            is_comment = self.include_comments and self._is_comment(line)
            is_empty = not stripped_line
            
            if is_docstring:
                # Capture the full docstring block
                ds_lines = [line]
                j = i + 1
                while j < len(lines) and self.docstring_pattern.match(lines[j].strip()):
                    ds_lines.append(lines[j])
                    j += 1
                docstring = "\n".join(ds_lines)
                i = j
                continue
            elif is_comment:
                comments.append(line)
                i += 1
                continue
            elif is_empty:
                i += 1
                continue
            
            # If we hit any code that isn't a docstring or comment, we're done
            break
            
        return docstring, comments, i

    def _extract_methods(self, body_lines: list[str], start_line_offset: int) -> list[dict]:
        """Extract method definitions from a list of body lines."""
        methods = []
        i = 0
        while i < len(body_lines):
            line = body_lines[i]
            m = self._match("method", line, return_match=True)
            if m:
                # If it's a method, extract its entire block recursively
                block_lines, end_index_local = self._extract_block(body_lines, i)
                end_line = start_line_offset + end_index_local

                # Now, split the method block itself
                method_header, method_docstring, method_body_lines, method_comments_str = self._split_block_content(block_lines)

                method_body = "\n".join(method_body_lines) if method_body_lines else None
                name = m.group(1)
                
                methods.append(
                    self._build_chunk(
                        "method",
                        method_header,
                        method_docstring,
                        method_body,
                        start_line_offset + i,
                        end_line,
                        name,
                        comments=method_comments_str,
                    )
                )
                i = end_index_local + 1
            else:
                i += 1
        return methods

    def _rebuild_body_text(self, body_lines: list[str], methods: list[dict]) -> str | None:
        """
        Rebuilds the body text by removing lines that are part of extracted methods.
        This ensures the main class/function body only contains what's left.
        """
        if not methods:
            return "\n".join(body_lines) if body_lines else None
        
        method_lines = set()
        for method in methods:
            start = method["start_line"] - method["start_line"]
            end = method["end_line"] - method["start_line"] + 1
            method_lines.update(range(start, end))

        cleaned_body_lines = [
            line for i, line in enumerate(body_lines) if i not in method_lines
        ]
        
        return "\n".join(cleaned_body_lines) if cleaned_body_lines else None

    def _build_chunk(
        self,
        type_: str,
        header: str,
        docstring: str | None,
        body: str | None,
        start: int,
        end: int,
        name: str | None = None,
        methods: list[dict] | None = None,
        comments: str | None = None,
    ) -> dict:
        """Build a structured chunk dictionary representing a code element."""
        return {
            "type": type_,
            "name": name,
            "namespace": None,
            "header": header,
            "docstring": docstring,
            "body": body,
            "comments": comments,
            "start_line": start + 1,
            "end_line": end + 1,
            "methods": methods or [],
        }

    def print_chunks(self, chunks: list[dict], indent: int = 0):
        """
        Print structured chunks recursively for human-readable inspection.

        Args:
            chunks (List[Dict]): The list of chunks to print.
            indent (int): The indentation level.
        """
        pad = " " * indent
        for idx, chunk in enumerate(chunks, 1):
            print(f"\n{pad}--- Chunk ---")
            print(f"{pad}Type: {chunk['type']}")
            if chunk["name"]:
                print(f"{pad}Name: {chunk['name']}")
            print(f"{pad}Lines: {chunk['start_line']}-{chunk['end_line']}")
            print(f"{pad}Header:\n{pad}{chunk['header']}")
            if chunk["docstring"]:
                print(f"{pad}Docstring:\n{pad}{chunk['docstring']}")
            if chunk["comments"]:
                print(f"{pad}Comments:\n{pad}{chunk['comments']}")
            if chunk["body"]:
                body_lines = chunk["body"].split("\n") if chunk["body"] else []
                formatted_body = "\n".join([f"{pad}{line}" for line in body_lines])
                print(f"{pad}Body:\n{formatted_body}")

            if chunk["methods"]:
                for m_idx, method in enumerate(chunk["methods"], 1):
                    print(f"\n{pad}    --- Method {m_idx} ---")
                    self.print_chunks([method], indent + 4)


if __name__ == "__main__":
    # Test with Python code
    python_code = '''
# Standard library imports
import os
import sys
from math import sqrt

# Top-level constant
PI = 3.14159

def top_level_function(x, y):
    """This function adds two numbers."""
    result = x + y
    return result

class Geometry:
    """Class representing basic geometric shapes."""
    # A wild comment appears!
    
    def __init__(self, name):
        """Initialize with shape name."""
        self.name = name

    def area(self):
        """Calculate area (stub)."""
        return 0

    def perimeter(self):
        """Calculate perimeter (stub)."""
        return 0

class Circle(Geometry):
    """Circle shape inheriting from Geometry."""

    def __init__(self, radius):
        super().__init__("Circle")
        self.radius = radius

    def area(self):
        """Calculate circle area."""
        # The area is calculated
        return PI * self.radius ** 2

    def perimeter(self):
        """Calculate circle perimeter."""
        return 2 * PI * self.radius

# Top-level statement
print("Geometry module loaded")
'''
    extractor = CodeStructureExtractor("python", include_comments=True, include_docstrings=True)
    structures = extractor.dispatch(python_code)
    extractor.print_chunks(structures)
