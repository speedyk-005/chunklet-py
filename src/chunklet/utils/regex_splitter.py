import re
import unicodedata
from typing import List

SENTENCE_END_TRIGGERS = r".!?…。！？؟؛।ฯ‽"


class RegexSplitter:
    """
    Rule-based sentence splitter using regex.
    Handles common sentence boundaries, abbreviations, acronyms, decimals,
    and misplaced punctuation.
    """

    def __init__(self):
        # Regex to split text by sentence-ending punctuation or newlines
        self.sentence_end_regex = re.compile(rf"(?<=[{SENTENCE_END_TRIGGERS}]|\n)\s*")

        # Regex for abbreviations (e.g., Mr., Dr.)
        self.abbreviation_regex = re.compile(r"\b[A-Z][a-z]{1,3}\.\s?$")

        # Regex for acronyms and decimals (e.g., N.A.S.A., 123.4)
        self.acronym_regex = re.compile(r"[A-Z]\.\s?$")
        self.after_acronym_regex = re.compile(r"([A-Z]\.\s?){2,}$")
        self.decimals_regex = re.compile(r"\d\.$")

    def count_unbalanced_closings(self, text: str) -> int:
        """
        Returns 0 if all brackets/quotes are properly balanced.
        Returns a positive number indicating the number of unmatched closing characters.
        """
        stack = []
        unbalanced_closing = 0

        for char in text:
            cat = unicodedata.category(char)
            # Opening chars: Ps (open punctuation), Pi (initial quote)
            if cat in ("Ps", "Pi"):
                stack.append(char)
            # Closing chars: Pe (close punctuation), Pf (final quote)
            elif cat in ("Pe", "Pf"):
                if stack:
                    stack.pop()
                else:
                    # unmatched closing
                    unbalanced_closing += 1

        return unbalanced_closing

    def split(self, text: str) -> List[str]:
        """
        Splits text into sentences using a smart, rule-based regex approach.
        Designed as a robust fallback, handling various sentence boundary issues.

        Args:
            text (str): The input text to split.

        Returns:
            List[str]: A list of sentences.
        """
        # Initial split by sentence-ending punctuation
        sentences = self.sentence_end_regex.split(text.strip())
        sentences = [sent for sent in sentences if sent.strip()]

        fixed_sentences = []
        if sentences:
            fixed_sentences.append(sentences[0])

        # Process each sentence to handle edge cases
        for curr_sent in sentences[1:]:
            prev_sent = fixed_sentences[-1]
            if (
                self.sentence_end_regex.match(
                    curr_sent
                )  # Re-join leftover punctuation, eg: hello!!
                or self.acronym_regex.fullmatch(
                    curr_sent
                )  # Re-join patterns resembling initials.
                or (
                    self.decimals_regex.search(prev_sent) and curr_sent[0].isdigit()
                )  # Re-join decimals but not numbered.
            ):
                fixed_sentences[-1] += curr_sent
            elif (
                self.abbreviation_regex.search(prev_sent) and not curr_sent[0].isupper()
            ) or self.after_acronym_regex.search(
                prev_sent
            ):  # Avoid splitting after an abbreviation or a fake positive acronym , eg: AI.
                fixed_sentences[-1] += " " + curr_sent
            elif count := self.count_unbalanced_closings(
                prev_sent
            ):  # Move closing back to prevent sentence end1.
                fixed_sentences[-1] += curr_sent[:count]
                fixed_sentences.append(curr_sent[count:])
            else:
                fixed_sentences.append(curr_sent)

        return [sent + " " for sent in fixed_sentences]


# Demonstration
if __name__ == "__main__":
    import textwrap

    text = textwrap.dedent(
        """
    She loves cooking. He studies AI. "You are a Dr.", she said. The weather is great. We play chess. Books are fun, aren't they?
 
    The Playlist contains:
      - two videos
      - one image
      - one music

    Robots are learning. It's raining. Let's code. Mars is red. Sr. sleep is rare. Consider item 1. This is a test. The year is 2025. This is a good year since N.A.S.A. reached 123.4 light year more.
    """
    )

    sentences = RegexSplitter().split(text)
    for i, sent in enumerate(sentences):
        print(f"---- sent ({i}) ----\n{sent}\n")
