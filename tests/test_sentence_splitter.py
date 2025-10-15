import re
import pytest
from chunklet.sentence_splitter import (
    SentenceSplitter,
    registered_splitter,
    unregister_splitter,
)
from chunklet.exceptions import CallbackExecutionError
from loguru import logger

# Silent logging
logger.remove()


# --- Fixture ---
@pytest.fixture
def splitter():
    """Provides a configured SentenceSplitter instance for testing"""
    return SentenceSplitter()


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

    def test_low_confidence_detection_fallback(splitter, mocker, caplog):
        """Test fallback to universal regex splitter on low confidence language detection."""
        mocker.patch(
            "chunklet.utils.detect_text_language.detect_text_language",
            return_value=("en", 0.5),
        )
        with caplog.at_level(logger.DEBUG):
            splitter.split("This is a test.", "auto")
        assert "Low confidence in language detected" in caplog.text


# --- Custom Splitter Tests ---


def test_custom_splitter_usage():
    """Test that the splitter can work a custom splitter without errors."""

    @registered_splitter("x_lang")
    def custom_x_splitter(text: str):
        return [s.strip() for s in text.split("X")]

    try:
        splitter = SentenceSplitter()

        text = "ThisXisXaXtestXstring."
        expected_sentences = ["This", "is", "a", "test", "string."]

        sentences = splitter.split(text, lang="x_lang")

        assert sentences == expected_sentences
    finally:
        unregister_splitter("x_lang")


@pytest.mark.parametrize(
    "lang, callback_func, expected_match",
    [
        (
            "invalid_list_splitter",
            lambda text: "This is a single string.",  # Returns str, not list[str]
            "Splitter '_temp_splitter' returns an invalid type: [] Input should be a valid list (input='This is a single string.', type=str).\n💡Hint: Make sure your splitter returns a list of strings.",
        ),
        (
            "list_non_string_splitter",
            lambda text: ["hello", 123, "world"],  # List contains non-strings
            "Splitter '_temp_splitter' returns an invalid type: [1] Input should be a valid string (input=123, type=int).\n💡Hint: Make sure your splitter returns a list of strings.",
        ),
        (
            "failing_splitter",
            lambda text: (_ for _ in ()).throw(
                ValueError("Intentional failure in custom splitter.")
            ),
            "Splitter '_temp_splitter' raised an exception.\n💡Hint: Review the logic inside this function.\nDetails: Intentional failure in custom splitter.",
        ),
    ],
)
def test_custom_splitter_validation_scenarios(
    splitter, lang, callback_func, expected_match
):
    """Test various custom splitter validation scenarios."""

    @registered_splitter(lang)
    def _temp_splitter(text):
        return callback_func(text)

    try:
        with pytest.raises(CallbackExecutionError, match=re.escape(expected_match)):
            splitter.split("Some text.", lang=lang)
    finally:
        unregister_splitter(lang)
