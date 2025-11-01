from abc import ABC, abstractmethod
from typing import Any, Generator


class BaseProcessor(ABC):
    """
    Abstract base class for document processors, providing a unified interface
    for extracting text and metadata from documents.
    """

    def __init__(self, file_path: str):
        """
        Initializes the processor with the path to the document.

        Args:
            file_path (str): Path to the document file.
        """
        self.file_path = file_path

    @abstractmethod
    def extract_metadata(self) -> dict[str, Any]:
        """
        Extracts metadata from the document.

        Returns:
            dict[str, Any]: Dictionary containing document metadata.
        """
        pass

    @abstractmethod
    def extract_text(self) -> Generator[str, None, None]:
        """
        Yields text content from the document.

        Yields:
            str: Text content chunks from the document.
        """
        pass
