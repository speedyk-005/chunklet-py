from typing import Any, Literal, Callable
from collections.abc import Iterable, Generator
from mpire import WorkerPool
from loguru import logger
from chunklet.utils.validation import safely_count_iterable

def run_in_batch(
    func: Callable,
    iterable_of_args: Iterable,
    iterable_name: str,
    n_jobs: int | None = None,
    show_progress: bool = True,
    on_errors: Literal["raise", "skip", "break"] = "raise",
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
        verbose (bool): Whether to enable verbose logging.

    Yields:
        Any: The result returned by each successful function call.
    """
    total, iterable_of_args = safely_count_iterable(iterable_name, iterable_of_args)

    if total == 0:
        if verbose:
            logger.info("Input {} is empty. Returning empty iterator.", iterable_name)
        return iter([])
        
    # Wrapper to capture result/exception
    def chunk_func(args):
        try:
            res = func(args)
            return res, None
        except Exception as e:
            return None, e

    failed_count = 0
    try:
        with WorkerPool(n_jobs=n_jobs) as executor:
            task_iter = executor.imap(
                chunk_func,
                iterable_of_args,
                iterable_len=total,
                progress_bar=show_progress,
            )

            for res, error in task_iter:
                if error:
                    failed_count += 1
                    if on_errors == "raise":
                        raise error
                    elif on_errors == "break":
                        logger.error(
                            "A task in 'run_in_batch' failed. Returning partial results.\n"
                            f"💡 Hint: Check logs for more details.\nReason: {error}"
                        )
                        break
                    else:  # skip
                        logger.warning(f"Skipping a failed task.\nReason: {error}")
                        continue

                yield res

    finally:
        if verbose:
            logger.info(
                "Batch processing completed with {}/{} successes",
                total - failed_count,
                total,
            )