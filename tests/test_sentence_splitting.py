import pytest

from chunklet.sentence_splitter import SentenceSplitter
from chunklet.sentence_splitter._universal_splitter import UniversalSplitter

# --- Fixture ---


@pytest.fixture
def splitter():
    """Provides a configured SentenceSplitter instance"""
    return SentenceSplitter(lang="en")


@pytest.fixture
def universal_splitter():
    """Provides a UniversalSplitter instance for fallback testing."""
    return UniversalSplitter()


# --- Multilingual Splitting Tests ---


@pytest.mark.parametrize(
    "text, expected_sentences",
    [
        (
            "Hello. How are you? I am fine.",
            ["Hello.", "How are you?", "I am fine."],
        ),  # English
        (
            "Bonjou tout moun! Non pa mwen se Bob.",
            ["Bonjou tout moun!", "Non pa mwen se Bob."],
        ),  # Haitian Creole
        (
            "হ্যালো। আপনি কেমন আছেন? আমি ভালো আছি।",
            ["হ্যালো।", "আপনি কেমন আছেন?", "আমি ভালো আছি।"],
        ),  # Bengali
        (
            "नमस्ते। आप कैसे हैं? मैं ठीक हूँ।",
            ["नमस्ते।", "आप कैसे हैं?", "मैं ठीक हूँ।"],  # Hindi
        ),
    ],
)
def test_multilingual_splitting(splitter, text, expected_sentences):
    """Test sentence splitting for various languages but not limited to."""
    sentences = splitter.split_text(text)
    assert sentences == expected_sentences


@pytest.mark.parametrize(
    "text, lang",
    [
        ("Hello world. How are you?", "xh"),  # Xhosa
        ("Sawubona Mhlaba. Unjani?", "zu"),  # Zulu
    ],
)
def test_unsupported_language_fallback(text, lang):
    """Test fallback to universal regex splitter for unsupported languages."""
    splitter = SentenceSplitter(lang=lang)
    sentences = splitter.split_text(text)
    assert len(sentences) >= 1


@pytest.mark.parametrize(
    "lang",
    [
        "en",  # yasbd
        "ko",  # yasbd
        "bn",  # indicnlp
        "ca",  # sentencex
    ],
)
def test_special_handler_exists(splitter, lang):
    """Each library should return a non-None handler that produces non-empty output."""
    handler = splitter._get_lang_handler(lang, verbose=False)
    assert handler is not None, f"No handler for language: {lang}"

    result = handler("Hello world. This is a test.")
    assert result, f"Handler for '{lang}' returned empty result"


@pytest.mark.parametrize(
    "text, expected_sentences",
    [
        # CJK with mixed punctuation
        (
            "这是第一句。这是第二句！这是第三句？",
            ["这是第一句。", "这是第二句！", "这是第三句？"],
        ),
        # Abbreviations must NOT split
        (
            "Dr. Smith said hi. He left.",
            ["Dr. Smith said hi.", "He left."],
        ),
        (
            "The U.S.A. is great. We love it.",
            ["The U.S.A. is great.", "We love it."],
        ),
        # Numbers must NOT split mid-value
        (
            "The price is $3.14. It weighs 123.45 kg.",
            ["The price is $3.14.", "It weighs 123.45 kg."],
        ),
        # Numbered lists
        (
            "Item 1. Item 2. Item 3.",
            ["Item 1.", "Item 2.", "Item 3."],
        ),
        # Quotes and parentheses are preserved
        (
            'She said "Hello there." Then she left.',
            ['She said "Hello there." Then she left.'],
        ),
        (
            "Paris (France) is nice. It is cold.",
            ["Paris (France) is nice.", "It is cold."],
        ),
        # Email / URL preserved
        (
            "Email me at pierrot1234@gmail.com please.",
            ["Email me at pierrot1234@gmail.com please."],
        ),
        # Newlines split
        (
            "First line.\nSecond line.\nThird line.",
            ["First line.", "Second line.", "Third line."],
        ),
    ],
)
def test_universal_splitter_basic(universal_splitter, text, expected_sentences):
    """text that UniversalSplitter handles Latin, CJK, abbreviations, numbers, quotes."""
    assert universal_splitter.split(text) == expected_sentences
