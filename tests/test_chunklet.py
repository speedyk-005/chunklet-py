import pytest
from chunklet import Chunklet

# --- Constants ---

ENGLISH_TEXT = (
    "She loves cooking. He studies AI. \"You are a Dr.\" she said. The weather is great. "
    "We play chess. Books are fun. The Playlist contains: two videos, one music. "
    "Robots are learning. It's raining. Let's code. Mars is red. Sr. sleep is rare. "
    "Consider item 1. This is a test. The year is 2025. This is a good year."
)

MULTILINGUAL_TEXTS = [
    "Hello. How are you? I am fine.",        # English
    "Bonjour. Comment allez-vous? Je vais bien.",  # French
    "Hola. ¿Cómo estás? Estoy bien.",        # Spanish
    "Das ist ein Satz. Hier ist noch ein Satz. Und noch einer.",  # German
]

ACRONYMS_TEXT = "The section is N. A. S. A. related. Consider S.1 to be important. Let's move on."
 
UNSUPPORTED_TEXT = "Això és una prova. Això és una altra prova."

# --- Fixtures ---
@pytest.fixture
def chunker():
    """Provides a configured Chunklet instance for testing"""
    def simple_token_counter(text: str) -> int:
        return len(text.split())
    return Chunklet(token_counter=simple_token_counter)

# --- Core Tests ---

@pytest.mark.parametrize("mode", ["sentence", "token", "hybrid"])
def test_all_modes_produce_chunks(chunker, mode):
    """Verify all chunking modes produce output"""
    chunks = chunker.chunk(ENGLISH_TEXT, mode=mode)
    assert chunks, f"Expected chunks in {mode} mode but got empty list"
    assert all(isinstance(c, str) for c in chunks), "All chunks should be strings"

def test_acronyms_preserved(chunker):
    """Verify special patterns remain intact"""
    chunks = chunker.chunk(ACRONYMS_TEXT)
    joined = " ".join(chunks)
    assert "N. A. S. A." in joined, "Acronyms should be preserved"

def test_batch_processing_completes(chunker):
    """Test batch processing runs without errors"""
    results = chunker.batch_chunk(MULTILINGUAL_TEXTS)
    assert len(results) == len(MULTILINGUAL_TEXTS), "Should process all inputs"

@pytest.mark.parametrize("offset, expect_chunks", [
    (0, True),
    (3, True),
    (10, True),
    (100, False),  # More than total sentences
])
def test_offset_behavior(chunker, offset, expect_chunks):
    """Verify offset affects output and large offsets produce no chunks"""
    chunks = chunker.chunk(ENGLISH_TEXT, offset=offset)
    if expect_chunks:
        assert chunks, f"Should get chunks for offset={offset}"
    else:
        assert not chunks, f"Should get no chunks for offset={offset}"

def test_preview_works(chunker):
    """Verify preview produces output"""
    sentences = chunker.preview_sentences(ENGLISH_TEXT)
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
    chunks = chunker.chunk(UNSUPPORTED_TEXT)
    assert chunks, "Fallback chunking should produce output"
    # Both sentences should be in the single chunk (fallback expected to produce one chunk)
    assert "Això és una prova." in chunks[0]
    assert "Això és una altra prova." in chunks[0]

# --- Overlap Related Tests ---
@pytest.mark.parametrize("mode, mock_overlap_text, chunk_kwargs", [
    ("sentence", ["... one music."], dict(max_sentences=7, overlap_percent=20)),
    ("token", ["... a test."], dict(max_tokens=20, overlap_percent=10)),
])
def test_overlap_behavior(mocker, chunker, mode, mock_overlap_text, chunk_kwargs):
    """Test overlap logic and handling of lowercase overlap."""
    mock_get_overlap = mocker.patch('chunklet.core.Chunklet._get_overlap_clauses')
    mock_get_overlap.return_value = mock_overlap_text
    chunks = chunker.chunk(ENGLISH_TEXT, mode=mode, **chunk_kwargs)
    assert len(chunks) > 1, "Overlap should produce multiple chunks"
    assert any(ov_text in chunks[1] for ov_text in mock_overlap_text), "Overlap clause missing in chunk"

def test_overlap_not_empty(chunker):
    """Verify overlap mode produces some content"""
    chunks = chunker.chunk(
        ENGLISH_TEXT,
        mode="sentence",
        max_sentences=3,
        overlap_percent=20
    )
    if len(chunks) > 1:
        assert chunks[0] and chunks[1], "Chunks should contain content"

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