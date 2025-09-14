"""Tests for the CodeChunker class."""

import pytest
from chunklet import CodeChunker, InvalidInputError, MissingTokenCounterError
from unittest.mock import MagicMock


@pytest.fixture
def code_chunker():
    """Provides a CodeChunker instance with a simple token counter."""

    def simple_token_counter(text: str) -> int:
        return len(text.split())

    return CodeChunker(language="python", token_counter=simple_token_counter)


# Test initialization
def test_code_chunker_init(code_chunker):
    assert code_chunker.config.language == "python"
    assert code_chunker.config.include_comments is True
    assert code_chunker.config.include_docstrings is True
    assert code_chunker.config.verbose is False
    assert callable(code_chunker.token_counter)


def test_code_chunker_init_invalid_input():
    """
    Test that CodeChunker raises InvalidInputError for an unsupported language for an invalid token counter.
    """

    with pytest.raises(
        InvalidInputError, match="Unsupported language: unsupported_lang"
    ):
        CodeChunker(language="unsupported_lang")

    with pytest.raises(InvalidInputError, match="token_counter"):
        CodeChunker(token_counter="not_a_callable")


# Test basic chunking
def test_code_chunker_basic_chunking(code_chunker):
    """Test basic code chunking functionality."""
    code = '''
def func_a():
    """Docstring for func_a"""
    pass

class MyClass:
    def method_a(self):
        pass
'''
    chunks = code_chunker.chunk(code, max_tokens=20)
    assert len(chunks) > 0
    assert isinstance(chunks[0], dict)
    assert "content" in chunks[0]
    assert "startline" in chunks[0]
    assert "endline" in chunks[0]

    # Verify content of some chunks
    assert "def func_a():" in chunks[0]["content"]
    assert "class MyClass:" in chunks[1]["content"]


def test_code_chunker_element_exceeds_limit(code_chunker):
    """Test that InvalidInputError is raised when an element exceeds the hard token limit."""
    long_body_code = '''
def handle_command(command, state):
    """Handles a command in a simple state machine."""
    match command:
        case "start":
            print("Starting the process.")
            state["status"] = "running"
        case "stop":
            print("Stopping the process.")
            state["status"] = "stopped"
        case "pause":
            print("Pausing the process.")
            state["status"] = "paused"
        case "resume":
            print("Resuming the process.")
            state["status"] = "running"
        case "status":
            print(f"Current status is: {state['status']}")
        case "reset":
            print("Resetting the state.")
            state["status"] = "idle"
            state["data"] = []
        case "add_data":
            print("Adding data.")
            state["data"].append("some_data")
        case "process_data":
            print("Processing data.")
            if state["data"]:
                # do something with data
                pass
        case _:
            print("Unknown command.")
    return state
'''
    with pytest.raises(
        InvalidInputError, match="is too large to fit in a single chunk"
    ):
        code_chunker.chunk(long_body_code, max_tokens=30)


def test_code_chunker_missing_token_counter():
    """Test that InvalidInputError is raised when no token counter is provided."""
    chunker_no_default_tc = CodeChunker(language="python", token_counter=None)
    with pytest.raises(InvalidInputError):
        chunker_no_default_tc.chunk("def func(): pass", token_counter=None)


def test_code_chunker_no_docstrings():
    """Test that docstrings are excluded when include_docstrings is False."""
    code = '''def func_a():
    """This is a docstring."""
    pass'''
    chunker = CodeChunker(
        language="python",
        include_docstrings=False,
        token_counter=lambda s: len(s.split()),
    )
    chunks = chunker.chunk(code, max_tokens=10)
    print(chunks)
    assert "This is a docstring." not in chunks[0]["content"]


def test_code_chunker_no_comments():
    """Test that comments are excluded when include_comments is False."""
    code = """# This is a comment
def func_a():
    pass"""
    chunker = CodeChunker(
        language="python",
        include_comments=False,
        token_counter=lambda s: len(s.split()),
    )
    chunks = chunker.chunk(code, max_tokens=10)
    print(chunks)
    assert "This is a comment" not in chunks[0]["content"]
