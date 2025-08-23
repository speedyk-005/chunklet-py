"""
Chunklet: Multi_strategy, Context-aware, Multilingual Text Chunker

This package provides a robust and flexible solution for splitting large texts
into smaller, manageable chunks. It is designed with applications like Large
Language Models (LLMs), Retrieval-Augmented Generation (RAG) pipelines, and
other context-aware Natural Language Processing (NLP) tasks in mind.

The core functionality is provided by the `Chunklet` class, which can be
imported directly from the package alongside execptions and schemas models.
"""

from .core import Chunklet
from .exceptions import ChunkletError, InvalidInputError, TokenNotProvidedError
from .models import CustomSplitterConfig, ChunkletInitConfig, ChunkingConfig

__all__ = [
    "Chunklet",
    "ChunkletError",
    "InvalidInputError",
    "TokenNotProvidedError",
]