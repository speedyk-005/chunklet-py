import re
import pytest
from chunklet.sentence_splitter import SentenceSplitter, CustomSplitterRegistry
from chunklet import CallbackError

# --- Fixture ---


@pytest.fixture
def splitter():
    """Provides a configured SentenceSplitter instance"""
    return SentenceSplitter()


@pytest.fixture
def registry():
    """Provides aCustomSplitterRegistry instance"""
    return CustomSplitterRegistry()


# --- Multilingual Splitting Tests ---


@pytest.mark.parametrize(
    "text, expected_sentences",
    [
        (
            "Hello. How are you? I am fine.",
            ["Hello.", "How are you?", "I am fine."],
        ),  # English
        (
            "Bonjour. Comment allez-vous? Je vais bien.",
            ["Bonjour.", "Comment allez-vous?", "Je vais bien."],
        ),  # French
        (
            "Hola. ¿Cómo estás? Estoy bien.",
            ["Hola.", "¿Cómo estás?", "Estoy bien."],
        ),  # Spanish
        (
            "Das ist ein Satz. Hier ist noch ein Satz. Und noch einer.",
            ["Das ist ein Satz.", "Hier ist noch ein Satz.", "Und noch einer."],
        ),  # German
        ("नमस्ते। आप कैसे हैं? मैं ठीक हूँ।", ["नमस्ते।", "आप कैसे हैं?", "मैं ठीक हूँ।"]),  # Hindi
    ],
)
def test_multilingual_splitting(splitter, text, expected_sentences):
    """Test sentence splitting for various languages but not limited to."""
    sentences = splitter.split(text, lang="auto")
    assert sentences == expected_sentences


@pytest.mark.parametrize(
    "text, expected_sentences",
    [
        (
            "Goeie môre. Hoe gaan dit? Dit gaan goed met my.",
            ["Goeie môre.", "Hoe gaan dit?", "Dit gaan goed met my."],
        ),  # Afrikaans
        (
            "Bonjou tout moun! Non pa mwen se Bob.",
            ["Bonjou tout moun!", "Non pa mwen se Bob."],
        ),  # Haitian Creole
    ],
)
def test_unsupported_language_fallback(splitter, text, expected_sentences):
    """Test fallback to universal regex splitter for unsupported languages."""
    sentences = splitter.split(text, "auto")
    assert sentences == expected_sentences


# --- Custom Splitter Tests ---


def test_custom_splitter_usage(registry):
    """Test that the splitter can work a custom splitter without errors."""

    @registry.register("x_lang")
    def custom_x_splitter(text: str):
        return [s.strip() for s in text.split("X")]

    try:
        splitter = SentenceSplitter()

        text = "ThisXisXaXtestXstring."
        expected_sentences = ["This", "is", "a", "test", "string."]

        sentences = splitter.split(text, lang="x_lang")

        assert sentences == expected_sentences
    finally:
        registry.unregister("x_lang")


@pytest.mark.parametrize(
    "splitter_name, callback_func, expected_match",
    [
        (
            "invalid_list_splitter",
            lambda text: "This is a single string.",  # Returns str, not list[str]
            "Input should be a valid list.\n  Found: (input='This is a single string.', type=str)",
        ),
        (
            "list_non_string_splitter",
            lambda text: ["hello", 123, "world"],  # List contains non-strings
            "Input should be a valid string.\n  Found: (input=123, type=int)",
        ),
        (
            "failing_splitter",
            lambda text: (_ for _ in ()).throw(
                ValueError("Intentional failure in custom splitter.")
            ),
            "Splitter 'failing_splitter' for lang 'xx' raised an exception.\nDetails: Intentional failure in custom splitter.",
        ),
    ],
)
def test_custom_splitter_validation_scenarios(
    splitter, splitter_name, callback_func, expected_match, registry
):
    """Test various custom splitter validation scenarios."""

    @registry.register("xx", name=splitter_name)
    def _temp_splitter(text):
        return callback_func(text)

    try:
        with pytest.raises(CallbackError, match=re.escape(expected_match)):
            assert registry.is_registered("xx")
            splitter.split("Some text.", lang="xx")
    finally:
        registry.unregister("xx")
