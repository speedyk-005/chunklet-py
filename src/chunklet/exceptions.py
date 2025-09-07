class ChunkletError(Exception):
    """Base class for all Chunklet-specific errors."""

    pass


class InvalidInputError(ChunkletError):
    """Base class for invalid input errors."""

    def __init__(self, message="Invalid input provided."):
        self.message = message
        super().__init__(self.message)


class TokenCounterMissingError(ChunkletError):
    """Raised when a token_counter is required but not provided."""

    def __init__(self):
        super().__init__("A token_counter is required for token-based chunking.")


class FileProcessingError(ChunkletError):
    """Raised when an error occurs during file reading or processing."""

    def __init__(self, message="Error processing file."):
        self.message = message
        super().__init__(self.message)


class UnsupportedFileTypeError(InvalidInputError):
    """Raised when a file type is not supported for a given operation."""

    def __init__(self, message="Unsupported file type."):
        self.message = message
        super().__init__(self.message)
