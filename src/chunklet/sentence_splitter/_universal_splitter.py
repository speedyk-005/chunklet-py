import regex as re

from chunklet.sentence_splitter.terminators import GLOBAL_SENTENCE_TERMINATORS

SENTENCE_TERMINATORS = "".join(GLOBAL_SENTENCE_TERMINATORS)

FLATTENED_NUMBERED_LIST_PATTERN = re.compile(
    rf"(?<=[{SENTENCE_TERMINATORS}:])\s+(\p{{N}}\.)+"
)

QUOTE_OR_PAREN_PATTERN = re.compile(
    r"(\p{Pi}|['\"]).+?(\p{Pf}|\1)|"
    r"\p{Ps}.+?\p{Pe}",
    re.S | re.X,
)

HASHED_PATTERN = re.compile(r"##-?\d+##")
NUMBERED_LIST_PATTERN = re.compile(r"[\n:]\s*\p{N}\.")

SENTENCE_END_PATTERN = re.compile(
    rf"""
    (?<!\b(?:\p{{Lu}}\p{{Ll}}{{1,4}}\.)+)  # Latin abbreviations (e.g., Dr., Prof.)
    (?<=[{SENTENCE_TERMINATORS}])          # sentence-ending punctuation
    (?=[\p{{Lo}}\p{{Lt}}]|\s+[^\p{{Ll}}])                     # Followed by optional space + non-lowercase letter
    """,
    re.X,
)


class UniversalSplitter:
    """
    Language-agnostic sentence boundary detector using regex patterns.

    A universal splitter using Unicode-aware regex patterns for any language.

    Handles:
      - Unicode sentence terminators
      - Numbered lists and headings
      - Quoted sentences
      - Line breaks and whitespace

    Use cases:
      - Primary splitter for languages without dedicated support
      - Fallback when language-specific splitters unavailable
    """

    def split(self, text: str) -> list[str]:
        """
        Splits text into sentences using rule-based regex patterns.

        Args:
            text: The input text to be segmented into sentences.

        Returns:
            A list of sentences after segmentation.
        """

        def mask(match: re.Match, norm_map: dict):
            # Generate the integer hash and Convert to string
            # because re.sub MUST return a string
            # Also fence them for easy detection
            hashed_str = f"##{hash(match.group())}##"

            # Store the mapping for later reconstruction
            norm_map[hashed_str] = match.group()
            return hashed_str

        def unmask(match: re.Match, norm_map: dict):
            return norm_map.get(match.group(), match.group())

        text = FLATTENED_NUMBERED_LIST_PATTERN.sub(r"\n \1", text.strip())

        # Normalize to protect them
        norm_map = {}
        text = QUOTE_OR_PAREN_PATTERN.sub(lambda m: mask(m, norm_map), text)
        text = NUMBERED_LIST_PATTERN.sub(lambda m: mask(m, norm_map), text)

        # Firstly, split base on punctuation
        # then split further on newline
        final_sentences = []
        sentences = SENTENCE_END_PATTERN.split(text.strip())

        for sent in sentences:
            if sent:
                final_sentences.extend(sent.strip().splitlines())

        # Restore the normalization
        return [
            HASHED_PATTERN.sub(lambda m: unmask(m, norm_map), sent)
            for sent in final_sentences
            if sent.strip()
        ]


# --- Example usage ---
if __name__ == "__main__":  # pragma: no cover
    import textwrap

    complex_text = textwrap.dedent("""
        Dr. Smith, the lead researcher at the U.S.A. I want 1. He want to talk to Dr. Smith. Space Agency, said: "We've reached 123.45 light-years… incredible!"  OK.
        My email addresses is pierrot1234@gmail.com. Could you guess it?
        He added, Consider the following points (They are special.):
            1. All systems are operational.
            2. No anomalies detected. like 3.14 gram.
            3. Data for 2025 is ready.  hello ! ! ! !

        Meanwhile, the team in Paris (France) exclaimed: "Bravo! Très bien!" They laughed at number 2. Could this be real? Yes, it is.
        The Playlist includes:
          - Video: Mars landing
          - Image: Satellite view
          - Music: Space-themed track
    """)

    splitter = UniversalSplitter()
    sentences = splitter.split(complex_text)

    print("\n=== Final Sentences ===")
    for i, s in enumerate(sentences, 1):
        print(f"{i}: {s}")
