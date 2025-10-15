from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.console import Console

# Setup Rich console
console = Console()


def get_progress_bar(enabled: bool = True) -> Progress:
    """
    Create and return a Rich Progress instance.

    The progress bar includes description, percentage, a visual bar, and
    estimated time remaining. It can be disabled for non-interactive environments.

    Args:
        enabled (bool, optional): Whether the progress bar is enabled. Defaults to True.

    Returns:
        Progress: A configured Rich Progress instance.
    """
    return Progress(
        TextColumn("[progress.description]{task.description}"),
        TextColumn("[bold blue]{task.percentage:>3.0f}%"),
        BarColumn(),
        TimeRemainingColumn(),
        disable=not enabled,
        console=console,
    )
