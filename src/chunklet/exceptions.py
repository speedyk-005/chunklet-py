class ChunkletError(Exception):
    """Base class for all Chunklet-specific errors."""

    pass


class InvalidInputError(ChunkletError):
    """Raised when an input is invalid."""

    pass


class MissingTokenCounterError(ChunkletError):
    """Raised when a token_counter is required but not provided."""

    def __init__(self):
        super().__init__(
            "A `token_counter` function is required for 'token' or 'hybrid' chunking modes.\n"
            "💡 Hint: Pass a token counting function to the `chunk` method, like `chunker.chunk(..., token_counter=len)`\n"
            "or configure it in the class initialization: `Chunker(token_counter=...)`"
        )


class UnsupportedFileTypeError(InvalidInputError):
    """Raised when a file type is not supported for a given operation."""

    pass


class FileProcessingError(ChunkletError):
    """Raised when an error occurs during file reading or processing."""

    pass


class TextProcessingError(ChunkletError):
    """Raised when an error occurs during text processing."""

    pass
