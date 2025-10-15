import pytest
import textwrap
import re
from chunklet.experimental.code_chunker import CodeChunker
from chunklet.exceptions import (
    MissingTokenCounterError,
    TokenLimitError,
    FileProcessingError,
    InvalidInputError,
)
from loguru import logger

# Silent logging
logger.remove()

# Helper function
def simple_token_counter(text: str) -> int:
    """Simple Token Counter For Testing."""
    return len(text.split())


def broken_token_counter(text: str) -> int:
    """Token counter that raises an error."""
    raise ValueError("Token counter failed")


# --- Fixtures ---


@pytest.fixture
def code_chunker():
    """Provide a ready-to-use CodeChunker instance for tests."""
    return CodeChunker(token_counter=simple_token_counter)


@pytest.fixture
def python_code():
    return textwrap.dedent(
        """\
        \"\"\"
        Module docstring
        \"\"\"

        import os

        class Calculator:
            \"\"\"
            A simple calculator class.
            
            A calculator that Contains basic arithmetic operations
            for demonstration purposes. 
            \"\"\"

            def add(self, x, y):
                \"\"\"Add two numbers and return result.

                This is a longer description that should be truncated
                in summary mode. It has multiple lines and details.
                \"\"\"
                result = x + y
                return result

            def multiply(self, x, y):
                # Multiply two numbers
                return x * y

        def standalone_function():
            \"\"\"A standalone function.\"\"\"
            return True
    """
    )


@pytest.fixture
def csharp_code():
    """C# test code with XML docstrings."""
    return textwrap.dedent(
        """\
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
    )


@pytest.fixture
def ruby_code():
    """Ruby test code - represents END-BASED languages."""
    return textwrap.dedent(
        """\
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
    )


@pytest.fixture
def long_function_code():
    """Code with a function that exceeds token limits."""
    return "def very_long_function():\n    " + "x = 1\n    " * 50


@pytest.fixture
def multiple_sources(python_code, csharp_code, ruby_code):
    """Multiple code sources for batch testing."""
    return [python_code, csharp_code, ruby_code]


@pytest.fixture
def non_existent_file():
    """Non-existent file path."""
    return "/path/to/nonexistent/file.py"


# --- Language Paradigm Tests ---


@pytest.mark.parametrize(
    "language_fixture,max_tokens",
    [
        ("python_code", 40),
        ("csharp_code", 50),
        ("ruby_code", 30),
    ],
)
def test_language_chunking(code_chunker, request, language_fixture, max_tokens):
    """Test Chunking For Different Language Paradigms."""
    code = request.getfixturevalue(language_fixture)
    chunks = code_chunker.chunk(code, max_tokens=max_tokens)

    assert len(chunks) > 0
    assert all(simple_token_counter(chunk.content) <= max_tokens for chunk in chunks)
    assert all(chunk.start_line <= chunk.end_line for chunk in chunks)
    assert all(hasattr(chunk, "tree") and chunk.tree for chunk in chunks)

    # Validate Line Continuity
    last_end = 0
    for chunk in chunks:
        if last_end > 0:
            assert chunk.start_line > last_end
        last_end = chunk.end_line


# --- Docstring Tests ---


@pytest.mark.parametrize(
    "language_fixture, all_mode_pattern, summary_mode_pattern",
    [
        # Python - test multi-line docstrings
        (
            "python_code",
            r"Add two numbers and return result\.\s+This is a longer description that should be truncated",
            r"Add two numbers and return result\.",
        ),
        # C# - test XML docstrings with regex patterns
        (
            "csharp_code",
            r"///\s*<summary>.*A simple calculator class.*</summary>",
            r"A simple calculator class\.",
        ),
    ],
)
def test_docstring_modes(
    code_chunker, request, language_fixture, all_mode_pattern, summary_mode_pattern
):
    """Test docstring processing modes for Python and C#."""
    code = request.getfixturevalue(language_fixture)

    # Test "all" mode - full docstring should be present
    chunks_all = code_chunker.chunk(code, max_tokens=200, docstring_mode="all")
    content_all = "".join(chunk.content for chunk in chunks_all)
    assert re.search(
        all_mode_pattern, content_all, re.DOTALL
    ), f"Full docstring pattern not found in 'all' mode for {language_fixture}"

    # Test "excluded" mode - docstring should be absent
    chunks_excluded = code_chunker.chunk(
        code, max_tokens=200, docstring_mode="excluded"
    )
    content_excluded = "".join(chunk.content for chunk in chunks_excluded)
    assert not re.search(
        all_mode_pattern, content_excluded, re.DOTALL
    ), f"Docstring found in 'excluded' mode for {language_fixture}"

    # Test "summary" mode - only summary should be present
    chunks_summary = code_chunker.chunk(code, max_tokens=200, docstring_mode="summary")
    content_summary = "".join(chunk.content for chunk in chunks_summary)
    assert re.search(
        summary_mode_pattern, content_summary
    ), f"Summary pattern not found in 'summary' mode for {language_fixture}"

    # For summary mode, verify the full pattern is NOT present (truncated)
    if language_fixture == "python_code":
        # For Python, the longer description should be truncated
        long_pattern = r"This is a longer description that should be truncated"
        assert not re.search(
            long_pattern, content_summary
        ), f"Long description found in 'summary' mode for {language_fixture}"
    elif language_fixture == "csharp_code":
        # For C#, the detailed XML tags should be truncated
        detail_pattern = r"<field.*>.*</field>"
        assert not re.search(
            detail_pattern, content_summary
        ), f"XML details found in 'summary' mode for {language_fixture}"


# --- Comment Inclusion Tests ---


@pytest.mark.parametrize("include_comments", [True, False])
def test_comment_inclusion(code_chunker, python_code, include_comments):
    """Test Inclusion/Exclusion Of Comments."""
    chunks = code_chunker.chunk(python_code, include_comments=include_comments)
    content = "\n".join(chunk.content for chunk in chunks)

    # Use correct case and exact comment text from fixture
    if include_comments:
        assert "# Multiply two numbers" in content
    else:
        assert "# Multiply two numbers" not in content


# --- Error Handling Tests ---


def test_missing_token_counter():
    """Test Error When No Token Counter Is Provided."""
    chunker = CodeChunker(token_counter=None)
    with pytest.raises(MissingTokenCounterError):
        chunker.chunk("def test(): pass")


def test_broken_token_counter():
    """Test Error When Token Counter Fails."""
    chunker = CodeChunker(token_counter=broken_token_counter)
    with pytest.raises(Exception):  # Should raise from the broken token counter
        chunker.chunk("def test(): pass")


def test_nonexistent_file(code_chunker, non_existent_file):
    """Test Error For Non-Existent File."""
    with pytest.raises(FileProcessingError):
        code_chunker.chunk(non_existent_file)


def test_oversized_block_error(code_chunker, long_function_code):
    """Test Error For Blocks Exceeding Max Tokens."""
    with pytest.raises(TokenLimitError):
        code_chunker.chunk(long_function_code, max_tokens=30, strict_mode=True)

    # should not raise on strict mode is disabled
    chunks = code_chunker.chunk(long_function_code, max_tokens=30, strict_mode=False)
    assert len(chunks) > 0  # Should split into multiple chunks


# --- Batch Chunking Tests ---


def test_batch_chunk_success(code_chunker, multiple_sources):
    """Test successful batch processing of multiple sources."""
    chunks = list(
        code_chunker.batch_chunk(
            sources=multiple_sources,
            max_tokens=50,
            n_jobs=2,
            show_progress=False,
            on_errors="skip",
        )
    )

    assert len(chunks) > 0
    # Verify all chunks have required attributes
    for chunk in chunks:
        assert hasattr(chunk, "content")
        assert hasattr(chunk, "tree")
        assert hasattr(chunk, "start_line")
        assert hasattr(chunk, "end_line")
        assert hasattr(chunk, "source_path")


def test_batch_chunk_empty_sources(code_chunker):
    """Test batch processing with empty sources list."""
    chunks = list(code_chunker.batch_chunk(sources=[]))
    assert len(chunks) == 0


def test_batch_chunk_invalid_sources_type(code_chunker):
    """Test batch processing with invalid sources type."""
    with pytest.raises(InvalidInputError):
        list(code_chunker.batch_chunk(sources="not_a_list"))


def test_batch_chunk_invalid_n_jobs(code_chunker, multiple_sources):
    """Test batch processing with invalid n_jobs parameter."""
    with pytest.raises(InvalidInputError):
        list(code_chunker.batch_chunk(sources=multiple_sources, n_jobs=0))


def test_batch_chunk_invalid_on_errors(code_chunker, multiple_sources):
    """Test batch processing with invalid on_errors parameter."""
    with pytest.raises(InvalidInputError):
        list(code_chunker.batch_chunk(sources=multiple_sources, on_errors="invalid"))


def test_batch_chunk_file_error_raise(
    code_chunker, multiple_sources, non_existent_file
):
    """Test batch processing with raise error strategy for file errors."""
    sources_with_error = multiple_sources + [non_existent_file]

    with pytest.raises(FileProcessingError):
        list(
            code_chunker.batch_chunk(
                sources=sources_with_error, on_errors="raise", show_progress=False
            )
        )


def test_batch_chunk_file_error_ignore(
    code_chunker, multiple_sources, non_existent_file
):
    """Test batch processing with ignore error strategy for file errors."""
    sources_with_error = multiple_sources + [non_existent_file]

    chunks = list(
        code_chunker.batch_chunk(
            sources=sources_with_error, on_errors="skip", show_progress=False
        )
    )

    # Should still get chunks from valid sources
    assert len(chunks) > 0


def test_batch_chunk_file_error_break(
    code_chunker, multiple_sources, non_existent_file
):
    """Test batch processing with break error strategy for file errors."""
    sources_with_error = [non_existent_file] + multiple_sources  # Error first

    chunks = list(
        code_chunker.batch_chunk(
            sources=sources_with_error, on_errors="break", show_progress=False
        )
    )

    # Should get no chunks since file error occurs first and breaks
    assert len(chunks) == 0


def test_batch_chunk_different_max_tokens(code_chunker, multiple_sources):
    """Test batch processing with different max_tokens values."""
    for max_tokens in [50, 100, 200]:
        chunks = list(
            code_chunker.batch_chunk(
                sources=multiple_sources, max_tokens=max_tokens, show_progress=False
            )
        )

        assert len(chunks) > 0
        # Verify chunks don't exceed token limit
        for chunk in chunks:
            assert simple_token_counter(chunk.content) <= max_tokens


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
