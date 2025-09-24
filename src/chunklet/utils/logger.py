import logging
from rich.console import Console
from rich.logging import RichHandler


console = Console(width=200) # fixed width to prevent excessive wrappings in narrow screens


handler = RichHandler(rich_tracebacks=True, show_path=True, markup=True)

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[handler]
)

logger = logging.getLogger(__name__)