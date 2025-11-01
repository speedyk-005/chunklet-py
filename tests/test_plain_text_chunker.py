import re
import pytest
from more_itertools import split_at
from loguru import logger
from chunklet.plain_text_chunker import PlainTextChunker
from chunklet.exceptions import (
    InvalidInputError,
    CallbackError,
    MissingTokenCounterError,
)

# Silent logging
logger.remove()


# --- Constants ---

# Sentinel to serve as boundary between the groups of chunks for each text
SEPARATOR_SENTINEL = object()

TEXT = """
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
        if "fail" in text:
            raise ValueError("Intentional failure")
        return len(text.split())

    return PlainTextChunker(token_counter=simple_token_counter)


# --- Core Tests ---
def test_init_validation_error():
    """Test that InvalidInputError is raised for invalid initialization parameters."""
    with pytest.raises(
        InvalidInputError, match=re.escape("(token_counter) Input should be callable.")
    ):
        PlainTextChunker(token_counter="Not a callable")


@pytest.mark.parametrize(
    "mode, max_tokens, max_sentences, expected_chunks",
    [("sentence", 512, 3, 7), ("token", 30, 100, 3), ("hybrid", 30, 3, 7)],
)
def test_all_modes_produce_chunks(
    chunker, mode, max_tokens, max_sentences, expected_chunks
):
    """Verify all chunking modes produce output with expected chunk counts and structure."""
    chunker.verbose = True
    chunks = chunker.chunk(
        TEXT,
        mode=mode,
        max_tokens=max_tokens,
        max_sentences=max_sentences,
    )
    assert chunks, f"Expected chunks in {mode} mode but got empty list"
    assert (
        len(chunks) == expected_chunks
    ), f"Expected {expected_chunks} chunks in {mode} mode, but got {len(chunks)}"

    # Verify the structure of the first chunk
    first_chunk = chunks[0]
    assert hasattr(first_chunk, "content")
    assert hasattr(first_chunk, "metadata")

    assert len(first_chunk.content) > 0

    assert first_chunk.metadata.chunk_num == 1
    assert hasattr(first_chunk.metadata, "span")


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
    chunks = chunker.chunk(TEXT, offset=offset)

    if expect_chunks:
        assert len(chunks) >= 1, f"Should get chunks for offset={offset}"
        assert len(chunks[0].content) > 0, "Chunk content should not be empty"
    else:
        assert not chunks, f"Should get no chunks for offset={offset}"


@pytest.mark.parametrize("mode", ["token", "hybrid"])
def test_token_counter_validation(mode):
    """Test that a MissingTokenCounterError is raised when a token_counter is missing for token/hybrid modes."""
    with pytest.raises(MissingTokenCounterError):
        new_chunker = PlainTextChunker()

        # Consume the generator to trigger the error
        new_chunker.chunk("some text", mode=mode)


def test_long_sentence_truncation(chunker):
    """Test that a long sentence without punctuation is #truncated correctly."""
    long_sentence = "word " * 100
    chunks = chunker.chunk(long_sentence, mode="token", max_tokens=30)

    assert len(chunks) >= 1, "Expected at least one chunk, but got None"
    assert chunks[0].content.endswith(
        "..."
    ), f"Chunk '{chunks[0].content}' does not end with '...'"


# --- Overlap Related Tests ---
def test_overlap_behavior(chunker):
    """Test that overlap produces multiple chunks and the overlap content is correct."""
    # Test case 1: Overlap with capitalized clause
    chunks = chunker.chunk(
        TEXT,
        mode="sentence",
        max_sentences=3,
        overlap_percent=33,
    )
    assert len(chunks) > 1, "Overlap should produce multiple chunks"

    # Manually calculate the expected overlap to create a robust test
    first_chunk_content = chunks[0].content
    clauses = chunker.clause_end_regex.split(first_chunk_content)

    overlap_num = round(len(clauses) * 0.33)
    expected_overlap_clause = clauses[-overlap_num:][0]

    # The logic adds '... ' if the clause doesn't start with a capital letter
    assert (
        re.match(
            rf"(?:\.\.\. )?{re.escape(expected_overlap_clause)}", chunks[1].content
        )
        is not None
    ), f"Expected second chunk to start with '{expected_overlap_clause}' (with optional '... '), but it did not."


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
def test_batch_processing_successful(chunker, texts_input, expected_results_len):
    """Comprehensive test for batch processing successful runs and edge cases."""
    results = list(
        chunker.batch_chunk(
            texts_input,
            mode="sentence",
            max_sentences=100,
            separator=SEPARATOR_SENTINEL,
        )
    )

    # Minus by 1 to removed count for the empty [] that split_at like to put at the end
    assert (
        len(list(split_at(results, lambda x: x is SEPARATOR_SENTINEL))) - 1
        == expected_results_len
    )


def test_batch_processing_input_validation(chunker):
    """Test batch processing error handling on invalid input"""
    # Test that InvalidInputError is raised for input that is an iterable, but contains wrong types
    texts_input_int = [1, 2, 3]  # Use list[int] here

    with pytest.raises(
        InvalidInputError, match=re.escape("Input should be a valid string.")
    ):
        list(chunker.batch_chunk(texts_input_int))

    # Test n_jobs with an invalid type
    with pytest.raises(
        InvalidInputError,
        match=re.escape("(n_jobs) Input should be greater than or equal to 1."),
    ):
        list(chunker.batch_chunk(["some text"], n_jobs=-1))


def test_batch_chunk_error_handling_on_task(chunker):
    """Test the on_errors parameter in batch_chunk."""

    texts = ["This is ok.", "This will fail.", "This will not be processed."]

    # Test on_errors = 'raise'
    with pytest.raises(
        CallbackError,
        match="Token counter failed while processing text starting with:",
    ):
        list(chunker.batch_chunk(texts, mode="token", on_errors="raise"))

    # Test on_errors = 'skip'
    results = chunker.batch_chunk(
        texts,
        mode="token",
        on_errors="skip",
        separator=SEPARATOR_SENTINEL,
    )

    # Split the flattened stream into groups
    all_chunk_groups = list(split_at(results, lambda x: x is SEPARATOR_SENTINEL))

    assert len(all_chunk_groups) - 1 == 2  # Expect 2 successful documents
    assert "This is ok." in all_chunk_groups[0][0].content
    assert "This will not be processed." in all_chunk_groups[1][0].content

    # Test on_errors = 'break'
    results = chunker.batch_chunk(
        texts,
        mode="token",
        on_errors="break",
        separator=SEPARATOR_SENTINEL,
    )

    # Split the flattened stream into groups
    all_chunk_groups = list(split_at(results, lambda x: x is SEPARATOR_SENTINEL))
    assert len(all_chunk_groups) - 1 == 1  # Expect 1 successful document
    assert "This is ok." in all_chunk_groups[0][0].content
