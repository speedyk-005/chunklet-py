import regex as re

from chunklet.sentence_splitter.terminators import GLOBAL_SENTENCE_TERMINATORS


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

    def __init__(self):
        self.sentence_terminators = "".join(GLOBAL_SENTENCE_TERMINATORS)

        # Patterns for handling numbered lists
        self.flattened_numbered_list_pattern = re.compile(
            rf"(?<=[{self.sentence_terminators}:])\s+(\p{{N}}\.)+"
        )

        self.numbered_list_pattern = re.compile(r"([\n:]\s*)(\p{N})\.")
        self.norm_numbered_list_pattern = re.compile(r"(\s*)(\p{N})<DOT>")

        # Core sentence split regex
        self.sentence_end_pattern = re.compile(
            rf"""
            (?<!\b(\p{{Lu}}\p{{Ll}}{{1, 4}}\.)*)   # Latin-only abbreviation
            (?<=[{self.sentence_terminators}]        # sentence-ending punctuation
            [\"'》」\p{{pf}}\p{{pe}}]*)?                 # optional quotes or closing chars
            (?=\s+[\p{{Lu}}\p{{Lo}}\p{{Lt}}]|\s*\n|\s*$)  # followed by letter (upper or catch-all) or end
            """,
            re.VERBOSE,
        )

    def split(self, text: str) -> list[str]:
        """
        Splits text into sentences using rule-based regex patterns.

        Args:
            text (str): The input text to be segmented into sentences.

        Returns:
            list[str]: A list of sentences after segmentation.

        Notes:
            - Normalizes numbered lists during splitting and restores them afterward.
            - Handles punctuation, newlines, and common edge cases.
        """
        # handle flattened numbered lists
        text = self.flattened_numbered_list_pattern.sub(r"\n \1", text.strip())

        # normalize numbered lists
        text = self.numbered_list_pattern.sub(r"\1\2<DOT>", text.strip())

        # Firstly, split base on punctuation
        # then split further on newline
        final_sentences = []
        sentences = self.sentence_end_pattern.split(text.strip())
        for sent in sentences:
            if sent:
                final_sentences.extend(sent.strip().splitlines())

        # remove _ protection in numbered list numbers
        return [
            self.norm_numbered_list_pattern.sub(r"\1\2.", sent).rstrip()
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
