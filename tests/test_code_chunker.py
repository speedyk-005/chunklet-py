import re
import pytest
from more_itertools import split_at
from chunklet.code_chunker import CodeChunker
from chunklet import (
    MissingTokenCounterError,
    TokenLimitError,
    FileProcessingError,
    InvalidInputError,
)


# Helper function
def simple_token_counter(text: str) -> int:
    """Simple Token Counter For Testing."""
    return len(text.split())


# --- Code constants ---

PYTHON_CODE = '''
"""
Module docstring
"""

import os

class Calculator:
    """
    A simple calculator class.

    A calculator that Contains basic arithmetic operations for demonstration purposes.
    """

    def __init__(self):
        self.value = 0

    @property
    def current_value(self):
        """Get the current value."""
        return self.value

    def add(self, x, y):
        """Add two numbers and return result.

        This is a longer description that should be truncated
        in summary mode. It has multiple lines and details.
        """
        result = x + y
        return result

    def multiply(self, x, y):
        # Multiply two numbers
        return x * y

def standalone_function():
    """A standalone function."""
    return True
'''

CSHARP_CODE = """
using System;

namespace MyApp
{
    /// <summary>
    /// A simple calculator class.
    /// </summary>
    public class Calculator
    {
        /// <summary>
        /// Adds two numbers.
        /// </summary>
        public int Add(int x, int y)
        {
            int result = x + y;
            return result;
        }

        // Multiply two numbers
        public int Multiply(int x, int y)
        {
            return x * y;
        }
    }
}
"""

RUBY_CODE = """
# Module-level comment
# Represents the module or file-level description

=begin
A simple calculator class.
Contains basic arithmetic operations for demonstration purposes.

Fields:
- Description: Overview of calculator functionality.
- Version: Version of this calculator class.
=end
class Calculator
  # Add two numbers and return the result
  def add(x, y)
    result = x + y  # Store sum
    result
  end

  # Multiply two numbers
  def multiply(x, y)
    x * y
  end
end

# A standalone function
def standalone_function
  true
end
"""

LONG_FUNCTION_CODE = "def very_long_function():\n    " + "x = 1\n    " * 50
NON_EXISTENT_FILE = "/path/to/nonexistent/file.py"
MULTIPLE_SOURCES = [PYTHON_CODE, CSHARP_CODE, RUBY_CODE]


# --- Fixtures ---


@pytest.fixture
def chunker():
    """Provide a ready-to-use CodeChunker instance for tests."""
    return CodeChunker(token_counter=simple_token_counter)


# --- Language Paradigm Tests ---


@pytest.mark.parametrize(
    "code_string, max_tokens, max_lines, max_functions, expected_num_chunks",
    [
        (PYTHON_CODE, 40, None, None, 3),
        (CSHARP_CODE, 50, None, None, 2),
        (RUBY_CODE, 40, None, None, 3),
        (PYTHON_CODE, None, 10, None, 5),
        (PYTHON_CODE, None, None, 1, 5),
    ],
)
def test_chunking_with_different_constraints(
    chunker, code_string, max_tokens, max_lines, max_functions, expected_num_chunks
):
    """Test chunking with different constraints (max_tokens, max_lines, max_functions)."""
    chunks = chunker.chunk(
        code_string,
        max_tokens=max_tokens,
        max_lines=max_lines,
        max_functions=max_functions,
    )

    assert len(chunks) > 0
    if max_tokens is not None:
        assert all(
            simple_token_counter(chunk.content) <= max_tokens for chunk in chunks
        )

    assert len(chunks) == expected_num_chunks
    assert all(chunk.metadata.start_line <= chunk.metadata.end_line for chunk in chunks)
    assert all(
        hasattr(chunk.metadata, "tree") and chunk.metadata.tree for chunk in chunks
    )

    # Validate Line Continuity
    last_end = 0
    for chunk in chunks:
        if last_end > 0:
            assert chunk.metadata.start_line > last_end
        last_end = chunk.metadata.end_line

    # Test for Decorator Separation Bug: ensure decorators stay with their functions
    if max_functions is not None:
        for chunk in chunks:
            # Check for decorator and function patterns in the same chunk
            decorator_pos = chunk.content.find("@")
            function_pos = chunk.content.find("def")

            if decorator_pos != -1 and function_pos != -1:
                # If both decorator and function are in the same chunk,
                # decorator must come before the function definition
                assert (
                    decorator_pos < function_pos
                ), f"Decorator found after function in chunk: {chunk.content[:100]}..."


# --- Docstring Tests ---


@pytest.mark.parametrize(
    "code_string, all_mode_pattern, summary_mode_pattern",
    [
        # Python - test multi-line docstrings
        (
            PYTHON_CODE,
            r"Add two numbers and return result\.\s+This is a longer description that should be truncated",
            r"Add two numbers and return result\.",
        ),
        # C# - test XML docstrings with regex patterns
        (
            CSHARP_CODE,
            r"///\s*<summary>.*A simple calculator class.*</summary>",
            r"A simple calculator class\.",
        ),
    ],
)
def test_docstring_modes(chunker, code_string, all_mode_pattern, summary_mode_pattern):
    """Test docstring processing modes for Python and C#."""
    # Test "all" mode - full docstring should be present
    chunks_all = chunker.chunk(code_string, max_tokens=200, docstring_mode="all")
    content_all = "".join(chunk.content for chunk in chunks_all)

    assert re.search(
        all_mode_pattern, content_all, re.DOTALL
    ), f"Full docstring pattern not found in 'all' mode for {code_string[:20]}..."

    # Test "excluded" mode - docstring should be absent
    chunks_excluded = chunker.chunk(
        code_string, max_tokens=200, docstring_mode="excluded"
    )
    content_excluded = "".join(chunk.content for chunk in chunks_excluded)

    assert not re.search(
        all_mode_pattern, content_excluded, re.DOTALL
    ), f"Docstring found in 'excluded' mode for {code_string[:20]}..."

    # Test "summary" mode - only summary should be present
    chunks_summary = chunker.chunk(
        code_string, max_tokens=200, docstring_mode="summary"
    )
    content_summary = "".join(chunk.content for chunk in chunks_summary)

    assert re.search(
        summary_mode_pattern, content_summary
    ), f"Summary pattern not found in 'summary' mode for {code_string[:20]}..."

    # For summary mode, verify the full pattern is NOT present (truncated)
    if code_string == PYTHON_CODE:
        # For Python, the longer description should be truncated
        long_pattern = r"This is a longer description that should be truncated"
        assert not re.search(
            long_pattern, content_summary
        ), "Long description found in 'summary' mode for Python"
    elif code_string == CSHARP_CODE:
        # For C#, the detailed XML tags should be truncated
        detail_pattern = r"<field.*>.*</field>"
        assert not re.search(
            detail_pattern, content_summary
        ), "XML details found in 'summary' mode for C#"


# --- Comment Inclusion Tests ---


@pytest.mark.parametrize("include_comments", [True, False])
def test_comment_inclusion(chunker, include_comments):
    """Test Inclusion/Exclusion Of Comments."""
    chunks = chunker.chunk(
        PYTHON_CODE, max_tokens=200, include_comments=include_comments
    )
    content = "\n".join(chunk.content for chunk in chunks)

    # Use correct case and exact comment text from fixture
    if include_comments:
        assert "# Multiply two numbers" in content
    else:
        assert "# Multiply two numbers" not in content


# --- Error Handling Tests ---


def test_broken_token_counter():
    """Test Error When Token Counter Fails."""

    def broken_token_counter(text: str) -> int:
        raise ValueError("Token counter failed")

    chunker = CodeChunker(token_counter=broken_token_counter)
    with pytest.raises(Exception):  # Should raise from the broken token counter
        chunker.chunk("def test(): pass", max_tokens=30)


def test_missing_token_counter_error():
    """Test MissingTokenCounterError when token counter is required but not provided."""
    new_chunker = CodeChunker()  # chunker without a token counter
    with pytest.raises(MissingTokenCounterError):
        new_chunker.chunk(
            "def test(): pass",
            max_tokens=30,
        )


@pytest.mark.parametrize(
    "max_tokens, max_lines, max_functions",
    [
        (None, None, None),  # No limits provided
        (None, None, 0),  # Set max functions to 0
    ],
)
def test_invalid_constraints_error(max_tokens, max_lines, max_functions):
    """Test InvalidInputError for invalid constraint combinations."""
    new_chunker = CodeChunker()  # chunker without a token counter
    with pytest.raises(InvalidInputError):
        new_chunker.chunk(
            "def test(): pass",
            max_tokens=max_tokens,
            max_lines=max_lines,
            max_functions=max_functions,
        )


def test_empty_source_code():
    """Test that empty source code returns empty list."""
    chunker = CodeChunker()
    result = chunker.chunk("", max_lines=30)
    assert result == []


def test_code_chunker_with_file(tmp_path):
    """Test CodeChunker with temporary files - both valid Python and binary."""
    from chunklet import FileProcessingError

    chunker = CodeChunker(token_counter=simple_token_counter)

    # Test 1: Valid Python file
    python_file = tmp_path / "test_code.py"
    python_file.write_text(PYTHON_CODE)

    chunks = chunker.chunk(python_file, max_tokens=50)
    assert len(chunks) > 0
    assert all(chunk.metadata.start_line <= chunk.metadata.end_line for chunk in chunks)

    # Test 2: Binary file should raise FileProcessingError
    binary_file = tmp_path / "binary_file.bin"
    binary_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe\xfd\xfc")  # Binary data

    with pytest.raises(FileProcessingError, match="Binary file not supported"):
        chunker.chunk(binary_file, max_tokens=50)


def test_nonexistent_file(chunker):
    """Test Error For Non-Existent File."""
    with pytest.raises(FileProcessingError):
        chunker.chunk(NON_EXISTENT_FILE, max_tokens=30)


def test_oversized_block_error(chunker):
    """Test Error For Blocks Exceeding Max Tokens."""
    params = {
        "source": LONG_FUNCTION_CODE,
        "max_tokens": 30,
        "max_lines": 5,
        "max_functions": 1,
    }
    with pytest.raises(TokenLimitError):
        chunker.chunk(**params, strict=True)

    # should not raise on strict mode is disabled
    chunks = chunker.chunk(**params, strict=False)
    assert len(chunks) > 0  # Should split into multiple chunks


# --- Batch Chunking Tests ---


def test_batch_chunk_success(chunker):
    """Test successful batch processing of multiple sources."""
    separator = object()

    results = list(
        chunker.batch_chunk(
            sources=MULTIPLE_SOURCES,
            max_tokens=50,
            on_errors="skip",
            separator=separator,
        )
    )

    first_chunks = next(split_at(results, lambda x: x is separator))

    assert len(first_chunks) > 0

    # Verify all chunk have required attributes
    for chunk in first_chunks:
        assert hasattr(chunk, "content")
        assert hasattr(chunk.metadata, "tree")
        assert hasattr(chunk.metadata, "start_line")
        assert hasattr(chunk.metadata, "end_line")
        assert hasattr(chunk.metadata, "source")
        assert hasattr(chunk.metadata, "chunk_num")


@pytest.mark.parametrize("max_tokens", [50, 100, 200])
def test_batch_chunk_different_max_tokens(max_tokens, chunker):
    """Test batch processing with different max_tokens values."""

    chunks = list(
        chunker.batch_chunk(
            sources=MULTIPLE_SOURCES,
            max_tokens=max_tokens,
        )
    )

    assert len(chunks) > 0

    # Verify chunks don't exceed token limit
    for chunk in chunks:
        assert simple_token_counter(chunk.content) <= max_tokens


def test_batch_chunk_error_handling_on_task(chunker):
    """Test the on_errors parameter in batch_chunk."""

    sources_with_error = [NON_EXISTENT_FILE] + MULTIPLE_SOURCES

    # Test on_errors = 'raise'
    with pytest.raises(FileProcessingError):
        list(
            chunker.batch_chunk(
                sources=sources_with_error,
                max_tokens=50,
                on_errors="raise",
                show_progress=False,  # Disabled to prevent an unexpected hanging
            )
        )

    # Test on_errors = 'skip'
    # Should still get chunks from valid sources
    chunks = list(
        chunker.batch_chunk(sources=sources_with_error, max_tokens=50, on_errors="skip")
    )
    assert len(chunks) > 0

    # Test on_errors = 'break'
    # Should get no chunks since file error occurs first and breaks
    chunks = list(
        chunker.batch_chunk(
            sources=sources_with_error, max_tokens=50, on_errors="break"
        )
    )
    assert len(chunks) == 0
