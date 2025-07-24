"""
Chunklet: A Smart Multilingual Text Chunker

This package provides a robust and flexible solution for splitting large texts
into smaller, manageable chunks. It is designed with applications like Large
Language Models (LLMs), Retrieval-Augmented Generation (RAG) pipelines, and
other context-aware Natural Language Processing (NLP) tasks in mind.

Key Features:
- Multiple Chunking Modes: Supports splitting by sentence count, token count,
  or a hybrid approach that combines both for optimal chunk sizing.
- Clause-Level Overlap: Ensures semantic continuity between chunks by
  implementing overlap at natural clause boundaries (e.g., commas, semicolons).
- Multilingual Support: Automatically detects language and utilizes appropriate
  splitting algorithms (CRF-based, Moses, or a smart regex fallback) for
  over 30 languages.
- Pluggable Token Counters: Allows users to integrate custom token counting
  functions (e.g., for specific LLM tokenizers like GPT-2).
- Parallel Processing: Efficiently handles batch chunking of multiple texts
  using multiprocessing for improved performance.
- Caching: Implements LRU caching to speed up repeated chunking operations
  with the same parameters.

The core functionality is provided by the `Chunklet` class, which can be
imported directly from the package.

Example Usage:
>>> from chunklet import Chunklet
>>> chunker = Chunklet()
>>> text = "This is a long document. It has multiple sentences. And more."
>>> chunks = chunker.chunk(text, max_sentences=2, overlap_percent=10)
>>> for chunk in chunks:
...     print(chunk)
"""

from .core import Chunklet

__version__ = "1.0.4"
