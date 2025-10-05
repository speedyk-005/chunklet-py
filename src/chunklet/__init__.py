"""
Chunklet: Multi_strategy, Context-aware, Multilingual Text Chunker

This package provides a robust and flexible solution for splitting large texts
into smaller, manageable chunks. It is designed with applications like Large
Language Models (LLMs), Retrieval-Augmented Generation (RAG) pipelines, and
other context-aware Natural Language Processing (NLP) tasks in mind.

The core functionality is provided by the `Chunklet` class, which can be
imported directly from the package alongside execptions.
"""

from .sentence_splitter import SentenceSplitter
from .plain_text_chunker import PlainTextChunker
from .document_chunker import DocumentChunker
# from .code_chunker import CodeChunker
from .exceptions import (
    ChunkletError,
    InvalidInputError,
    MissingTokenCounterError,
    UnsupportedFileTypeError,
    TokenLimitError,
    FileProcessingError,
    CallbackExecutionError,
)

__version__ = "2.0.0"

__all__ = [
    "SentenceSplitter",
    "PlainTextChunker",
    "DocumentChunker",
    #"CodeChunker",
    "CodeChunker",
    "ChunkletError",
    "InvalidInputError",
    "MissingTokenCounterError",
    "UnsupportedFileTypeError",
    "TokenLimitError",
    "FileProcessingError",
    "CallbackExecutionError",
]
