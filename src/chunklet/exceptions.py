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
    pass

class UnsupportedFileTypeError(InvalidInputError):
    """Raised when a file type is not supported for a given operation."""
    pass

class TokenLimitError(ChunkletError):
    """Raised when max_tokens constraint is exceeded."""
    pass

class FileProcessingError(ChunkletError):
    """Raised when a file cannot be loaded, opened, or
accessed."""
    pass

class CallbackExecutionError(ChunkletError):
    """Raised when a callback function provided to chunker
or splitter fails during execution."""
    pass