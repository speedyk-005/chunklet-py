import os 
import sys
import re
from typing import Any, Literal, Callable
from itertools import tee
from more_itertools import ilen
from collections.abc import Iterable, Generator
from rich.progress import Progress

# multiprocess is lazy imported
from loguru import logger
from chunklet.utils.validation import safely_count_iterable

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
    # Using 'multiprocess' (a fork of multiprocessing) for enhanced pickling capabilities.
    from multiprocess import Pool

    total, iterable_of_args = safely_count_iterable(iterable_name, iterable_of_args)
        
    if verbose:
        logger.info("Starting batch chunking for {} items.", total)

    if total == 0:
        if verbose:
            logger.info("Input {} is empty. Returning empty iterator.", iterable_name)
        return iter([])

    # This is often better for I/O-bound tasks
    effective_n_jobs = n_jobs if n_jobs is not None else os.cpu_count() or 1
    # Use a heuristic (total / workers / 4) to send large chunks, ensuring a minimum of 1
    chunksize = max(1, total // (effective_n_jobs * 4))
    
    # Wrapper to capture result/exception
    def chunk_func(*args, **kwargs):
        try:
            res = func(*args, **kwargs)
            return res, None
        except Exception as e:
            return None, e

    progress = None
    failed_count = 0
    try:
        with Pool(processes=n_jobs) as pool:
            imap_func = pool.imap if separator is not None else pool.imap_unordered
            task_iter = imap_func(
                chunk_func,
                iterable_of_args,
                chunksize = chunksize,
            ) 

            task_iter, task_iter_2 = tee(task_iter)
            total_res = ilen(task_iter_2)
            
            # Progress bar setup
            if show_progress and total > 0:
                progress = Progress()
                task = progress.add_task(f"[green]Processing {iterable_name}[/green]", total=total_res) 
                progress.start() 
        
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
                        if progress:
                            progress.update(task, advance=1)
                        continue

                if progress:
                    progress.update(task, advance=1)
                    
                yield from res

                if separator is not None:
                    yield separator

    finally:
        if progress:
            progress.stop() 

        if verbose:
            logger.info(
                "Batch processing completed. {}/{} items processed successfully.",
                total - failed_count,
                total,
            )
