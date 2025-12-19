from __future__ import annotations
import regex as re
from typing import List
from chunklet.sentence_splitter.terminators import GLOBAL_SENTENCE_TERMINATORS


class FallbackSplitter:
    """
    Rule-based, language-agnostic sentence boundary detector.

    A rule-based, sentence boundary detection tool that doesn't rely on hardcoded lists of
    abbreviations or sentence terminators, making it adaptable to various text formats and domains.

    FallbackSplitter uses regex patterns to split text into sentences, handling:
      - Common sentence-ending punctuation (., !, ?)
      - Abbreviations and acronyms (e.g., Dr., Ph.D., U.S.)
      - Numbered lists and headings
      - Multi-punctuation sequences (e.g., ! ! !, ?!)
      - Line breaks and whitespace normalization
      - Decimal numbers and inline numbers

    Sentences are conservatively segmented, prioritizing context over aggressive splitting,
    which reduces false splits inside abbreviations, multi-punctuation sequences, or numeric constructs.
    """

    def __init__(self):
        """Initializes regex patterns for sentence splitting."""
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
            (?<!\b(\p{{Lu}}\p{{Ll}}{{1, 5}}\.)*)   # negative lookbehind for abbreviations
            (?<=[{self.sentence_terminators}]        # sentence-ending punctuation
            [\"'》」\p{{pf}}\p{{pe}}]*)                  # optional quotes or closing chars
            (?=\s+\p{{Lu}}|\s*\n|\s*$)               # followed by uppercase or end of text
            """,
            re.VERBOSE | re.UNICODE,
        )

    def split(self, text: str) -> List[str]:
        """
        Splits text into sentences using rule-based regex patterns.

        Args:
            text (str): The input text to be segmented into sentences.

        Returns:
            List[str]: A list of sentences after segmentation.

        Notes:
            - Normalizes numbered lists during splitting and restores them afterward.
            - Handles punctuation, newlines, and common edge cases.
        """
        # Stage 1: handle flattened numbered lists
        text = self.flattened_numbered_list_pattern.sub(r"\n \1", text.strip())

        # Stage 2: normalize numbered lists
        text = self.numbered_list_pattern.sub(r"\1\2<DOT>", text.strip())

        # Stage 3: first pass - punctuation-based split
        sentences = self.sentence_end_pattern.split(text.strip())

        # Stage 4: remove empty strings and strip whitespace
        fixed_sentences = [s.strip() for s in sentences if s and s.strip()]

        # Stage 5: second pass - split further on newline (if not at start)
        final_sentences = []
        for sent in fixed_sentences:
            final_sentences.extend(sent.splitlines())

        # Stage 6: remove _ in numbered list numbers
        return [
            self.norm_numbered_list_pattern.sub(r"\1\2.", sent).rstrip()
            for sent in final_sentences
            if sent.strip()
        ]


# ===== Example usage =====
if __name__ == "__main__":  # pragma: no cover
    import textwrap

    complex_text = textwrap.dedent(
        """
        Dr. Smith, the lead researcher at the U.S.A. I want 1. He want to talk to Dr. Smith. Space Agency, said: "We've reached 123.45 light-years… incredible!"  OK.
        He added, Consider the following points (They are special.):
            1. All systems are operational.
            2. No anomalies detected. like 3.14 gram.
            3. Data for 2025 is ready.  hello ! ! ! !

        Meanwhile, the team in Paris (France) exclaimed: "Bravo! Très bien!" They laughed at number 2. Could this be real? Yes, it is.
        The Playlist includes:
          - Video: Mars landing
          - Image: Satellite view
          - Music: Space-themed track
        """
    )

    splitter = FallbackSplitter()
    sentences = splitter.split(complex_text)

    print("\n=== Final Sentences ===")
    for i, s in enumerate(sentences, 1):
        print(f"{i}: {s}")
