"""
Chunklet: Advanced Text, Code, and Document Chunking for LLM Applications

A comprehensive library for semantic text segmentation, interactive chunk visualization,
and multi-format document processing. Split content intelligently across 50+ languages,
visualize chunks in real-time, and handle various file types with flexible,
context-aware chunking strategies.

Key Features:
- Sentence splitting: Multilingual text segmentation across 50+ languages
- Semantic chunking: PlainTextChunker, DocumentChunker, and CodeChunker
- Interactive visualization: Web-based chunk exploration and parameter tuning
- Multi-format support: Text, code, PDF, DOCX, EPUB, and more
- Batch processing: Memory-optimized generators with flexible error handling
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

__version__ = "2.1.1"

__all__ = [
    "ChunkletError",
    "InvalidInputError",
    "MissingTokenCounterError",
    "UnsupportedFileTypeError",
    "TokenLimitError",
    "FileProcessingError",
    "CallbackError",
]
