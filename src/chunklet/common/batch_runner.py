import os 
import sys
import re
from typing import Any, Literal, Callable
from itertools import tee
from more_itertools import ilen
from collections.abc import Iterable, Generator
# mpire is lazy imported
from loguru import logger
from chunklet.common.validation import safely_count_iterable
from chunklet.common._progress_bar import ProgressBar

def run_in_batch(
    func: Callable,
    iterable_of_args: Iterable,
    iterable_name: str,
    n_jobs: int | None = None,
    show_progress: bool = True,
    on_errors: Literal["raise", "skip", "break"] = "raise",
    separator: Any = None,
    verbose: bool = True,
) -> Generator[Any, None, None]:
    """
    Processes a batch of items in parallel using multiprocessing.
    Splits the iterable into chunks and executes the function on each.

    Args:
        func (Callable): The function to call for each argument.
        iterable_of_args (Iterable): An iterable of inputs to process.
        iterable_name: Name of the iterable. needed for logging and exception message.
        n_jobs (int | None): Number of parallel workers to use.
            If None, uses all available CPUs. Must be >= 1 if specified.
        show_progress (bool): Whether to display a progress bar.
        on_errors (Literal["raise", "skip", "break"]):
            How to handle errors during processing. Defaults to "raise".
        separator (Any): A value to be yielded after the chunks of each text are processed.
            Note: None cannot be used as a separator.
        verbose (bool): Whether to enable verbose logging.

    Yields:
        Any: A `Box` object containing the chunk content and metadata, or any separator object.
    """
    from mpire import WorkerPool

    total, iterable_of_args = safely_count_iterable(iterable_name, iterable_of_args)
        
    if verbose:
        logger.info("Starting batch chunking for {} items.", total)

    if total == 0:
        if verbose:
            logger.info("Input {} is empty. Returning empty iterator.", iterable_name)
        return iter([])

    # Wrapper to capture result/exception
    def chunk_func(*args, **kwargs):
        try:
            res = func(*args, **kwargs)
            return res, None
        except Exception as e:
            return None, e

    failed_count = 0
    try:
        with ProgressBar(iterable_of_args, total=total, display=show_progress) as pbar_iterable:
            with WorkerPool(n_jobs=n_jobs) as pool:
                imap_func = pool.imap if separator is not None else pool.imap_unordered
                task_iter = imap_func(
                    chunk_func,
                    pbar_iterable, # The pool iterates over the progress bar
                    iterable_len=total,
                )

                for res, error in task_iter:
                    if error:
                        failed_count += 1
                        if on_errors == "raise":
                            raise error
                        elif on_errors == "break":
                            logger.error(
                                "A task for {} failed. Returning partial results.\nReason: {}",
                                iterable_name,
                                error,
                            )
                            break
                        else:  # skip
                            logger.warning("Skipping a failed task.\nReason: {}", error)
                            continue
                        
                    yield from res

                    if separator is not None:
                        yield separator

    finally:
        if verbose:
            logger.info(
                "Batch processing completed. {}/{} items processed successfully.",
                total - failed_count,
                total,
            )
