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

Note:
    PlainTextChunker has been merged into DocumentChunker since v2.2.0.
    Use DocumentChunker.chunk_text() or DocumentChunker.chunk_texts() instead.
"""

import importlib
import sys
import types
import typing
import warnings
from importlib.metadata import PackageNotFoundError, version

from chunklet.common.deprecation import deprecated_callable

try:
    __version__ = version("chunklet-py")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

from .exceptions import (
    CallbackError,
    ChunkletError,
    FileProcessingError,
    InvalidInputError,
    MissingTokenCounterError,
    TokenLimitError,
    UnsupportedFileTypeError,
)

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
    "PlainTextChunker",  # Kept for backward compatibility
    "Visualizer",
]


# Map the public names to their sub-module locations
_LOOKUP = {
    "SentenceSplitter": "chunklet.sentence_splitter",
    "PlainTextChunker": "chunklet.plain_text_chunker",
    "DocumentChunker": "chunklet.document_chunker",
    "CodeChunker": "chunklet.code_chunker",
    "Visualizer": "chunklet.visualizer",
}


class _PlainTextChunkerModuleProxy(types.ModuleType):
    """Proxy module for backward compatibility.

    This proxy intercepts attribute access to show a deprecation warning
    when accessing PlainTextChunker via the old import path.
    """

    def __init__(self):
        super().__init__("chunklet.plain_text_chunker")
        self._PlainTextChunker: typing.Any = None

    def _get_deprecated_class(self):
        if self._PlainTextChunker is None:
            from chunklet.document_chunker._plain_text_chunker import PlainTextChunker

            self._PlainTextChunker = deprecated_callable(
                use_instead="chunklet.DocumentChunker.chunk_text and chunk_texts",
                deprecated_in="2.2.0",
                removed_in="3.0.0",
            )(PlainTextChunker)
        return self._PlainTextChunker

    def __getattr__(self, name: str) -> typing.Any:
        return self._get_deprecated_class()

    def __dir__(self):
        return dir(self._get_deprecated_class())


# Register proxy in sys.modules for backward compatibility
sys.modules["chunklet.plain_text_chunker"] = _PlainTextChunkerModuleProxy()


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
    """
    if name in _LOOKUP:
        module = importlib.import_module(_LOOKUP[name], __package__)
        return getattr(module, name)

    raise AttributeError(f"module {__name__} has no attribute {name}")


# Optional: Helping IDEs with autocompletion
def __dir__():
    return sorted(list(globals().keys()) + list(_LOOKUP.keys()))
