import pytest
from typing import List
from unittest.mock import patch
from chunklet import (
    PlainTextChunker,
    TextProcessingError,
    InvalidInputError,
    MissingTokenCounterError,
)
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

MULTILINGUAL_TEXTS = [
    "Hello. How are you? I am fine.",  # English
    "Bonjour. Comment allez-vous? Je vais bien.",  # French
    "Hola. ¿Cómo estás? Estoy bien.",  # Spanish
    "Das ist ein Satz. Hier ist noch ein Satz. Und noch einer.",  # German
    "Bonjou tout moun! Non pa mwen se Bob.",  # Haitian Creole
]

UNSUPPORTED_TEXT = "Goeie môre. Hoe gaan dit? Dit gaan goed met my."  # Afrikaans


# --- Fixtures ---
@pytest.fixture
def chunker():
    """Provides a configured Chunklet instance for testing"""

    def simple_token_counter(text: str) -> int:
        return len(text.split())

    return PlainTextChunker(token_counter=simple_token_counter)


# --- Core Tests ---
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


def test_preview_works(chunker):
    """Verify preview_sentences produces a list of sentences."""
    sentences, _ = chunker.preview_sentences(ENGLISH_TEXT)
    assert len(sentences) == 19, "Should get sentence preview"


# --- Token Counter Validation ---
@pytest.mark.parametrize("mode", ["token", "hybrid"])
def test_token_counter_validation(mode):
    """Test that a MissingTokenCounterError is raised when a token_counter is missing for token/hybrid modes."""
    with pytest.raises(MissingTokenCounterError):
        PlainTextChunker().chunk("some text", mode=mode)


# --- Fallback Splitter Test ---
def test_fallback_splitter(chunker):
    """Test fallback splitter on unsupported language text and low confidence language detection."""
    # Should fallback to the regex splitter
    chunks = chunker.chunk(UNSUPPORTED_TEXT, max_sentences=1, mode="sentence")
    assert len(chunks) == 3, "Expected 3 chunks for the unsupported language text"
    assert chunks[0] == "Goeie môre."
    assert chunks[1] == "Hoe gaan dit?"
    assert chunks[2] == "Dit gaan goed met my."

    # Test low confidence language detection
    with patch(
        "chunklet.plain_text_chunker.detect_text_language",
        return_value=("en", 0.5),
    ):
        sentences, warnings = chunker._split_by_sentence("This is a test.", "auto")
        assert "Low confidence in language detected" in "".join(warnings)


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


# --- Cache Tests ---
def test_non_cached_chunking(chunker):
    """Test chunking with cache disabled."""
    non_cached_chunker = PlainTextChunker(
        use_cache=False, token_counter=chunker.token_counter
    )
    chunks = non_cached_chunker.chunk(ENGLISH_TEXT)
    assert chunks  # chunks is List[str], so this is fine
    assert isinstance(chunks[0], str)  # Add a check for string type


# --- Batch Processing Tests ---
@pytest.mark.parametrize(
    "texts_input, n_jobs, mode, max_sentences, expected_exception, expected_match, expected_results_len, failing_text",
    [
        # Successful run
        (
            MULTILINGUAL_TEXTS,
            None,
            "sentence",
            100,
            None,
            None,
            len(MULTILINGUAL_TEXTS),
            None,
        ),
        # Edge cases from test_batch_chunk_various_inputs
        ([], None, "sentence", 1, None, None, 0, None),
        (
            "this is a string, not a list",
            None,
            "sentence",
            1,
            InvalidInputError,
            "The 'texts' parameter must be an iterable of strings",
            None,
            None,
        ),
        (
            ["First sentence.", "", "Second sentence."],
            None,
            "sentence",
            1,
            None,
            None,
            3,
            None,
        ),
        # Error handling from test_batch_chunk_n_jobs_1_with_error
        (
            [
                "This is ok.",
                "This one will fail.",
                "This will not be processed.",
            ],
            1,
            "token",
            100,
            None,
            None,
            1,
            "fail",
        ),
    ],
)
def test_batch_processing(
    chunker,
    texts_input,
    n_jobs,
    mode,
    max_sentences,
    expected_exception,
    expected_match,
    expected_results_len,
    failing_text,
):
    """Comprehensive test for batch processing."""

    if failing_text:

        def failing_token_counter(text: str) -> int:
            if failing_text in text:
                raise ValueError("Intentional failure")
            return len(text.split())

        chunker.token_counter = failing_token_counter

    if expected_exception:
        with pytest.raises(expected_exception, match=expected_match):
            list(
                chunker.batch_chunk(
                    texts_input,
                    n_jobs=n_jobs,
                    mode=mode,
                    max_sentences=max_sentences,
                )
            )
    else:
        results = list(
            chunker.batch_chunk(
                texts_input,
                n_jobs=n_jobs,
                mode=mode,
                max_sentences=max_sentences,
            )
        )
        assert len(results) == expected_results_len
        if texts_input and results and results[0]:
            # Check structure of the first result of the first text
            assert isinstance(results[0][0], str)  # Check if it's a string

        if texts_input == ["First sentence.", "", "Second sentence."]:
            assert "First sentence." in results[0][0]
            assert results[1] == []
            assert "Second sentence." in results[2][0]
        if failing_text:
            assert results[0][0] == "This is ok."


def test_error_on_token_counter_failure():
    """Test that TextProcessingError is raised when the token_counter fails."""

    def failing_token_counter(text: str) -> int:
        raise Exception("Token counter failed intentionally")

    chunker = PlainTextChunker(token_counter=failing_token_counter)
    with pytest.raises(
        TextProcessingError,
        match="Token counter failed while processing text starting with:",
    ):
        chunker.chunk("some text", mode="token")


@pytest.mark.parametrize(
    "n_jobs_value",
    [
        0,
        -1,
    ],
)
def test_batch_chunk_invalid_n_jobs(chunker, n_jobs_value):
    """Test that InvalidInputError is raised for invalid n_jobs values."""
    with pytest.raises(
        InvalidInputError,
        match="The 'n_jobs' parameter must be an integer greater than or equal to 1, or None",
    ):
        list(chunker.batch_chunk(["some text"], n_jobs=n_jobs_value))


def test_custom_splitter_basic_usage():
    """Test basic usage of a custom splitter."""

    # Define a simple custom splitter that splits by 'X'
    def custom_x_splitter(text: str) -> List[str]:
        return [s.strip() for s in text.split("X") if s.strip()]

    custom_splitters = [
        {
            "name": "XSplitter",
            "languages": "en",
            "callback": custom_x_splitter,
        }
    ]

    # Initialize Chunklet with the custom splitter
    chunker = PlainTextChunker(custom_splitters=custom_splitters)

    text = "ThisXisXaXtestXstring."
    expected_sentences = ["This", "is", "a", "test", "string."]

    sentences, _ = chunker.preview_sentences(text, lang="en")

    assert sentences == expected_sentences


def test_init_validation_error():
    """Test that InvalidInputError is raised for invalid initialization parameters."""
    with pytest.raises(
        InvalidInputError, match="\[token_counter\] Input should be callable"
    ):
        PlainTextChunker(token_counter="Not a callable")
