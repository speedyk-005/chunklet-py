import sys
import re
import math
from functools import lru_cache
from typing import List, Callable, Optional, Union
from loguru import logger
from langid.langid import LanguageIdentifier, model
from sentence_splitter import SentenceSplitter
from sentsplit.segment import SentSplit
from mpire import WorkerPool

# Setup Loguru logger: remove default, add filtered stderr sink
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    filter=lambda record: "sentsplit" not in record["name"],  # exclude sentsplit logs
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <cyan>{name}</cyan> | <level>{message}</level>"
)

LANGS_SENT_SPLIT = {
    "en", "fr", "de", "it", "pl", "pt", "lt", "ja", "ko", "ru", "zh", "tr"
}

LANGS_MOSES = {
    "ca", "cs", "da", "el", "es", "fi", "hu", "is", "lv",
    "nl", "no", "ro", "sk", "sl", "sv"
}

SENTENCE_END_REGEX = r".!?…。！？؟؛।"
CLAUSE_END_TRIGGERS = r";,)\]\”\’'\"`：—"

class Chunklet:
    """
    Chunklet splits text into chunks by sentences or tokens with overlap applied
    on sentences and clauses within overlapping sentences using the same overlap_percent.
    """

    def __init__(
        self,
        verbose: bool = True,
        use_cache: bool = False,
        token_counter: Optional[Callable[[str], int]] = None,
    ):
        self.verbose = verbose
        self.use_cache = use_cache
        self.token_counter = token_counter
        self._language_identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)
        self.sentence_end_regex = re.compile(r"\n|(?<=[" + SENTENCE_END_REGEX + r"])\s*")
        self.acronym_regex = re.compile(r"(\w|\d).\s?")
        self.abbreviation_regex = re.compile(r"\b[A-Z][a-z]{0,3}\.$")
        self.non_sentence_end_regex = re.compile(r"[^" + SENTENCE_END_REGEX + r"]*[a-z].*")
        self.clause_end_regex = re.compile(r"(?<=[" + CLAUSE_END_TRIGGERS + r"])\s")

    @staticmethod
    def _static_chunk_helper(
        text, lang, mode, max_tokens, max_sentences, token_counter, overlap_percent, offset
    ) -> List[str]:
        temp_chunker = Chunklet(verbose=False, use_cache=False, token_counter=token_counter)
        return temp_chunker._chunk(
            text=text,
            lang=lang,
            mode=mode,
            max_tokens=max_tokens,
            max_sentences=max_sentences,
            overlap_percent=overlap_percent,
            offset=offset,
        )

    def _fallback_regex_splitter(self, text: str) -> List[str]:
        sentences = self.sentence_end_regex.split(text)

        fixed_sentences = []
        sentences = [s.rstrip() for s in sentences if s.strip()]
        for i in range(len(sentences)):
            if i == 0:
                fixed_sentences.append(sentences[i])
                continue
            prev_sent = fixed_sentences[-1]
            curr_sent = sentences[i]
            if (
                len(curr_sent) == 1
                or self.sentence_end_regex.match(curr_sent)
                or self.acronym_regex.fullmatch(curr_sent)
            ):
                fixed_sentences[-1] += curr_sent
            elif (
                self.abbreviation_regex.search(prev_sent)
                and self.non_sentence_end_regex.match(curr_sent)
            ):
                fixed_sentences[-1] += " " + curr_sent
            else:
                fixed_sentences.append(curr_sent)
        return fixed_sentences

    def _split_by_sentence(self, text: str, lang: str) -> List[str]:
        if lang == "auto":
            lang_detected, confidence = self._language_identifier.classify(text)
            if confidence < 0.7 and self.verbose:
                logger.warning(
                    f"Low confidence in language detection: '{lang_detected}' ({confidence:.2f})."
                )
            lang = lang_detected if confidence > 0.7 else lang

        if lang in LANGS_SENT_SPLIT:
            raw_sentences = SentSplit(lang).segment(text)
            return [s.rstrip("\n") for s in raw_sentences if s.strip()]

        if lang in LANGS_MOSES:
            return SentenceSplitter(language=lang).split(text)       
           
        if self.verbose:
            logger.warning(
                "Language not supported or detected with low confidence. Falling back to regex splitter."
            )
        return self._fallback_regex_splitter(text)      

    def _get_overlap_clauses(
        self, prev_chunk: List,  overlap_num: int,
    ) -> List[str]:
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
        mode: str,
        max_tokens: int,
        max_sentences: int,
        overlap_percent: Union[int, float],
    ) -> List[List[str]]:
        chunks = []   
             
        if mode == "sentence":
            overlap_num = round(max_sentences * overlap_percent / 100)
            stride = max(1, max_sentences - overlap_num)   
            
            chunks.append(sentences[:max_sentences]) # first chunk has no prev chunk for overlapping                            
            for idx in range(max_sentences, len(sentences), stride):
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
                    token_count + sentence_tokens > max_tokens
                    or sentence_count + 1 > max_sentences
                ):
                    chunks.append(curr_chunk)  # chunk considered complete
                    
                    # prepare data for next chunk                                                                               
                    overlap_num = round(len(curr_chunk) * overlap_percent / 100)
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
        lang: str,
        mode: str,
        max_tokens: int,
        max_sentences: int,
        overlap_percent: Union[int, float],
        offset: int,
    ) -> List[str]:
        if not text:
            return []
        if not (0 <= overlap_percent <= 85):
            raise ValueError("overlap_percent must be between 0 and 85")
        if max_sentences < 1:
            raise ValueError("max_sentences must be at least 1")
        if max_tokens < 1:
            raise ValueError("max_tokens must be at least 1")
        if mode not in {"sentence", "token", "hybrid"}:
            raise ValueError("Invalid mode. Choose from 'sentence', 'token', or 'hybrid'.")
        if mode in {"token", "hybrid"} and self.token_counter is None:
            raise ValueError("A token_counter is required for token-based chunking.")
        if mode == "sentence":
            max_tokens = math.inf
        elif mode == "token":
            max_sentences = math.inf
            
        sentences  = self._split_by_sentence(text, lang)                
        if not sentences:
            return []
        if max_sentences == 1 and mode == "sentence":
            return sentences
            
        offset = round(offset)
        if offset >= len(sentences):
            if self.verbose:
                logger.warning(
                    f"Offset {offset} >= total sentences {len(sentences)}. Returning empty list."
                )
            return []
            
        sentences = sentences[offset:]        
        chunks = self.group_by_chunk(sentences, mode, max_tokens, max_sentences, overlap_percent)
        return chunks
        
    @lru_cache(maxsize=25)
    def _chunk_cached(
        self,
        text: str,
        lang: str,
        mode: str,
        max_tokens: int,
        max_sentences: int,
        overlap_percent: Union[int, float],
        offset: int,
    ) -> List[str]:
        return self._chunk(
            text=text,
            lang=lang,
            mode=mode,
            max_tokens=max_tokens,
            max_sentences=max_sentences,
            overlap_percent=overlap_percent,
            offset=offset,
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
    ) -> List[str]:
        if self.use_cache:
            return self._chunk_cached(
                text=text,
                lang=lang,
                mode=mode,
                max_tokens=max_tokens,
                max_sentences=max_sentences,
                overlap_percent=overlap_percent,
                offset=offset,
            )
        return self._chunk(
            text=text,
            lang=lang,
            mode=mode,
            max_tokens=max_tokens,
            max_sentences=max_sentences,
            overlap_percent=overlap_percent,
            offset=offset,
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
    ) -> List[List[str]]:
        if not texts:
            return []

        args = [
            (
                text,
                lang,
                mode,
                max_tokens,
                max_sentences,
                self.token_counter,
                overlap_percent,
                offset,
            )
            for text in texts
        ]

        with WorkerPool(n_jobs=n_jobs) as pool:
            results = pool.map(self._static_chunk_helper, args)
        return results

    def preview_sentences(self, text: str, lang: str = "auto") -> List[str]:
        return self._split_by_sentence(text, lang)(text)


def simple_token_counter(text: str) -> int:
    return len(text.split())

def main():
    import argparse
    import textwrap

    parser = argparse.ArgumentParser(
        description="Chunklet: Smart Multilingual Text Chunker for LLMs, RAG, and beyond.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "text",
        nargs="?",
        help="The input text to chunk. If not provided, --file must be used."
    )
    parser.add_argument(
        "--file",
        help="Path to a text file to read input from. Overrides the 'text' argument."
    )
    parser.add_argument(
        "--output-file",
        help="Path to a file to write the output chunks to. If not provided, output is printed to stdout."
    )
    parser.add_argument(
        "--mode",
        choices=["sentence", "token", "hybrid"],
        default="sentence",
        help="Chunking mode: 'sentence', 'token', or 'hybrid'. (default: sentence)"
    )
    parser.add_argument(
        "--lang",
        default="auto",
        help="Language of the text (e.g., 'en', 'fr', 'auto'). (default: auto)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=512,
        help="Maximum number of tokens per chunk. (default: 512)"
    )
    parser.add_argument(
        "--max-sentences",
        type=int,
        default=100,
        help="Maximum number of sentences per chunk. (default: 100)"
    )
    parser.add_argument(
        "--overlap-percent",
        type=float,
        default=10,
        help="Percentage of overlap between chunks (0-85). (default: 10)"
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Starting sentence offset for chunking. (default: 0)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable LRU caching."
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process input as a list of texts for batch chunking (requires --file with one text per line)."
    )
    parser.add_argument(
        "--n-jobs",
        type=int,
        default=None,
        help="Number of parallel jobs for batch chunking. (default: None, uses all available cores)"
    )

    args = parser.parse_args()

    if not args.text and not args.file:
        parser.error("Either 'text' argument or '--file' must be provided.")
    if args.batch and not args.file:
        parser.error("Batch mode (--batch) requires input from a file (--file).")

    input_texts = []
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            if args.batch:
                input_texts = [line.strip() for line in f if line.strip()]
            else:
                input_texts = [f.read()]
    elif args.text:
        input_texts = [args.text]

    chunker = Chunklet(
        verbose=args.verbose,
        use_cache=not args.no_cache,
        token_counter=simple_token_counter
    )

    results = []
    if args.batch:
        results = chunker.batch_chunk(
            texts=input_texts,
            lang=args.lang,
            mode=args.mode,
            max_tokens=args.max_tokens,
            max_sentences=args.max_sentences,
            overlap_percent=args.overlap_percent,
            offset=args.offset,
            n_jobs=args.n_jobs
        )
    else:
        # For single text, chunk returns a list of strings
        results = [chunker.chunk(
            text=input_texts[0],
            lang=args.lang,
            mode=args.mode,
            max_tokens=args.max_tokens,
            max_sentences=args.max_sentences,
            overlap_percent=args.overlap_percent,
            offset=args.offset
        )] # Wrap in a list to match batch output structure for consistent printing

    output_content = []
    for i, doc_chunks in enumerate(results):
        if args.batch:
            output_content.append(f"## Document {i+1}")
        for j, chunk in enumerate(doc_chunks):
            output_content.append(f"--- Chunk {j+1} ---")
            output_content.append(chunk)
        output_content.append("") # Add a newline between documents/single chunk outputs

    output_str = "\n".join(output_content)

    if args.output_file:
        with open(args.output_file, "w", encoding="utf-8") as f:
            f.write(output_str)
    else:
        print(output_str)

if __name__ == "__main__":
    main()
