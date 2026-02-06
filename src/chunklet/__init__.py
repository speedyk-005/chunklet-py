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

import importlib
import typing

from .exceptions import (
    ChunkletError,
    InvalidInputError,
    MissingTokenCounterError,
    UnsupportedFileTypeError,
    TokenLimitError,
    FileProcessingError,
    CallbackError,
)

__version__ = "2.2.0"

__all__ = [
    "ChunkletError",
    "InvalidInputError",
    "MissingTokenCounterError",
    "UnsupportedFileTypeError",
    "TokenLimitError",
    "FileProcessingError",
    "CallbackError",
    "SentenceSplitter",
    "DocumentChunker",
    "CodeChunker",
    "PlainTextChunker",
    "Visualizer",
]


# Map the public names to their sub-module locations
_LOOKUP = {
    "SentenceSplitter": "chunklet.sentence_splitter",
    "DocumentChunker": "chunklet.document_chunker",
    "CodeChunker": "chunklet.code_chunker",
    "PlainTextChunker": "chunklet.plain_text_chunker",
    "Visualizer": "chunklet.visualizer",
}

def __getattr__(name: str) -> typing.Any:
    """Dynamically imports and returns chunking components when accessed.
    
    This function implements lazy loading for chunking components. When a user
    accesses an attribute that isn't directly defined in this module, Python calls
    this function to resolve the attribute.
    
    Args:
        name: The name of the attribute being accessed (e.g., "DocumentChunker", "CodeChunker").
        
    Returns:
        The requested chunking component from its respective submodule.

    Raises:
        AttributeError: If the requested component is not found in _LOOKUP.
        
    Example:
        >>> from chunklet import DocumentChunker
        >>> chunker = DocumentChunker()
        >>> # Component is imported only when accessed
    """
    if name in _LOOKUP:
        module = importlib.import_module(_LOOKUP[name], __package__)
        return getattr(module, name)
    
    raise AttributeError(f"module {__name__} has no attribute {name}")

# Optional: Helping IDEs with autocompletion
def __dir__():
    return sorted(list(globals().keys()) + list(_LOOKUP.keys()))
