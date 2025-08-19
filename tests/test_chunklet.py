import pytest
from chunklet import Chunklet

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
]

ACRONYMS_TEXT = (
    "The section is N. A. S. A. related. Consider S.1.2 to be important. Let's move on."
)
UNSUPPORTED_TEXT = "Bonjour tout moun! Non pa mwen se Bob."  # Haitian Creole


# --- Fixtures ---
@pytest.fixture
def chunker():
    """Provides a configured Chunklet instance for testing"""

    def simple_token_counter(text: str) -> int:
        return len(text.split())

    return Chunklet(token_counter=simple_token_counter)


# --- Core Tests ---
@pytest.mark.parametrize(
    "mode, max_tokens, max_sentences, expected_chunks",
    [("sentence", 512, 3, 9), ("token", 30, 100, 3), ("hybrid", 30, 3, 9)],
)
def test_all_modes_produce_chunks(
    chunker, mode, max_tokens, max_sentences, expected_chunks
):
    """Verify all chunking modes produce output with expected chunk counts."""
    chunks = chunker.chunk(
        ENGLISH_TEXT, mode=mode, max_tokens=max_tokens, max_sentences=max_sentences
    )
    assert chunks, f"Expected chunks in {mode} mode but got empty list"
    assert (
        len(chunks) == expected_chunks
    ), f"Expected {expected_chunks} chunks in {mode} mode, but got {len(chunks)}"


def test_acronyms_preserved(chunker):
    """Verify special patterns remain intact"""
    chunks = chunker.chunk(ACRONYMS_TEXT, mode="sentence", max_sentences=1)
    assert len(chunks) == 3, "Expected 3 chunks"
    assert "N. A. S. A. related" in chunks[0], "Acronym should be in the first chunk"
    assert (
        "Consider S.1.2 to be important" in chunks[1]
    ), "S.1 should be in the second chunk"


def test_batch_processing_completes(chunker):
    """Test batch processing runs without errors"""
    results = chunker.batch_chunk(MULTILINGUAL_TEXTS)
    assert len(results) == len(MULTILINGUAL_TEXTS), "Should process all inputs"


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
    else:
        assert not chunks, f"Should get no chunks for offset={offset}"


def test_preview_works(chunker):
    """Verify preview produces output"""
    sentences, _ = chunker.preview_sentences(ENGLISH_TEXT)
    assert sentences, "Should get sentence preview"


# --- Token Counter Validation ---
@pytest.mark.parametrize("mode", ["token", "hybrid"])
def test_token_counter_validation(mode):
    """Test that a ValueError is raised when a token_counter is missing for token/hybrid modes."""
    with pytest.raises(ValueError, match="token_counter is required"):
        Chunklet().chunk("some text", mode=mode)


# --- Fallback Splitter Test ---
def test_fallback_splitter(chunker):
    """Test fallback splitter on unsupported language text (single string input)."""
    chunks = chunker.chunk(UNSUPPORTED_TEXT, max_sentences=1, mode="sentence")
    assert len(chunks) == 2, "Expected 2 chunks for the unsupported language text"
    assert "Bonjour tout moun!" in chunks[0]
    assert "Non pa mwen se Bob." in chunks[1]


# --- Overlap Related Tests ---
def test_overlap_behavior(chunker):
    """Test that overlap produces multiple chunks and the overlap content is correct."""
    chunks = chunker.chunk(
        ENGLISH_TEXT,
        mode="sentence",
        max_sentences=3,
        overlap_percent=33,
    )
    assert len(chunks) > 1, "Overlap should produce multiple chunks"

    # Manually calculate the expected overlap to create a robust test
    first_chunk_text = 'She loves cooking. He studies AI. "You are a Dr.", she said. '
    clauses = chunker.clause_end_regex.split(first_chunk_text)
    # Expected clauses: ['She loves cooking. He studies AI. "You are a Dr.",', ' she said. ']

    overlap_num = round(len(clauses) * 0.33)
    expected_overlap_clause = clauses[-overlap_num:][0]

    # The logic adds '... ' if the clause doesn't start with a capital letter
    expected_overlap_string = f"... {expected_overlap_clause.lstrip()}"

    assert chunks[1].startswith(
        expected_overlap_string
    ), f"Expected second chunk to start with '{expected_overlap_string}', but it did not."


# --- Cache Tests ---
def test_non_cached_chunking(chunker):
    """Test chunking with cache disabled."""
    non_cached_chunker = Chunklet(use_cache=False, token_counter=chunker.token_counter)
    chunks = non_cached_chunker.chunk(ENGLISH_TEXT)
    assert chunks


# --- Batch Processing Edge Cases ---
def test_batch_chunk_edge_cases(chunker):
    """Test batch_chunk with empty list and invalid n_jobs raises errors."""
    assert chunker.batch_chunk([]) == []
    with pytest.raises(ValueError, match="n_jobs must be >= 1 or None"):
        chunker.batch_chunk(["text"], n_jobs=0)
    with pytest.raises(ValueError, match="n_jobs must be >= 1 or None"):
        chunker.batch_chunk(["text"], n_jobs=-1)
