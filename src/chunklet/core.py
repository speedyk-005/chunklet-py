import sys
import re
import math
import concurrent.futures
from functools import lru_cache
from typing import List, Callable, Optional, Union, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from pysbd import Segmenter
from sentence_splitter import SentenceSplitter
from loguru import logger
from .utils.detect_text_language import detect_text_language

# Complete set of languages supported by pysbd (Python Sentence Boundary Disambiguation)
PYSBD_SUPPORTED_LANGUAGES = {
    "en",  # English
    "mr",  # Marathi
    "hi",  # Hindi
    "bg",  # Bulgarian
    "es",  # Spanish
    "ru",  # Russian
    "ar",  # Arabic
    "am",  # Amharic
    "hy",  # Armenian
    "fa",  # Persian (Farsi)
    "ur",  # Urdu
    "pl",  # Polish
    "zh",  # Chinese (Mandarin)
    "nl",  # Dutch
    "da",  # Danish
    "fr",  # French
    "it",  # Italian
    "el",  # Greek
    "my",  # Burmese (Myanmar)
    "ja",  # Japanese
    "de",  # German
    "kk",  # Kazakh
}

# Languages unique to SentenceSplitter that are NOT supported by pysbd
SENTENCESPLITTER_UNIQUE_LANGUAGES = {
    "ca",  # Catalan
    "cs",  # Czech
    "fi",  # Finnish
    "hu",  # Hungarian
    "is",  # Icelandic
    "lv",  # Latvian
    "lt",  # Lithuanian
    "no",  # Norwegian
    "pt",  # Portuguese
    "ro",  # Romanian
    "sk",  # Slovak
    "sl",  # Slovenian
    "sv",  # Swedish
    "tr",  # Turkish
}
SENTENCE_END_REGEX = r".!?…。！？؟؛।"
CLAUSE_END_TRIGGERS = r";,)\\]\"\’'\"`：—"


class ChunkingConfig(BaseModel):
    class Config:
        frozen = True
    """Pydantic model for chunking configuration validation"""
    lang: str = "auto"
    mode: Literal["sentence", "token", "hybrid"] = "sentence"
    max_tokens: Union[int, float] = Field(default=512)
    max_sentences: Union[int, float] = Field(default=100)
    overlap_percent: Union[int, float] = Field(default=10, ge=0, le=85)
    offset: int = Field(default=0, ge=0)
    verbose: bool = False
    use_cache: bool = True
    token_counter: Optional[Callable[[str], int]] = None

    @model_validator(mode='after')
    def validate_token_counter(self) -> 'ChunkingConfig':
        if self.mode in {"token", "hybrid"} and self.token_counter is None:
            raise ValueError("A token_counter is required for token-based chunking.")
        return self


class Chunklet:
    """
    Chunklet splits text into chunks by sentences or tokens with overlap applied
    on sentences and clauses within overlapping sentences using the same overlap_percent.
    """
    def __init__(
        self,
        verbose: bool = False,
        use_cache: bool = True,
        token_counter: Optional[Callable[[str], int]] = None,
    ):
        """
        Initialize Chunklet settings.

        Args:
            verbose (bool): Enable verbose logging.
            use_cache (bool): Enable caching on chunking.
            token_counter (Callable): Counts tokens in a sentence for token-based chunking.
        """
        self.verbose = verbose
        self.use_cache = use_cache
        self.token_counter = token_counter

        # Regex to split text into sentences by sentence-ending punctuation or newlines
        self.sentence_end_regex = re.compile(
            r"\n|(?<=[" + SENTENCE_END_REGEX + r"])\s*"
        )

        # Regex for acronyms to avoid splitting within them
        self.acronym_regex = re.compile(r"(\w|\d).\s?")

        # Regex for abbreviations like "Mr.", "Dr." to prevent wrong splits
        self.abbreviation_regex = re.compile(r"\b[A-Z][a-z]{0,3}.\.$")

        # Regex to detect text that is not a sentence end (helps avoid false positives)
        self.non_sentence_end_regex = re.compile(
            r"[^" + SENTENCE_END_REGEX + r"]*[a-z].*"
        )

        # Regex to split clauses inside sentences by clause-ending punctuation
        self.clause_end_regex = re.compile(r"(?<=[" + CLAUSE_END_TRIGGERS + r"])\s") 
        
    def _fallback_regex_splitter(self, text: str) -> List[str]:
        """
        Splits text into sentences using a regex-based approach as a fallback.
        Handles common sentence boundary issues like acronyms and abbreviations.

        Args:
            text (str): The input text to split.

        Returns:
            List[str]: A list of sentences.
        """
        # Initial split by sentence-ending punctuation
        sentences = self.sentence_end_regex.split(text)

        fixed_sentences = []
        sentences = [s.rstrip() for s in sentences if s.strip()]
        
        # Process each sentence to handle edge cases
        for i in range(len(sentences)):
            if i == 0:
                fixed_sentences.append(sentences[i])
                continue
            
            prev_sent = fixed_sentences[-1]
            curr_sent = sentences[i]

            # Handle cases where split might be incorrect:
            # 1. Single character fragments
            # 2. Acronyms/abbreviations
            # 3. False positive splits
            if (
                len(curr_sent) == 1
                or self.sentence_end_regex.match(curr_sent)
                or self.acronym_regex.fullmatch(curr_sent)
            ):
                fixed_sentences[-1] += curr_sent
            elif self.abbreviation_regex.search(
                prev_sent
            ) and self.non_sentence_end_regex.match(curr_sent):
                fixed_sentences[-1] += " " + curr_sent
            else:
                fixed_sentences.append(curr_sent)
        return fixed_sentences

    def _split_by_sentence(self, text: str, lang: str) -> List[str]:
        """
        Splits the given text into sentences based on the detected or specified language.
        Prioritizes `pysbd` for supported languages, falls back to `SentenceSplitter`
        for languages unique to it, and finally to a regex-based splitter.

        Args:
            text (str): The input text to split.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto').

        Returns:
            List[str]: A list of sentences.
        """
        if lang == "auto":
            lang_detected, confidence = detect_text_language(text)
            if confidence < 0.7 and self.verbose:
                logger.warning(
                    f"Low confidence in language detection: '{lang_detected}' ({confidence:.2f})."
                )
            lang = lang_detected if confidence > 0.7 else lang

        if lang in PYSBD_SUPPORTED_LANGUAGES:
            seg = Segmenter(language=lang)
            return seg.segment(text)

        if lang in SENTENCESPLITTER_UNIQUE_LANGUAGES:
            return SentenceSplitter(language=lang).split(text)

        if self.verbose:
            logger.warning(
                "Language not supported or detected with low confidence. Falling back to regex splitter."
            )
        return self._fallback_regex_splitter(text)

    def _get_overlap_clauses(
        self,
        prev_chunk: List,
        overlap_num: int,
    ) -> List[str]:
        """
        Extracts a specified number of clauses from the end of the previous chunk
        to create overlap for the next chunk.

        Args:
            prev_chunk (List): The previous chunk, consisting of a list of sentences.
            overlap_num (int): The number of clauses to extract for overlap.

        Returns:
            List[str]: A list of clauses to be used as overlap.
        """
        all_clauses = []
        for sent in prev_chunk:
            clauses = self.clause_end_regex.split(sent)
            all_clauses.extend(c.rstrip() for c in clauses if c.strip())

        overlapped_clauses = all_clauses[-overlap_num:]
        if overlapped_clauses and overlapped_clauses[0][0].islower():
            overlapped_clauses[0] = "... " + overlapped_clauses[0]
        return overlapped_clauses

    def group_by_chunk(
        self,
        sentences: List[str],
        config: ChunkingConfig,
    ) -> List[List[str]]:
        """
        Groups sentences into chunks based on the specified mode and constraints.
        Applies overlap logic between consecutive chunks.

        Args:
            sentences (List[str]): A list of sentences to be chunked.
            config (ChunkingConfig): Configuration for chunking.

        Returns:
            List[List[str]]: A list of chunks, where each chunk is a list of sentences.
        """
        chunks = []

        if config.mode == "sentence":
            overlap_num = round(config.max_sentences * config.overlap_percent / 100)
            stride = max(1, config.max_sentences - overlap_num)

            chunks.append(
                sentences[:config.max_sentences]
            )  # first chunk has no prev chunk for overlapping
            for idx in range(config.max_sentences, len(sentences), stride):
                curr_chunk = sentences[idx : idx + stride]
                overlap_clauses = []  # To prevent unbound local error.
                if overlap_num > 0:
                    overlap_clauses = self._get_overlap_clauses(chunks[-1], overlap_num)
                chunks.append(overlap_clauses + curr_chunk)
        else:
            curr_chunk = []
            token_count = 0
            sentence_count = 0
            for sentence in sentences:
                sentence_tokens = self.token_counter(sentence)
                if curr_chunk and (
                    token_count + sentence_tokens > config.max_tokens
                    or sentence_count + 1 > config.max_sentences
                ):
                    chunks.append(curr_chunk)  # chunk considered complete

                    # prepare data for next chunk
                    overlap_num = round(len(curr_chunk) * config.overlap_percent / 100)
                    curr_chunk = self._get_overlap_clauses(curr_chunk, overlap_num)

                    # treat them as sentence
                    token_count = sum(self.token_counter(s) for s in curr_chunk)
                    sentence_count = len(curr_chunk)
                curr_chunk.append(sentence)
                token_count += sentence_tokens
                sentence_count += 1
            if curr_chunk:
                chunks.append(curr_chunk)
        return ["\n".join(chunk) for chunk in chunks]

    def _chunk(
        self,
        text: str,
        lang: str = "auto",
        mode: str = "sentence",
        max_tokens: int = 512,
        max_sentences: int = 100,
        overlap_percent: Union[int, float] = 10,
        offset: int = 0,
        token_counter: Optional[Callable[[str], int]] = None,
    ) -> List[str]:
        """
        Internal method to chunk a given text based on specified parameters.
        Performs validation and orchestrates sentence splitting and chunk grouping.

        Args:
            text (str): The input text to chunk.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto').
            mode (str): Chunking mode ('sentence', 'token', or 'hybrid').
            max_tokens (int): Maximum number of tokens per chunk.
            max_sentences (int): Maximum number of sentences per chunk.
            overlap_percent (Union[int, float]): Percentage of overlap between chunks (0-85).
            offset (int): Starting sentence offset for chunking.
            token_counter (Optional[Callable[[str], int]]): callable that takes a string
                (sentence) and returns its token count. Required for token-based chunking
                if default token_counter is not set in init.

        Returns:
            List[str]: A list of text chunks.

        Raises:
            ValidationError: If any of the input parameters are invalid.
        """
        if not text:
            return []

        # Adjust limits based on mode
        if mode == "sentence":
            max_tokens = math.inf
        elif mode == "token":
            max_sentences = math.inf

        # Validate all parameters through ChunkingConfig
        config = ChunkingConfig(
            lang=lang,
            mode=mode,
            max_tokens=max_tokens,
            max_sentences=max_sentences,
            overlap_percent=overlap_percent,
            offset=offset,
            token_counter=token_counter if token_counter is not None else self.token_counter,
        )

        sentences = self._split_by_sentence(text, config.lang)
        if not sentences:
            return []
        
        offset = round(config.offset)
        if offset >= len(sentences):
            logger.warning(
                f"Offset {offset} >= total sentences {len(sentences)}. Returning empty list."
            )
            return []

        sentences = sentences[offset:]
        chunks = self.group_by_chunk(
            sentences, config
        )
        return chunks

    @lru_cache(maxsize=25)
    def _chunk_cached(
        self,
        text: str,
        lang: str = "auto",
        mode: str = "sentence",
        max_tokens: int = 512,
        max_sentences: int = 100,
        overlap_percent: Union[int, float] = 10,
        offset: int = 0,
        token_counter: Optional[Callable[[str], int]] = None,
    ) -> List[str]:
        """
        Cached version of the `_chunk` method. Uses LRU cache for performance.

        Args:
            text (str): The input text to chunk.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto').
            mode (str): Chunking mode ('sentence', 'token', or 'hybrid').
            max_tokens (int): Maximum number of tokens per chunk.
            max_sentences (int): Maximum number of sentences per chunk.
            overlap_percent (Union[int, float]): Percentage of overlap between chunks (0-85).
            offset (int): Starting sentence offset for chunking.
            token_counter (Optional[Callable[[str], int]]): callable that takes a string
                (sentence) and returns its token count.

        Returns:
            List[str]: A list of text chunks.
        """
        return self._chunk(
            text=text,
            lang=lang,
            mode=mode,
            max_tokens=max_tokens,
            max_sentences=max_sentences,
            overlap_percent=overlap_percent,
            offset=offset,
            token_counter=token_counter,
        )

    def chunk(
        self,
        text: str,
        *,
        lang: str = "auto",
        mode: str = "sentence",
        max_tokens: int = 512,
        max_sentences: int = 100,
        overlap_percent: Union[int, float] = 10,
        offset: int = 0,
        token_counter: Optional[Callable[[str], int]] = None,
    ) -> List[str]:
        """
        Chunks a single text into smaller pieces based on the specified parameters.

        Args:
            text (str): The input text to chunk.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto'). Defaults to "auto".
            mode (str): Chunking mode ('sentence', 'token', or 'hybrid'). Defaults to "sentence".
            max_tokens (int): Maximum number of tokens per chunk. Defaults to 512.
            max_sentences (int): Maximum number of sentences per chunk. Defaults to 100.
            overlap_percent (Union[int, float]): Percentage of overlap between chunks (0-85).
                Defaults to 10.
            offset (int): Starting sentence offset for chunking. Defaults to 0.

        Returns:
            List[str]: A list of text chunks.
        """
        if self.use_cache:
            return self._chunk_cached(
                text=text,
                lang=lang,
                mode=mode,
                max_tokens=max_tokens,
                max_sentences=max_sentences,
                overlap_percent=overlap_percent,
                offset=offset,
                token_counter=token_counter if token_counter is not None else self.token_counter,
            )
        return self._chunk(
            text=text,
            lang=lang,
            mode=mode,
            max_tokens=max_tokens,
            max_sentences=max_sentences,
            overlap_percent=overlap_percent,
            offset=offset,
            token_counter=token_counter if token_counter is not None else self.token_counter,
        )

    def batch_chunk(
        self,
        texts: List[str],
        *,
        lang: str = "auto",
        mode: str = "sentence",
        max_tokens: int = 512,
        max_sentences: int = 100,
        overlap_percent: Union[int, float] = 20,
        offset: int = 0,
        n_jobs: Optional[int] = None,
        token_counter: Optional[Callable[[str], int]] = None,
        verbose: bool = False,
    ) -> List[List[str]]:
        """
        Process a batch of texts in parallel, splitting each into chunks according to specified parameters.
        
        Args:
            texts: List of input texts to be chunked. Each text will be processed independently.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto'). Defaults to "auto".
            mode (str): Chunking mode ('sentence', 'token', or 'hybrid'). Defaults to "sentence".
            max_tokens (int): Maximum number of tokens per chunk. Defaults to 512.
            max_sentences (int): Maximum number of sentences per chunk. Defaults to 100.
            overlap_percent (Union[int, float]): Percentage of overlap between chunks (0-85).
                Defaults to 10.
            offset (int): Starting sentence offset for chunking. Defaults to 0.
            n_jobs: Number of parallel workers to use. If None, uses all available CPUs.
                   Must be >= 1 if specified.
            token_counter: Optional token counting function. Required for token-based modes.
            verbose: Enable verbose logging.

        Returns:
            A list of lists, where each inner list contains the chunks for the corresponding input text.
            The order of texts is preserved in the output.
        """
        if not texts:
            return []

        # Validate n_jobs parameter
        if n_jobs is not None and n_jobs < 1:
            raise ValueError("n_jobs must be >= 1 or None")

        with concurrent.futures.ThreadPoolExecutor(max_workers=n_jobs) as executor:
            results = list(
                executor.map(
                    lambda text: self._chunk(
                        text=text,
                        lang=lang,
                        mode=mode,
                        max_tokens=max_tokens,
                        max_sentences=max_sentences,
                        overlap_percent=overlap_percent,
                        offset=offset,
                        token_counter=token_counter if token_counter is not None else self.token_counter,
                    ),
                    texts,
                )
            )
        return results

    def preview_sentences(self, text: str, lang: str = "auto") -> List[str]:
        """
        Splits a text into sentences and returns them, useful for previewing.

        Args:
            text (str): The input text to split into sentences.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto'). Defaults to "auto".

        Returns:
            List[str]: A list of sentences from the input text.
        """
        return self._split_by_sentence(text, lang)