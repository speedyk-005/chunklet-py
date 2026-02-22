from loguru import logger


def log_info(verbose: bool, *args, **kwargs) -> None:
    """Log an info message if verbose is enabled.

    This is a convenience function that only logs when verbose mode is enabled,
    avoiding unnecessary log output in production.

    Args:
        verbose: If True, logs the message; if False, does nothing.
        *args: Positional arguments passed to logger.info().
        **kwargs: Keyword arguments passed to logger.info().

    Example:
        >>> log_info(True, "Processing file: {}", filepath)
        Processing file: /path/to/file
        >>> log_info(False, "This will not be logged")
        (no output)
    """
    if verbose:
        logger.info(*args, **kwargs)
