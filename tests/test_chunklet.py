import pytest
from typing import List
from chunklet import Chunklet

# --- Sample Texts ---
english_sample_text = """
    She loves cooking. He studies AI. "You are a Dr." she said. The weather is great.
    We play chess. Books are fun.
    The Playlist contains:
        - two videos
        - one music
    Robots are learning.
    It's raining. Let's code. Mars is red. Sr. sleep is rare.
    Consider item 1. This is a test.
    The year is 2025. This is a good year.
"""

acronym_text = "The section is N. A. S. A. related. Consider S.1 to be an important point. Let's move on."

texts_with_langs = {
    "en": "Hello. How are you? I am fine.",
    "fr": "Bonjour. Comment allez-vous ? Je vais bien.",
    "es": "Hola. ¿Cómo estás? Estoy bien.",
    "de": "Das ist ein deutscher Satz. Hier ist noch ein Satz. Und noch einer.",
    "ht": "Bonjou. Kijan ou ye? Mwen byen. Sa a se yon tèks an kreyòl ayisyen. Li gen plizyè fraz. Nou kontan wè ou."
}

# --- Helper Functions ---

def simple_token_counter(sentence: str) -> int:
    """A simple token counter that counts words."""
    return len(sentence.split())

def has_word_overlap(chunk1: str, chunk2: str, overlap_length: int = 2) -> bool:
    """
    Check if there is an overlap of at least `overlap_length` consecutive words
    between chunk1 and chunk2 anywhere inside the strings.
    """
    words1 = chunk1.split()
    overlaps = [' '.join(words1[i:i+overlap_length]) for i in range(len(words1) - overlap_length + 1)]
    return any(overlap in chunk2 for overlap in overlaps)

# --- Fixtures ---

@pytest.fixture(scope="module")
def chunklet_instance():
    """Provides a fresh Chunklet instance with default token_counter."""
    return Chunklet()

@pytest.fixture(scope="module")
def token_counter_chunklet_instance():
    """Provides Chunklet with simple_token_counter for token-based tests."""
    return Chunklet(token_counter=simple_token_counter)

# --- Tests ---

def test_sentence_mode_overlap(chunklet_instance):
    """Tests if sentence mode creates chunks with expected overlap."""
    max_sentences = 3
    overlap_percent = 33
    chunks = chunklet_instance.chunk(
        english_sample_text,
        mode="sentence",
        max_sentences=max_sentences,
        overlap_percent=overlap_percent
    )

    assert len(chunks) > 1, "Expected more than one chunk for the English sample text."
    if len(chunks) > 1:
        assert has_word_overlap(chunks[0], chunks[1], overlap_length=2), "Overlap not found between first two chunks."

def test_token_mode_overlap(token_counter_chunklet_instance):
    """Tests if token mode correctly handles token limits and overlap."""
    max_tokens = 25
    overlap_percent = 20

    chunks = token_counter_chunklet_instance.chunk(
        english_sample_text,
        mode="token",
        max_tokens=max_tokens,
        overlap_percent=overlap_percent
    )

    assert len(chunks) > 1, "Expected more than one chunk for the English sample text."
    for chunk in chunks:
        assert simple_token_counter(chunk) <= max_tokens, f"Chunk exceeds max_tokens: {chunk}"

    if len(chunks) > 1:
        assert has_word_overlap(chunks[0], chunks[1]), "Overlap not found between chunks."

def test_acronym_handling(chunklet_instance):
    """Tests that the chunker correctly handles acronyms like N.A.S.A. and initials."""
    chunks = chunklet_instance.chunk(acronym_text, mode="sentence", max_sentences=1)
    assert "N. A. S. A." in chunks[0]

def test_multilingual_auto_detection(chunklet_instance):
    """Tests chunking with mixed languages and auto-detection."""
    for lang, text in texts_with_langs.items():
        chunks = chunklet_instance.chunk(text, mode="sentence", max_sentences=1, lang="auto")
        assert len(chunks) > 0, f"Expected chunks for {lang} text, but got none."
        # Further assertions can be added here if specific chunk content is expected

def test_chunk_caching_behavior():
    """Tests that caching returns consistent results and is actually used."""
    chunker = Chunklet(token_counter=simple_token_counter, use_cache=True)
    text = "This is a test. This is only a test. Testing caching behavior."

    # First call, should compute and cache
    result1 = chunker.chunk(text, mode="hybrid", max_tokens=10, max_sentences=2, overlap_percent=30)

    # Second call, should hit cache and return quickly (same parameters)
    result2 = chunker.chunk(text, mode="hybrid", max_tokens=10, max_sentences=2, overlap_percent=30)

    assert result1 == result2, "Cached result differs from original result."

    # Changing a parameter invalidates cache, should recompute
    result3 = chunker.chunk(text, mode="hybrid", max_tokens=5, max_sentences=2, overlap_percent=30)
    assert result3 != result1, "Cache was not invalidated on parameter change."

def test_batch_chunk_method(token_counter_chunklet_instance):
    """Tests the batch_chunk method for correct chunking and parallel processing."""
    texts = [
        "This is the first sentence. This is the second sentence.",
        "Another text for batch processing. It has multiple sentences.",
        "Short text."
    ]
    results = token_counter_chunklet_instance.batch_chunk(
        texts,
        mode="sentence",
        max_sentences=1,
        overlap_percent=0,
    )

    assert len(results) == len(texts), "Expected results for each input text."
    assert len(results[0]) == 2
    assert len(results[1]) == 2
    assert len(results[2]) == 1
