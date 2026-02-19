import functools
import warnings
from importlib.metadata import PackageNotFoundError, version
from packaging.version import InvalidVersion, Version
from typing import Any, Callable

try:
    CURRENT_VERSION = version("chunklet-py")
except PackageNotFoundError:
    CURRENT_VERSION = "0.0.0"


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
        warn_message = (
            f"`{func_or_cls.__qualname__}` was deprecated since v{deprecated_in} "
            f"in favor of `{use_instead}`. It will be removed in v{removed_in}."
        )
        remove_message = (
            f"`{func_or_cls.__qualname__}` was removed in v{removed_in}. "
            f"Use `{use_instead}` instead."
        )

        @functools.wraps(func_or_cls)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if Version(CURRENT_VERSION) >= Version(removed_in):
                raise AttributeError(remove_message)
            warnings.warn(warn_message, FutureWarning, stacklevel=2)
            return func_or_cls(*args, **kwargs)

        return wrapper

    return decorator
