

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

logger.remove() # Suppress default Loguru output
warnings.filterwarnings("ignore", category=UserWarning, module="sentsplit.segment") # Ignore sentsplit's pkg_resources warning

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
    """

    def __init__(self, verbose: bool = True, use_cache: bool = False):
        self.verbose = verbose
        self.use_cache = use_cache
        # Apply LRU cache to the internal _chunk method if caching is enabled
        self._cached_chunk = lru_cache(maxsize=25)(self._chunk)

    @staticmethod
    def _static_chunk_helper(chunk_params: tuple):
        """
        Helper for parallel processing. Creates a temporary Chunklet instance per worker
        to perform chunking, ensuring picklability and avoiding shared state issues.
        """
        text, lang, mode, max_tokens, max_sentences, token_counter, overlap_fraction, offset = chunk_params
        temp_chunker = Chunklet(verbose=False, use_cache=False) # No verbose/cache for worker instances
        return temp_chunker._chunk(text, lang, mode, max_tokens, max_sentences, token_counter, overlap_fraction, offset)


    def _simple_split(self, text: str) -> List[str]:
        """
        Regex-based fallback for sentence splitting. Handles common punctuation
        and merges mis-splits like abbreviations (e.g., "Dr.", "Sr.") or numbered lists.
        """
        common_end_triggers = r"?!…。！？؛٫،।\."
        sentences = re.split(rf"\n|(?<=[{common_end_triggers}])\s*", text.strip())

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
                re.fullmatch(r"(\w|\d)\.\s?", curr)
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
            lang = lang_detected if confidence > 0.9 else lang # Use detected lang only if confident

        if lang in LANGS_SENT_SPLIT:
            return SentSplit(lang).segment

        if lang in LANGS_MOSES:
            return SentenceSplitter(language=lang).split

        if self.verbose:
            logger.warning(f"Language '{lang}' not fully supported. Falling back to regex splitter.")
        return self._simple_split

    def _chunk(
        self,
        text: str,
        lang: str = "auto",
        mode: str = "hybrid",
        max_tokens: int = 512,
        max_sentences: int = 100,
        token_counter: Optional[Callable[[str], int]] = None,
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

        # Adjust limits based on mode: 'inf' means that limit is ignored
        if mode == "sentence":
            max_tokens = math.inf
        elif mode == "token":
            max_sentences = math.inf
        # 'hybrid' mode uses both limits

        # Token counter is required for token-based modes
        if mode in {"token", "hybrid"} and token_counter is None:
            raise ValueError("A 'token_counter' function must be provided for 'token' or 'hybrid' modes.")

        splitter = self._get_sentence_splitter(text, lang)
        sentences = splitter(text)
        if not sentences:
            return []

        if offset >= len(sentences):
            if self.verbose:
                logger.warning(f"Offset {offset} >= total sentences {len(sentences)}. Returning empty list.")
            return []

        sentences = sentences[offset:] # Start processing from specified offset

        chunks = []
        if mode == "sentence":
            # Sentence-based mode: fixed size windows with overlap
            overlap_num = int(max_sentences * overlap_fraction)
            overlap_num = min(overlap_num, max_sentences - 1) # Ensure overlap < chunk size
            stride = max(1, max_sentences - overlap_num)

            chunks.append(sentences[:max_sentences]) # First chunk from start

            # Iterate with sliding window
            for idx in range(max_sentences, len(sentences), stride):
                chunk = sentences[idx - overlap_num: idx + stride]
                chunks.append(chunk)
        else:
            # Token/Hybrid mode: dynamic growth with splitting and proportional overlap
            curr_chunk: List[str] = []
            token_count = 0
            sentence_count = 0

            for sentence in sentences:
                sentence_tokens = token_counter(sentence)

                # If current chunk has content and adding this sentence would push it over
                if curr_chunk and (
                    (token_count + sentence_tokens > max_tokens) or
                    (sentence_count + 1 > max_sentences)
                ):
                    chunks.append(curr_chunk) # Finalize the current chunk

                    # Calculate dynamic overlap for the *just completed* chunk.
                    overlap_num_dynamic = int(len(curr_chunk) * overlap_fraction)

                    # Ensure at least 1 sentence overlap if overlap_fraction > 0 and possible
                    if overlap_fraction > 0 and overlap_num_dynamic == 0 and len(curr_chunk) > 0:
                        overlap_num_dynamic = 1

                    overlap_num_dynamic = min(overlap_num_dynamic, len(curr_chunk) -1 if len(curr_chunk) > 0 else 0)

                    # Initialize the new chunk with overlapping sentences from the previous chunk.
                    # The current 'sentence' (that triggered the split) will be added next.
                    curr_chunk = curr_chunk[-overlap_num_dynamic:]
                    token_count = sum(token_counter(s) for s in curr_chunk)
                    sentence_count = len(curr_chunk)

                # Add the current sentence to the active chunk (whether it's new or continuing)
                curr_chunk.append(sentence)
                token_count += sentence_tokens
                sentence_count += 1

            if curr_chunk: # Add any remaining sentences as the last chunk
                chunks.append(curr_chunk)

        # Join sentences within each sublist to form final string chunks
        return ["\n".join(chunk) for chunk in chunks]

    def chunk(
        self,
        text: str,
        lang: str = "auto",
        mode: str = "hybrid",
        max_tokens: int = 512,
        max_sentences: int = 100,
        token_counter: Optional[Callable[[str], int]] = None,
        overlap_fraction: float = 0.2, 
        offset: int = 0,
    ) -> List[str]:
        """
        Public interface for chunking text. Uses caching if enabled.
        """
        if self.use_cache:
            # Caching works best if token_counter is a stable/hashable function.
            # Avoid caching if token_counter changes frequently (e.g., new lambda each call).
            # Also ensure overlap_fraction is part of the cache key!
            return self._cached_chunk(text, lang, mode, max_tokens, max_sentences, token_counter, overlap_fraction, offset)
        return self._chunk(text, lang, mode, max_tokens, max_sentences, token_counter, overlap_fraction, offset)

    def batch_chunk(
        self,
        texts: List[str],
        lang: str = "auto",
        mode: str = "hybrid",
        max_tokens: int = 512,
        max_sentences: int = 100,
        token_counter: Optional[Callable[[str], int]] = None,
        overlap_fraction: float = 0.2, # Make sure this is passed through!
        offset: int = 0,
        n_jobs: int = None,
    ) -> List[List[str]]:
        """
        Splits a list of texts into overlapping chunks using parallel workers.
        """
        if not texts:
            return []

        # Prepare arguments for parallel processing.
        # Each element is a single-element tuple, where that element is the tuple
        # of parameters _static_chunk_helper expects. This ensures correct unpacking.
        args = [
            ((text, lang, mode, max_tokens, max_sentences, token_counter, overlap_fraction, offset),)
            for text in texts
        ]

        with WorkerPool(n_jobs=n_jobs) as pool:
            results = pool.map(self._static_chunk_helper, args)

        return results

    def preview_sentences(self, text: str, lang: str = "auto") -> List[str]:
        """
        Returns raw sentences from text without chunking. Useful for inspecting segmentation.
        """
        return self._get_sentence_splitter(text, lang)(text)


# === Example usage ===
if __name__ == "__main__":
    import textwrap

    # Simple token counter: counts words (for demonstration)
    def simple_token_counter(sentence: str) -> int:
        return len(sentence.split())

    chunker = Chunklet(verbose=True, use_cache=True)

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
        token_counter=simple_token_counter,
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
        token_counter=simple_token_counter,
        overlap_fraction=0.3
    )
    for i, c in enumerate(chunks):
        print(f"Chunk {i+1} (Tokens: {simple_token_counter(c)}, Sentences: {len(c.splitlines())}):\n{c}\n")

    print("\n=== Batch chunking with parallel processing (with GUARANTEED overlap) ===")
    texts = [sample_text, sample_text[:50] + " And another sentence.", "Short text."]
    batch_results = chunker.batch_chunk(
        texts,
        mode="hybrid",
        max_tokens=30,
        max_sentences=7,
        token_counter=simple_token_counter,
        overlap_fraction=0.3, 
        n_jobs=2
    )
    for i, text_chunks in enumerate(batch_results):
        print(f"\n--- Batch Result for Text {i+1} ---")
        for j, chunk in enumerate(text_chunks):
            print(f"  Chunk {j+1} (Tokens: {simple_token_counter(chunk)}, Sentences: {len(chunk.splitlines())}):\n  {chunk}\n")

    print("\n=== Preview Sentences (no chunking) ===")
    sentences_preview = chunker.preview_sentences("Hello there. How are you? I am fine.", lang="en")
    for i, s in enumerate(sentences_preview):
        print(f"Sentence {i+1}: {s}")

    print("\nCode it, test it, love it.!")