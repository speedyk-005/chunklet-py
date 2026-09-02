import pytest

from chunklet.sentence_splitter import SentenceSplitter

# --- Fixture ---


@pytest.fixture
def splitter():
    """Provides a configured SentenceSplitter instance"""
    return SentenceSplitter(lang="en")


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
