"""
This module contains unit tests for the SentenceSplitter class,
covering its core functionality, fallback mechanisms, custom splitter
integration, and error handling.
"""
import re
import pytest
from chunklet.sentence_splitter import SentenceSplitter
from chunklet.plain_text_chunker import PlainTextChunker
from chunklet.exceptions import InvalidInputError, CallbackExecutionError


# --- Fixture ---
@pytest.fixture
def splitter():
    """Provides a configured SentenceSplitter instance for testing"""
    return SentenceSplitter()

# --- Multilingual Splitting Tests ---
@pytest.mark.parametrize(
    "text, expected_sentences",
    [
        ("Hello. How are you? I am fine.", ["Hello.", "How are you?", "I am fine."]),  # English
        ("Bonjour. Comment allez-vous? Je vais bien.", ["Bonjour.", "Comment allez-vous?", "Je vais bien."]),  # French
        ("Hola. ¿Cómo estás? Estoy bien.", ["Hola.", "¿Cómo estás?", "Estoy bien."]),  # Spanish
        ("Das ist ein Satz. Hier ist noch ein Satz. Und noch einer.", ["Das ist ein Satz.", "Hier ist noch ein Satz.", "Und noch einer."]),  # German
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
        ("Goeie môre. Hoe gaan dit? Dit gaan goed met my.", ["Goeie môre.", "Hoe gaan dit?", "Dit gaan goed met my."]),  # Afrikaans
        ("Bonjou tout moun! Non pa mwen se Bob.", ["Bonjou tout moun!", "Non pa mwen se Bob."]),  # Haitian Creole
    ],
)
def test_unsupported_language_fallback(splitter, text, expected_sentences):
    """Test fallback to universal regex splitter for unsupported languages."""
    sentences = splitter.split(text, 'auto')
    assert sentences == expected_sentences

def test_low_confidence_detection_fallback(splitter, mocker):
    """Test fallback to universal regex splitter on low confidence language detection."""
    mocker.patch(
        "chunklet.sentence_splitter.sentence_splitter.detect_text_language",
        return_value=("en", 0.5),
    )
    sentences, warnings = splitter.split("This is a test.", "auto", _return_warnings=True)
    assert "Low confidence in language detected" in "".join(warnings)


# --- Custom Splitter Tests ---
def test_custom_splitter_init_validation_error():
    """Test that InvalidInputError is raised for invalid custom_splitters during initialization."""
    invalid_custom_splitters = [
        {
            "name": "MissingCallbackSplitter",
            "languages": "en",
            # "callback": missing
        }
    ]
    with pytest.raises(InvalidInputError, match="Invalid custom_splitters configuration."):        SentenceSplitter(custom_splitters=invalid_custom_splitters)

def test_custom_splitter_usage():
    """Test that the splitter can work a custom splitter without errors."""

    # Define a simple custom splitter that splits by 'X'
    def custom_x_splitter(text: str):
        return text.split("X")

    custom_splitters = [
        {
            "name": "XSplitter",
            "languages": "en",
            "callback": custom_x_splitter,
        }
    ]

    # Initialize Splitter with the custom splitter
    splitter = SentenceSplitter(custom_splitters=custom_splitters)

    text = "ThisXisXaXtestXstring."
    expected_sentences = ["This", "is", "a", "test", "string."]

    sentences = splitter.split(text, lang="en")

    assert sentences == expected_sentences


@pytest.mark.parametrize(
    "splitter_name, callback_func, expected_match",
    [
        (
            "InvalidListSplitter",
            lambda text: "This is a single string.",  # Returns str, not list[str]
            "Custom splitter 'InvalidListSplitter' callback returned an invalid type. Expected a list of strings, but got <class 'str'> with elements of mixed types.",
        ),
        (
            "ListNonStringSplitter",
            lambda text: ["hello", 123, "world"],  # List contains non-strings
            "Custom splitter 'ListNonStringSplitter' callback returned an invalid type. Expected a list of strings, but got <class 'list'> with elements of mixed types.",
        ),
        (
            "FailingSplitter",
            lambda text: (_ for _ in ()).throw(ValueError("Intentional failure in custom splitter.")),
            "Custom splitter 'FailingSplitter' callback failed for text starting with: 'Some text....'.\\nDetails: Intentional failure in custom splitter.",
        ),
    ],
)
def test_custom_splitter_validation_scenarios(
    splitter, splitter_name, callback_func, expected_match
):
    """Test various custom splitter validation scenarios."""
    custom_splitters = [
        {
            "name": splitter_name,
            "languages": "en",
            "callback": callback_func,
        }
    ]
    
    # Initialize Splitter with the custom splitter (should not raise error at init for these cases)
    splitter_with_custom = SentenceSplitter(custom_splitters=custom_splitters)

    with pytest.raises(CallbackExecutionError, match=expected_match):
        splitter_with_custom.split("Some text.", lang="en")
