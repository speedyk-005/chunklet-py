"""
Chunklet: The v2.0.0 Evolution - Multi-strategy, Context-aware, Multilingual Text & Code Chunker

This package provides a robust and flexible solution for splitting large texts
and code into smaller, manageable chunks. Designed for applications like Large
Language Models (LLMs), Retrieval-Augmented Generation (RAG) pipelines, and
other context-aware Natural Language Processing (NLP) tasks.

Version 2.0.0 introduces a revamped architecture with:
- Dedicated chunkers: `PlainTextChunker` (formerly `Chunklet`), `DocumentChunker`, and `CodeChunker`.
- Expanded language support (50+ languages) and improved error handling.
- Flexible batch processing with `on_errors` parameter and memory-optimized generators.
- Enhanced modularity, extensibility, and performance.
"""
from .exceptions import (
    ChunkletError,
    InvalidInputError,
    MissingTokenCounterError,
    UnsupportedFileTypeError,
    TokenLimitError,
    FileProcessingError,
    CallbackError,
)

__version__ = "2.0.0"

__all__ = [
    "ChunkletError",
    "InvalidInputError",
    "MissingTokenCounterError",
    "UnsupportedFileTypeError",
    "TokenLimitError",
    "FileProcessingError",
    "CallbackError",
]
