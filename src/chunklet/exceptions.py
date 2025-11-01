class ChunkletError(Exception):
    """Base exception for chunking and splitting
    operations."""

    pass


class InvalidInputError(ChunkletError):
    """Raised when one or multiple invalid input(s) are
    encountered."""

    pass


class MissingTokenCounterError(InvalidInputError):
    """Raised when a token_counter is required but not
    provided."""

    def __init__(self, msg: str = ""):
        self.msg = msg or (
            "A token_counter is required for token-based chunking.\n"
            "💡 Hint: Pass a token counting function to the `chunk` method, like `chunker.chunk(..., token_counter=tk)`\n"
            "or configure it in the class initialization: `.*Chunker(token_counter=tk)`"
        )
        super().__init__(self.msg)


class FileProcessingError(ChunkletError):
    """Raised when a file cannot be loaded, opened, or
    accessed."""

    pass


class UnsupportedFileTypeError(FileProcessingError):
    """Raised when a file type is not supported for a given operation."""

    pass


class TokenLimitError(ChunkletError):
    """Raised when max_tokens constraint is exceeded."""

    pass


class CallbackError(ChunkletError):
    """Raised when a callback function provided to chunker
    or splitter fails during execution."""

    pass
