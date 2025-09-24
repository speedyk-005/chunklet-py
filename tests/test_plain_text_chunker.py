import pytest
import re
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


@pytest.mark.parametrize(
    "texts_input, expected_results_len",
    [
        # Successful run
        (MULTILINGUAL_TEXTS, len(MULTILINGUAL_TEXTS)),
        # Edge cases from test_batch_chunk_various_inputs
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
    with pytest.raises(TextProcessingError, match="Token counter failed while processing text starting with:"):
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


# --- Custom Splitter Tests ---

def test_custom_splitter_usage():
    """Test that the chunker can work a custom splitter without errors."""

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


@pytest.mark.parametrize(
    "splitter_name, callback_func, expected_match",
    [
        (
            "InvalidListSplitter",
            lambda text: "This is a single string.",  # Returns str, not list[str]
            "Custom splitter 'InvalidListSplitter' callback returned an invalid type.",
        ),
        (
            "ListNonStringSplitter",
            lambda text: ["hello", 123, "world"],  # List contains non-strings
            "Custom splitter 'ListNonStringSplitter' callback returned an invalid type. ",
        ),
        (
            "FailingSplitter",
            lambda text: (_ for _ in ()).throw(ValueError("Intentional failure in custom splitter.")),
            "Custom splitter 'FailingSplitter' callback failed for text starting with: 'Some text....'.",
        ),
    ],
)
def test_custom_splitter_validation_scenarios(
    chunker, splitter_name, callback_func, expected_match
):
    """Test various custom splitter validation scenarios."""
    custom_splitters = [
        {
            "name": splitter_name,
            "languages": "en",
            "callback": callback_func,
        }
    ]
    chunker_with_custom_splitter = PlainTextChunker(custom_splitters=custom_splitters)

    with pytest.raises(TextProcessingError, match=re.escape(expected_match)):
        chunker_with_custom_splitter.chunk("Some text.", lang="en")