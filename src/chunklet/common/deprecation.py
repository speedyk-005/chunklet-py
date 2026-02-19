import functools
import warnings
from typing import Any, Callable


def deprecated_callable(
    use_instead: str,
    deprecated_in: str,
    removed_in: str,
):
    """Decorate a function or class with warning message.

    This decorator marks a function or class as deprecated.

    Args:
        use_instead (str): Replacement name (e.g., "split_text", "DocumentChunker", or "chunk_text or chunk_file").
        deprecated_in (str): Version when the function was deprecated (e.g., "2.2.0").
        removed_in (str): Version when the function will be removed (e.g., "3.0.0").

    Returns:
        Callable: Decorator function that wraps the source function/class.
    """

    def decorator(func_or_cls: Callable) -> Callable:
        template = (
            f"`{func_or_cls.__qualname__}` was deprecated since v{deprecated_in} "
            f"in favor of `{use_instead}`. It will be removed in v{removed_in}."
        )

        @functools.wraps(func_or_cls)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warnings.warn(template, FutureWarning, stacklevel=2)
            return func_or_cls(*args, **kwargs)

        return wrapper

    return decorator
