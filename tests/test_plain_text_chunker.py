"""
This module contains unit tests for the PlainTextChunker class,
covering its core functionality, various chunking modes, overlap behavior,
and batch processing capabilities.
"""
import pytest
import re
from chunklet.sentence_splitter import SentenceSplitter
from chunklet.plain_text_chunker import PlainTextChunker
from chunklet.exceptions import InvalidInputError, CallbackExecutionError, MissingTokenCounterError
from loguru import logger


# Silent logging
logger.remove()


# --- Constants ---

ENGLISH_TEXT = """
She loves cooking. He studies AI. "You are a Dr.", she said. The weather is great. We play chess. Books are fun, aren't they?
 
The Playlist contains:
  - two videos
  - one image
  - one music

Robots are learning. It's raining. Let's code. Mars is red. Sr. sleep is rare. Consider item 1. This is a test. The year is 2025. This is a good year since N.A.S.A. reached 123.4 light year more.
"""


# --- Fixtures ---
@pytest.fixture
def chunker():
    """Provides a configured Chunklet instance for testing"""

    def simple_token_counter(text: str) -> int:
        return len(text.split())

    return PlainTextChunker(token_counter=simple_token_counter)


# --- Core Tests ---
def test_init_validation_error():
    """Test that InvalidInputError is raised for invalid initialization parameters."""
    pattern = re.escape("[token_counter] Input should be callable")
    with pytest.raises(InvalidInputError, match=pattern):
        PlainTextChunker(token_counter="Not a callable")


@pytest.mark.parametrize(
    "mode, max_tokens, max_sentences, expected_chunks",
    [("sentence", 512, 3, 9), ("token", 30, 100, 1), ("hybrid", 30, 3, 9)],
)
def test_all_modes_produce_chunks(
    chunker, mode, max_tokens, max_sentences, expected_chunks
):
    """Verify all chunking modes produce output with expected chunk counts and structure."""
    chunker.verbose = True
    chunks = chunker.chunk(
        ENGLISH_TEXT,
        mode=mode,
        max_tokens=max_tokens,
        max_sentences=max_sentences,
    )
    assert chunks, f"Expected chunks in {mode} mode but got empty list"
    assert (
        len(list(chunks)) == expected_chunks
    ), f"Expected {expected_chunks} chunks in {mode} mode, but got {len(list(chunks))}"

    # Verify the structure of the first chunk
    first_chunk = chunks[0]  # first_chunk is now a string
    assert isinstance(first_chunk, str)
    assert len(first_chunk) > 0  # Check length of the string


@pytest.mark.parametrize(
    "offset, expect_chunks",
    [
        (0, True),
        (3, True),
        (10, True),
        (100, False),  # More than total sentences
    ],
)
def test_offset_behavior(chunker, offset, expect_chunks):
    """Verify offset affects output and large offsets produce no chunks"""
    chunks = chunker.chunk(ENGLISH_TEXT, offset=offset)
    if expect_chunks:
        assert chunks, f"Should get chunks for offset={offset}"
        assert len(chunks[0]) > 0, "Chunk content should not be empty"
    else:
        assert not chunks, f"Should get no chunks for offset={offset}"


@pytest.mark.parametrize("mode", ["token", "hybrid"])
def test_token_counter_validation(mode):
    """Test that a MissingTokenCounterError is raised when a token_counter is missing for token/hybrid modes."""
    with pytest.raises(MissingTokenCounterError):
        PlainTextChunker().chunk("some text", mode=mode)


def test_long_sentence_truncation(chunker):
    """Test that a long sentence without punctuation is truncated correctly."""
    long_sentence = "word " * 100
    # Use max_tokens to trigger truncation for the single long sentence
    chunks = chunker.chunk(long_sentence, mode="token", max_tokens=30)

    assert len(chunks) == 1
    # The chunk should be truncated and have the continuation marker.
    assert len(chunks[0]) < len(long_sentence)
    assert chunks[0].endswith("...")


# --- Overlap Related Tests ---
def test_overlap_behavior(chunker):
    """Test that overlap produces multiple chunks and the overlap content is correct."""
    # Test case 1: Overlap with capitalized clause
    chunks = chunker.chunk(
        ENGLISH_TEXT,
        mode="sentence",
        max_sentences=3,
        overlap_percent=33,
    )
    assert len(chunks) > 1, "Overlap should produce multiple chunks"

    # Manually calculate the expected overlap to create a robust test
    first_chunk_content = chunks[0]
    clauses = chunker.clause_end_regex.split(first_chunk_content)

    overlap_num = round(len(clauses) * 0.33)
    expected_overlap_clause = clauses[-overlap_num:][0]

    # The logic adds '... ' if the clause doesn't start with a capital letter
    if not (
        expected_overlap_clause[0].isupper()
        or (len(expected_overlap_clause) > 1 and expected_overlap_clause[1].isupper())
    ):
        expected_overlap_string = f"... {expected_overlap_clause.lstrip()}"
    else:
        expected_overlap_string = expected_overlap_clause

    assert chunks[1].startswith(
        expected_overlap_string
    ), f"Expected second chunk to start with '{expected_overlap_string}', but it did not."

    # Test case 2: Overlap with non-capitalized clause
    text = "This is a first sentence, and this is a second part. This is the second sentence."
    chunks = chunker.chunk(text, mode="sentence", max_sentences=1, overlap_percent=50)
    assert len(chunks) > 1
    assert chunks[1].startswith("... and this is a second part.")

    # Test _get_overlap_clauses directly
    sentences = [
        "This is the first sentence.",
        "This is the second sentence, with a clause.",
        "This is the third sentence.",
    ]
    overlap = chunker._get_overlap_clauses(sentences, 50)
    assert isinstance(overlap, list)
    assert len(overlap) > 0


# --- Batch chunking Tests---
@pytest.mark.parametrize(
    "texts_input, expected_results_len",
    [
        # Successful run
        (["Hello. How are you?", "I am fine."], 2),
        # Edge cases
        ([], 0),
        (["First sentence.", "", "Second sentence."], 3),
    ],
)
def test_batch_processing_successful(
    chunker, texts_input, expected_results_len
):
    """Comprehensive test for batch processing successful runs and edge cases."""
    results = list(
        chunker.batch_chunk(
            texts_input,
            mode="sentence",
            max_sentences=100,
            _document_context=True,
        )
    )
    assert len(results) == expected_results_len
    if texts_input and results and results[0] and len(results[0]) > 0:
        # Check structure of the first result of the first text
        assert isinstance(results[0][0], str)  # Check if it's a string

    if texts_input == ["First sentence.", "", "Second sentence."]:
        assert "First sentence." in results[0][0]
        assert results[1] == []
        assert "Second sentence." in results[2][0]


def test_batch_processing_input_validation(chunker):
    """Test batch processing error handling on invalid input"""
    # Test that InvalidInputError is raised for input text isnt an iterable object
    texts_input = "this is a string, not a list"

    with pytest.raises(
        InvalidInputError, match="The 'texts' parameter must be an iterable of strings"
    ):
        list(chunker.batch_chunk(texts_input))

    #Test that InvalidInputError is raised for invalid n_jobs values
    with pytest.raises(
        InvalidInputError,
        match="The 'n_jobs' parameter must be an integer greater than or equal to 1, or None",
    ):
        list(chunker.batch_chunk(["some text"], n_jobs=-1))


def test_batch_chunk_error_handling_on_task(chunker):
    """Test the on_errors parameter in batch_chunk."""

    def failing_token_counter(text: str) -> int:
        if "fail" in text:
            raise ValueError("Intentional failure")
        return len(text.split())

    chunker.token_counter = failing_token_counter

    texts = ["This is ok.", "This will fail.", "This will not be processed."]

    # Test on_errors = 'raise'
    with pytest.raises(CallbackExecutionError, match="Token counter failed while processing text starting with:"):
        list(chunker.batch_chunk(texts, mode="token", on_errors="raise"))

    # Test on_errors = 'ignore'
    results = list(chunker.batch_chunk(texts, mode="token", on_errors="ignore"))
    assert len(results) == 2
    assert "This is ok." in results[0]
    assert "This will not be processed." in results[1]

    # Test on_errors = 'break'
    results = list(chunker.batch_chunk(texts, mode="token", on_errors="break"))
    assert len(results) == 1
    assert "This is ok." in results[0]


@pytest.mark.parametrize(
    "separator, texts, expected_output",
    [
        # Case 1: Simple string separator
        ("---", ["First sentence.", "Second sentence."], ["First sentence.", "---", "Second sentence.", "---"]),
        # Case 2: None as separator
        (None, ["First sentence.", "Second sentence."], ["First sentence.", None, "Second sentence.", None]),
    ],
)
def test_batch_chunk_with_separator(chunker, separator, texts, expected_output):
    """Test the separator functionality in batch_chunk with real chunking."""
    result = list(chunker.batch_chunk(texts, separator=separator))

    assert result == expected_output
