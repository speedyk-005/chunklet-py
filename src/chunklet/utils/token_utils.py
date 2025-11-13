from typing import Callable
from functools import lru_cache
from chunklet.exceptions import CallbackError


@lru_cache(maxsize=1024)
def count_tokens(text: str, token_counter: Callable[[str], int]) -> int:
    """
    Count tokens in a string using a provided token counting function.

    Wraps the token counting function with error handling. Ensures the returned
    value is numeric and converts it to an integer.

    Args:
        text (str): Text to count tokens in.
        token_counter (Callable[[str], int]): Function that returns the number of tokens.

    Returns:
        int: Number of tokens.

    Raises:
        CallbackError: If the token counter fails or returns an invalid type.

    Examples:
        >>> def simple_word_counter(text: str) -> int:
        ...     return len(text.split())
        >>> text = "This is a sample sentence."
        >>> count_tokens(text, simple_word_counter)
        5

        >>> def char_counter(text: str) -> int:
        ...     return len(text)
        >>> count_tokens("hello", char_counter)
        5

        >>> # Example with a failing token counter
        >>> def failing_counter(text: str) -> int:
        ...     raise ValueError("Something went wrong!")
        >>> try:
        ...     count_tokens("test", failing_counter)
        ... except CallbackError as e:
        ...     print(e)
        Token counter failed while processing text starting with: 'test...'.
        💡 Hint: Please ensure the token counter function handles all edge cases and returns an integer.
        Details: Something went wrong!
    """
    try:
        token_count = token_counter(text)
        if isinstance(token_count, (int, float)):
            return int(token_count)
        raise CallbackError(
            f"Token counter returned invalid type ({type(token_count).__name__}) "
            f"for text starting with: '{text[:100]}'"
        )
    except Exception as e:
        raise CallbackError(
            f"Token counter failed while processing text starting with: '{text[:100]}...'.\n"
            "💡 Hint: Please ensure the token counter function handles "
            f"all edge cases and returns an integer. \nDetails: {e}"
        ) from e
