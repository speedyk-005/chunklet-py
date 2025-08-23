class ChunkletError(Exception):
    """Base class for all Chunklet-specific errors."""

    pass


class InvalidInputError(ChunkletError):
    """Base class for invalid input errors."""

    def __init__(self, message="Invalid input provided."):
        self.message = message
        super().__init__(self.message)


class TokenNotProvidedError(ChunkletError):
    """Raised when a token_counter is required but not provided."""

    def __init__(self):
        super().__init__("A token_counter is required for token-based chunking.")
