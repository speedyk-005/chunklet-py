"""
This module contains the language sets for the supported sentence splitters.
Each set is filtered to contain only the languages truly unique to that library.
"""

# Complete set of languages supported by pysbd (Python Sentence Boundary Disambiguation) (23)
PYSBD_SUPPORTED_LANGUAGES = {
    "am",  # Amharic
    "ar",  # Arabic
    "bg",  # Bulgarian
    "da",  # Danish
    "de",  # German
    "el",  # Greek
    "en",  # English
    "es",  # Spanish
    "fa",  # Persian
    "fr",  # French
    "hi",  # Hindi
    "hy",  # Armenian
    "it",  # Italian
    "ja",  # Japanese
    "kk",  # Kazakh
    "mr",  # Marathi
    "my",  # Burmese
    "nl",  # Dutch
    "pl",  # Polish
    "ru",  # Russian
    "sk",  # Slovak
    "ur",  # Urdu
    "zh",  # Chinese
}

# Languages unique to sentsplit that are NOT supported by pysbd (4)
SENTSPLIT_UNIQUE_LANGUAGES = {
    "ko",  # Korean
    "lt",  # Lithuanian
    "pt",  # Portuguese
    "tr",  # Turkish
}

# Languages unique to Indic NLP Library that are NOT supported by the other libraries (11)
INDIC_NLP_UNIQUE_LANGUAGES = {
    "as",  # Assamese
    "bn",  # Bengali
    "gu",  # Gujarati
    "kn",  # Kannada
    "ml",  # Malayalam
    "ne",  # Nepali
    "or",  # Odia
    "pa",  # Punjabi
    "sa",  # Sanskrit
    "ta",  # Tamil
    "te",  # Telugu
}

# Languages unique to Sentencex that are NOT supported by the other libraries (2)
SENTENCEX_UNIQUE_LANGUAGES = {
    "ca",  # Catalan
    "fi",  # Finnish
}


# Set of all supported languages
SUPPORTED_LANGUAGES = (
    PYSBD_SUPPORTED_LANGUAGES
    | SENTSPLIT_UNIQUE_LANGUAGES
    | INDIC_NLP_UNIQUE_LANGUAGES
    | SENTENCEX_UNIQUE_LANGUAGES
)

# For languages not explicitly listed above, a universal, regex-based sentence splitter is used as a fallback to ensure broad compatibility.
