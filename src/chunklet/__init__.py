"""
Chunklet: Multi_strategy, Context-aware, Multilingual Text Chunker

This package provides a robust and flexible solution for splitting large texts
into smaller, manageable chunks. It is designed with applications like Large
Language Models (LLMs), Retrieval-Augmented Generation (RAG) pipelines, and
other context-aware Natural Language Processing (NLP) tasks in mind.

The core functionality is provided by the `Chunklet` class, which can be
imported directly from the package alongside execptions and schemas models.
"""

from .plain_text_chunker import PlainTextChunker
from .document_chunker import DocumentChunker
from .exceptions import ChunkletError, InvalidInputError, TokenNotProvidedError
from .models import (
    CustomSplitterConfig,
    PlainTextChunkerConfig,
    CustomProcessorConfig,
    ChunkingConfig
)
from .utils import (
    DOCXProcessor,
    PDFProcessor,
    rst_to_markdown,
    UniversalSplitter,
    detect_text_language,
)

__version__ = "2.0.0"

__all__ = [
    "PlainTextChunker",
    "DocumentChunker",
    "ChunkletError",
    "InvalidInputError",
    "TokenNotProvidedError",
    "DOCXProcessor",
    "PDFProcessor",
    "rst_to_markdown",
    "UniversalSplitter",
    "detect_text_language",
]
