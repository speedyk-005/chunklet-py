"""String and text utilities shared across the project."""

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass

_WORD_RE = re.compile(r"\b[\w'-]+\b")


def slugify(text: str) -> str:
    """Turn arbitrary text into a URL-safe slug."""
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return _WORD_RE_REPLACE_DASHES(ascii_text.lower())


def _WORD_RE_REPLACE_DASHES(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def count_words(text: str) -> int:
    """Count words in text using a small regex."""
    return len(_WORD_RE.findall(text))


def most_common_words(text: str, limit: int = 5) -> list[tuple[str, int]]:
    """Return the most frequent words with their counts."""
    words = [w.lower() for w in _WORD_RE.findall(text)]
    return Counter(words).most_common(limit)


def truncate(text: str, max_chars: int, suffix: str = "...") -> str:
    """Truncate text to max_chars, appending a suffix when cut."""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - len(suffix)].rstrip() + suffix


def wrap(text: str, width: int = 72) -> str:
    """Word-wrap text to a given line width."""
    lines = []
    for paragraph in text.split("\n\n"):
        current = ""
        for word in paragraph.split():
            candidate = word if not current else f"{current} {word}"
            if len(candidate) <= width:
                current = candidate
                continue
            if current:
                lines.append(current)
            current = word
        if current:
            lines.append(current)
        lines.append("")
    return "\n".join(lines).rstrip("\n")


@dataclass
class WordStats:
    """Aggregated word statistics for a piece of text."""

    total: int
    unique: int
    average_length: float


def summarize(text: str) -> WordStats:
    """Compute total, unique, and average word length for text."""
    words = [w.lower() for w in _WORD_RE.findall(text)]
    if not words:
        return WordStats(total=0, unique=0, average_length=0.0)
    average = sum(len(word) for word in words) / len(words)
    return WordStats(total=len(words), unique=len(set(words)), average_length=average)


class TextPipeline:
    """A small pipeline that chains cleanup steps over incoming text."""

    def __init__(self) -> None:
        self._steps: list[tuple[str, ...]] = []

    def add_step(self, name: str) -> None:
        """Register a named cleanup step."""
        self._steps.append((name,))

    def run(self, text: str) -> str:
        """Apply every registered step in order."""
        result = text
        for name in self._steps:
            result = self._apply_step(result, name)

        return result

    def _apply_step(self, text: str, name: str) -> str:
        if name == "lowercase":
            return text.lower()
        if name == "collapse-space":
            return re.sub(r"\s+", " ", text).strip()

        return text
