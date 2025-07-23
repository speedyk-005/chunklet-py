


import re
import math
import langid
import warnings
from functools import lru_cache
from typing import List, Callable, Optional
from loguru import logger
from sentence_splitter import SentenceSplitter
from sentsplit.segment import SentSplit
from mpire import WorkerPool

logger.remove()  # Suppress default Loguru output
warnings.filterwarnings("ignore", category=UserWarning, module="sentsplit.segment")  # Ignore sentsplit's pkg_resources warning

# Languages supported by SentSplit (CRF-based models)
LANGS_SENT_SPLIT = {
    "en", "fr", "de", "it", "pl", "pt", "lt", "ja", "ko", "ru", "zh", "tr"
}

# Additional languages supported by sentence_splitter (rule-based models)
LANGS_MOSES = {
    "ca", "cs", "da", "el", "es", "fi", "hu", "is", "lv",
    "nl", "no", "ro", "sk", "sl", "sv"
}


class Chunklet:
    """
    A multilingual sentence-based chunker with optional LRU caching.

    Supports intelligent sentence splitting and chunks sentences into overlapping
    blocks, suitable for context-aware NLP applications.

    Args:
        verbose (bool): Enable warnings for issues like low language detection confidence.
        use_cache (bool): Enable LRU caching for repeated chunk calls.
        token_counter (Callable): Function used to count tokens in a sentence.
    """

    def __init__(self, verbose: bool = True, use_cache: bool = False, token_counter: Optional[Callable[[str], int]] = None):
        self.verbose = verbose
        self.use_cache = use_cache
        self.token_counter = token_counter

    

    def _falllback_regex_spliiter(self, text: str) -> List[str]:
        """
        Regex-based fallback for sentence splitting. Handles common punctuation
        and merges mis-splits like abbreviations (e.g., "Dr.", "Sr.") or numbered lists.
        """
        common_end_triggers = r"?!…。！？؛٫،।."
        sentences = re.split(rf"\n|(?<=[{common_end_triggers}])\s*", text)

        if not sentences:
            return []

        fixed_sentences = []
        sentences = [s.rstrip() for s in sentences if s.strip()]

        for i in range(len(sentences)):
            if i == 0:
                fixed_sentences.append(sentences[i])
                continue

            prev = fixed_sentences[-1]
            curr = sentences[i]

            # Merge if current segment is just punctuation or a standalone abbreviation/list item (e.g., "N.A.S.A.", "1.")
            if (
                re.match(fr"[{common_end_triggers}].*", curr) or
                re.fullmatch(r"(\w|\d).\s?", curr)
            ):
                fixed_sentences[-1] += " " + curr
            # Merge common abbreviations (e.g., "Dr.", "Mrs.") followed by non-capitalized word
            elif (
                re.search(r"\b[A-Z][a-z]{0,3}\.$", prev) and
                curr and re.match(fr"[^{common_end_triggers}A-Z]*[a-z].*", curr)
            ):
                fixed_sentences[-1] += " " + curr
            else:
                fixed_sentences.append(curr)

        return fixed_sentences

    def _get_sentence_splitter(self, text: str, lang: str) -> Callable[[str], List[str]]:
        """
        Selects the best sentence splitter: CRF-based, rule-based, or regex fallback.
        """
        if lang == "auto":
            lang_detected, confidence = langid.classify(text)
            if confidence < 0.90 and self.verbose:
                logger.warning(f"Low confidence in language detection: '{lang_detected}' ({confidence:.2f}).")
            lang = lang_detected if confidence > 0.9 else lang  # Use detected lang only if confident        
        if lang in LANGS_SENT_SPLIT:            
            return SentSplit(lang).segment

        if lang in LANGS_MOSES:
            print("Using SentenceSplitter")
            return SentenceSplitter(language=lang).split

        if self.verbose:
            logger.warning(f"Language '{lang}' not fully supported. Falling back to regex splitter.")        
        return self._falllback_regex_spliiter

    def _chunk(
        self,
        text: str,
        lang: str = "auto",
        mode: str = "hybrid",
        max_tokens: int = 512,
        max_sentences: int = 100,
        overlap_fraction: float = 0.2,
        offset: int = 0,
    ) -> List[str]:
        """
        Core chunking logic: splits text into overlapping chunks based on mode (sentence, token, hybrid).
        """
        if not text:
            return []

        if mode not in {"sentence", "token", "hybrid"}:
            raise ValueError("Invalid mode. Choose from 'sentence', 'token', or 'hybrid'.")

        if mode in {"token", "hybrid"} and self.token_counter is None:
            raise ValueError("A 'token_counter' function must be provided for 'token' or 'hybrid' modes.")

        if mode == "sentence":
            max_tokens = math.inf
        elif mode == "token":
            max_sentences = math.inf

        splitter = self._get_sentence_splitter(text, lang)
        sentences = splitter(text)
        if not sentences:
            return []

        if offset >= len(sentences):
            if self.verbose:
                logger.warning(f"Offset {offset} >= total sentences {len(sentences)}. Returning empty list.")
            return []

        sentences = sentences[offset:]

        chunks = []
        if mode == "sentence":
            overlap_num = int(max_sentences * overlap_fraction)
            if overlap_fraction > 0 and overlap_num == 0 and max_sentences > 1:
                overlap_num = 1
            overlap_num = min(overlap_num, max_sentences - 1)
            stride = max(1, max_sentences - overlap_num)

            for idx in range(0, len(sentences), stride):
                end_idx = min(idx + max_sentences, len(sentences))
                chunk = sentences[idx:end_idx]
                if not chunk:
                    break
                chunks.append(chunk)

        else:
            curr_chunk: List[str] = []
            token_count = 0
            sentence_count = 0

            for sentence in sentences:
                sentence_tokens = self.token_counter(sentence)

                if curr_chunk and (
                    (token_count + sentence_tokens > max_tokens) or
                    (sentence_count + 1 > max_sentences)
                ):
                    chunks.append(curr_chunk)
                    overlap_num_dynamic = int(len(curr_chunk) * overlap_fraction)

                    if overlap_fraction > 0 and overlap_num_dynamic == 0 and len(curr_chunk) > 0:
                        overlap_num_dynamic = 1
                    overlap_num_dynamic = min(overlap_num_dynamic, len(curr_chunk) - 1 if len(curr_chunk) > 0 else 0)

                    curr_chunk = curr_chunk[-overlap_num_dynamic:]
                    token_count = sum(self.token_counter(s) for s in curr_chunk)
                    sentence_count = len(curr_chunk)

                curr_chunk.append(sentence)
                token_count += sentence_tokens
                sentence_count += 1

            if curr_chunk:
                chunks.append(curr_chunk)

        return ["\n".join(chunk) for chunk in chunks]

    @lru_cache(maxsize=25)
    def _chunk_cached(self, *args, **kwargs):
        """A cached version of the core chunking logic."""
        return self._chunk(*args, **kwargs)

    def chunk(self, *args, **kwargs) -> List[str]:
        """
        Public interface for chunking text. Uses caching if enabled.
        """
        if self.use_cache:
            return self._chunk_cached(*args, **kwargs)
        return self._chunk(*args, **kwargs)

    def batch_chunk(
        self,
        texts: List[str],
        lang: str = "auto",
        mode: str = "hybrid",
        max_tokens: int = 512,
        max_sentences: int = 100,
        overlap_fraction: float = 0.2,
        offset: int = 0,
        n_jobs: int = None,
    ) -> List[List[str]]:
        """
        Splits a list of texts into overlapping chunks.
        """
        if not texts:
            return []

        results = []
        for text in texts:
            chunks = self.chunk(
                text=text,
                lang=lang,
                mode=mode,
                max_tokens=max_tokens,
                max_sentences=max_sentences,
                overlap_fraction=overlap_fraction,
                offset=offset
            )
            results.append(chunks)

        return results

    def preview_sentences(self, text: str, lang: str = "auto") -> List[str]:
        """
        Returns raw sentences from text without chunking. Useful for inspecting segmentation.
        """
        return self._get_sentence_splitter(text, lang)(text)


if __name__ == "__main__":
    import textwrap

    def simple_token_counter(sentence: str) -> int:
        return len(sentence.split())

    chunker = Chunklet(verbose=True, use_cache=True, token_counter=simple_token_counter)

    sample_text = textwrap.dedent("""
        She loves cooking. He studies AI. "You are a Dr." she said. The weather is great.
        We play chess. Books are fun.
        The Playlist contains:
            - two videos
            - one music
        Robots are learning.
        It's raining. Let's code. Mars is red. Sr. sleep is rare.
        Consider item 1. This is a test.
        The year is 2025. This is a good year.
        The section is N.A.S.A. related.
    """)

    print("=== Hybrid Mode (token and sentence limits with GUARANTEED overlap) ===")
    chunks = chunker.chunk(
        sample_text,
        mode="hybrid",
        max_tokens=30,
        max_sentences=7,
        overlap_fraction=0.3
    )
    for i, c in enumerate(chunks):
        print(f"Chunk {i+1} (Tokens: {simple_token_counter(c)}, Sentences: {len(c.splitlines())}):\n{c}\n")

    print("\n=== Sentence Mode (sentence limit only, with GUARANTEED overlap) ===")
    chunks = chunker.chunk(
        sample_text,
        mode="sentence",
        max_sentences=5,
        overlap_fraction=0.2
    )
    for i, c in enumerate(chunks):
        print(f"Chunk {i+1} (Sentences: {len(c.splitlines())}):\n{c}\n")

    print("\n=== Token Mode (token limit only, with GUARANTEED overlap) ===")
    chunks = chunker.chunk(
        sample_text,
        mode="token",
        max_tokens=25,
        overlap_fraction=0.3
    )
    for i, c in enumerate(chunks):
        print(f"Chunk {i+1} (Tokens: {simple_token_counter(c)}, Sentences: {len(c.splitlines())}):\n{c}\n")