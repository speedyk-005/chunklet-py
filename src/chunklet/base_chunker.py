"""
Base Chunker Abstract Class

Defines the interface for chunkers.
"""

from abc import ABC, abstractmethod
from typing import Generator
from box import Box
from loguru import logger


class BaseChunker(ABC):
    """
    Abstract base class for chunkers.

    Defines the standard interface for chunking content into units.
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    @abstractmethod
    def chunk(self, *args, **kwargs) -> list[Box]:
        """
        Extract chunks.

        Returns:
            list[Box]: List of chunks with content and metadata.
        """
        pass

    @abstractmethod
    def batch_chunk(self, *args, **kwargs) -> Generator[Box, None, None]:
        """
        Process multiple items in parallel.

        Yields:
            Box: `Box` object, representing a chunk with its content and metadata.
        """
        pass

    def log_info(self, *args, **kwargs) -> None:
        """Log an info message if verbose is enabled."""
        if self.verbose:
            logger.info(*args, **kwargs)
