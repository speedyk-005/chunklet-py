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

# Languages unique to Sentencex that are NOT supported by the other libraries (15)
# `Sentencex` is a powerful library that aims to support all languages with a Wikipedia presence,
# with fallbacks for over 200 languages.
# It uses a fallback system to support a vast number of languages.
# The set below is a curated selection of the more reliable
# and unique languages from `Sentencex`. It has been filtered to:
#    *   Include only languages with an ISO 639-1 code.
#    *   Exclude languages that are already covered by `pysbd`, `sentsplit`, or `Indic NLP Library`.
#    *   Exclude languages that are fallbacks to other languages but are not reliable enough.
SENTENCEX_UNIQUE_LANGUAGES = {
    "an",  # Aragonese
    "ca",  # Catalan
    "co",  # Corsican
    "cs",  # Czech
    "fi",  # Finnish
    "gl",  # Galician
    "io",  # Ido
    "jv",  # Javanese
    "li",  # Limburgish
    "mo",  # Moldovan
    "nds",  # Low German
    "nn",  # Norwegian Nynorsk
    "oc",  # Occitan
    "su",  # Sundanese
    "wa",  # Walloon
}


# Set of all supported languages
SUPPORTED_LANGUAGES = (
    PYSBD_SUPPORTED_LANGUAGES
    | SENTSPLIT_UNIQUE_LANGUAGES
    | INDIC_NLP_UNIQUE_LANGUAGES
    | SENTENCEX_UNIQUE_LANGUAGES
)

# For languages not explicitly listed above, a universal, regex-based sentence splitter is used as a fallback to ensure broad compatibility.
