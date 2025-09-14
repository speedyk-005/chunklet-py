from __future__ import annotations
from typing import Callable
from loguru import logger
from pydantic import ValidationError
from chunklet.libs.code_structure_extractor import CodeStructureExtractor
from chunklet.utils.error_utils import pretty_errors
from chunklet.models import CodeChunkerConfig, CodeChunkingConfig
from chunklet.exceptions import (
    ChunkletError,
    InvalidInputError,
    MissingTokenCounterError,
)


class CodeChunker:
    """A code chunker that splits code into manageable chunks with token limits.

    Features:
    - Splits code based on structural elements (classes, functions, methods, etc.)
    - Handles class continuations with ellipsis markers
    - Supports multiple programming languages
    - Provides verbose logging for debugging
    - Includes default token counter functionality
    - Pydantic-based configuration validation
    """

    def __init__(
        self,
        language: str = "python",
        include_comments: bool = True,
        include_docstrings: bool = True,
        verbose: bool = False,
        token_counter: Callable = None,
    ):
        """Initialize the chunker with language settings.

        Args:
            language (str): The target programming language (e.g., "python", "javascript").
            include_comments (bool): Whether to include comments in the output chunks.
            include_docstrings (bool): Whether to include docstrings in the output chunks.
            verbose (bool): Whether to enable verbose logging for debugging.
            token_counter (Callable): Default token counter function. If None, uses a simple word-based counter.

        Raises:
            InvalidInputError: If the provided configuration is invalid.
        """
        try:
            self.config = CodeChunkerConfig(
                language=language,
                include_comments=include_comments,
                include_docstrings=include_docstrings,
                verbose=verbose,
                token_counter=token_counter,
            )
        except Exception as e:
            raise InvalidInputError(
                f"Error: Invalid configuration provided.\nDetails: {pretty_errors(e)}"
            )

        try:
            self.extractor = CodeStructureExtractor(
                self.config.language,
                self.config.include_comments,
                self.config.include_docstrings,
            )
        except ValueError as e:
            raise InvalidInputError(str(e))
        self.token_counter = self.config.token_counter

    def _count_tokens(self, text: str, token_counter: Callable[[str], int]) -> int:
        """
        Safely count tokens, handling potential errors from the token_counter.

        Args:
            text (str): The text to count tokens from.
            token_counter (Callable[[str], int]): The token counter function.

        Returns:
            int: The number of tokens in the text.

        Raises:
            ChunkletError: If the token counter fails.
        """
        try:
            return token_counter(text)
        except Exception as e:
            raise ChunkletError(
                f"Token counter failed while processing text starting with: '{text[:100]}...'.\n"
                f"💡 Hint: Please ensure the token counter function handles all edge cases and returns an integer.\nDetails: {e}"
            ) from e

    def chunk(
        self,
        code: str,
        token_counter: Callable = None,
        max_tokens: int = 256,
    ):
        """Split code into chunks with soft and max_tokens limits.

        Args:
            code (str): The source code to chunk.
            token_counter (Callable): Function that counts tokens in text. If None, uses the default token counter.
            max_tokens (int): The maximum number of tokens allowed per chunk.

        Returns:
            List[Dict]: List of chunks with text and metadata.

        Raises:
            InvalidInputError: If any element exceeds the max_tokens limit or configuration is invalid.
            MissingTokenCounterError: If no token counter is provided and default is not set.
        """
        token_counter = token_counter or self.token_counter

        params = {
            "code": code,
            "token_counter": token_counter,
            "max_tokens": max_tokens,
        }

        try:
            config = CodeChunkingConfig(**params)
        except Exception as e:
            raise InvalidInputError(f"Validation Error: {str(e)}")

        token_counter = config.token_counter
        max_tokens = config.max_tokens

        chunks = []
        current_chunk = []
        current_tokens = 0

        if self.config.verbose:
            logger.info(f"Starting chunking with limits: max_tokens={max_tokens}")

        # Extract the code into structural elements
        extracted_elements = self.extractor.dispatch(code)

        if self.config.verbose:
            logger.info(f"Extracted {len(extracted_elements)} structural elements")

        for element in extracted_elements:
            # Handle class elements specially - they contain methods
            if element["type"] == "class" and element.get("methods"):
                class_chunks = self._handle_class_element(
                    element,
                    current_chunk,
                    current_tokens,
                    max_tokens,
                    token_counter,
                )

                if class_chunks:
                    # If we have existing content, finalize current chunk
                    if current_chunk:
                        chunks.append(self._create_chunk(current_chunk))

                    # Add class chunks
                    chunks.extend(class_chunks)
                    current_chunk = []
                    current_tokens = 0
                continue

            # For regular elements
            element_text = self._element_to_text(element)
            element_tokens = self._count_tokens(element_text, token_counter)

            # Check if element exceeds limit
            if element_tokens > max_tokens:
                if not current_chunk:
                    raise InvalidInputError(
                        f"The element '{element.get('name', element['type'])}' ({element_tokens} tokens) "
                        f"is too large to fit in a single chunk with a max limit of {max_tokens}. "
                        "\n💡 Hint: Consider increasing the 'max_tokens' parameter or refactoring the element."
                    )
                else:
                    chunks.append(self._create_chunk(current_chunk))
                    current_chunk = [element]
                    current_tokens = element_tokens
            elif current_tokens + element_tokens > max_tokens:
                chunks.append(self._create_chunk(current_chunk))
                current_chunk = [element]
                current_tokens = element_tokens
            else:
                current_chunk.append(element)
                current_tokens += element_tokens

        # Add final chunk
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk))

        if self.config.verbose:
            logger.info(f"Created {len(chunks)} total chunks")

        return chunks

    def _handle_class_element(
        self,
        element: dict,
        current_chunk: list,
        current_tokens: int,
        max_tokens: int,
        token_counter: Callable,
    ) -> List[str]:
        """Handle class elements with their methods, splitting across chunks if needed.

        Args:
            element (Dict): The class element to process.
            current_chunk (list): Current chunk being built.
            current_tokens (int): Current token count in chunk.
            max_tokens (int): The maximum number of tokens allowed per chunk.
            token_counter (Callable): Function to count tokens.

        Returns:
            list[dict]: List of class chunks, empty if class should be handled in current chunk.

        Raises:
            InvalidInputError: If any method exceeds max_tokens limit.
        """
        chunks = []

        # Create class header text
        class_header_text = self._element_to_text(
            {
                "header": element["header"],
                "docstring": element["docstring"],
                "comments": element["comments"],
                "body": None,
            }
        )
        class_header_tokens = self._count_tokens(class_header_text, token_counter)

        # Start with class header
        current_class_elements = [
            {
                "type": "class",
                "name": element["name"],
                "header": element["header"],
                "docstring": element["docstring"],
                "comments": element["comments"],
                "body": None,
                "start_line": element["start_line"],
                "end_line": element["start_line"],
            }
        ]
        current_class_tokens = class_header_tokens

        # Add methods to the class chunk
        for method in element["methods"]:
            method_text = self._element_to_text(method)
            method_tokens = self._count_tokens(method_text, token_counter)

            # Check if individual method exceeds limit
            if method_tokens > max_tokens:
                raise InvalidInputError(
                    f"The method '{method.get('name', 'unnamed')}' ({method_tokens} tokens) is "
                    f"too large to fit in a single chunk with a max limit of {max_tokens}. "
                    "\n💡 Hint: Consider increasing the 'max_tokens' parameter or refactoring the method."
                )

            # If method doesn't fit in current class chunk, create continuation
            if current_class_tokens + method_tokens > max_tokens:
                # Add continuation marker to current class chunk
                if current_class_elements:
                    # Add ellipsis at the end of the current chunk
                    current_class_elements.append(
                        {
                            "type": "continuation_marker",
                            "header": "    ...",
                            "docstring": None,
                            "comments": None,
                            "body": None,
                        }
                    )
                    chunks.append(self._create_chunk(current_class_elements))

                # Create new chunk with class header and this method
                current_class_elements = [
                    {
                        "type": "class_continuation",
                        "name": element["name"],
                        "header": element["header"],
                        "docstring": None,
                        "comments": None,
                        "body": None,
                        "start_line": element["start_line"],
                        "end_line": element["start_line"],
                    },
                    {
                        "type": "continuation_marker",
                        "header": "    ...",
                        "docstring": None,
                        "comments": None,
                        "body": None,
                    },
                    method,
                ]
                current_class_tokens = (
                    self._count_tokens(element["header"], token_counter) + method_tokens
                )
            else:
                current_class_elements.append(method)
                current_class_tokens += method_tokens

        # Add final class chunk
        if current_class_elements:
            chunks.append(self._create_chunk(current_class_elements))

        return chunks

    def _element_to_text(self, element: Dict) -> str:
        """Convert an extracted element back to text representation.

        Args:
            element (dict): The element to convert to text.

        Returns:
            str: The text representation of the element.
        """
        parts = []

        # Add header
        if element["header"]:
            parts.append(element["header"])

        # Add docstring
        if element["docstring"]:
            parts.append(element["docstring"])

        # Add comments
        if element["comments"]:
            parts.append(element["comments"])

        # Add body
        if element["body"]:
            parts.append(element["body"])

        return "\n".join(parts)

    def _create_chunk(self, elements: List[Dict]) -> Dict:
        """Create a final chunk from a list of elements, returning a dictionary with text and metadata."""
        chunk_text = "\n".join([self._element_to_text(element) for element in elements])

        start_line = None
        for element in elements:
            if "start_line" in element and element["start_line"] is not None:
                start_line = element["start_line"]
                break

        end_line = None
        for element in reversed(elements):
            if "end_line" in element and element["end_line"] is not None:
                end_line = element["end_line"]
                break

        return {
            "content": chunk_text,
            "startline": start_line,
            "endline": end_line,
        }


# -- Example usage --
if __name__ == "__main__":
    import re

    def dummy_token_counter(text: str) -> int:
        """Simple token counter for demonstration"""
        if not text:
            return 0
        return len(re.findall(r"\w+|\S", text))

    python_code = '''
class LargeClass:
    """A class with many methods that might need splitting"""

    def method1(self):
        """First method with some content"""
        print("Method 1")
        return "result1"

    def method2(self):
        """Second method with more content"""
        for i in range(10):
            print(f"Method 2 iteration {i}")
        return "result2"

    def method3(self):
        """Third method with even more content"""
        data = [x for x in range(100) if x % 2 == 0]
        result = sum(data) * 2
        return f"Final result: {result}"

    def method4(self):
        """Fourth method"""
        # Complex calculation
        value = 42
        for i in range(5):
            value += i * 2
        return value

# Some other code
def standalone_function():
    """A standalone function"""
    return "hello world"

import math
from collections import defaultdict
'''

    chunker = CodeChunker("python", include_comments=True, include_docstrings=True)
    chunks = chunker.chunk(python_code, dummy_token_counter, max_tokens=100)

    print(f"Total chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks, 1):
        print(f"\n=== Chunk {i} ===")
        print(f"Content:\n{chunk['content']}")
        print(f"Start Line: {chunk['startline']}, End Line: {chunk['endline']}")
        print(f"--- Estimated tokens: {dummy_token_counter(chunk['content'])} ---")
