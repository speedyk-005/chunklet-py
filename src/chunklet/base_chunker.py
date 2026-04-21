"""
Base Chunker Abstract Class

Defines the interface for chunkers.
"""

from abc import ABC, abstractmethod
from collections.abc import Generator

from dotdict3 import DotDict
from loguru import logger


class BaseChunker(ABC):
    """
    Abstract base class for chunkers.

    Defines the standard interface for chunking content into units.
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    @abstractmethod
    def chunk_text(self, *args, **kwargs) -> list[DotDict]:
        """
        Extract chunks from text.

        Returns:
            list[DotDict] List of chunks with content and metadata.
        """
        pass

    @abstractmethod
    def chunk_texts(self, *args, **kwargs) -> list[list[DotDict]]:
        """
        Process multiple texts.

        Returns:
            list[list[DotDict]] List of chunks for each input text.
        """
        pass

    @abstractmethod
    def chunk_file(self, *args, **kwargs) -> list[DotDict]:
        """
        Read and chunk a file.

        Returns:
            list[DotDict] List of chunks with content and metadata.
        """
        pass

    @abstractmethod
    def chunk_files(self, *args, **kwargs) -> Generator[DotDict, None, None]:
        """
        Process multiple files.

        Yields:
            DotDict `DotDict` object, representing a chunk with its content and metadata.
        """
        pass
