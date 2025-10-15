from loguru import logger
from rich.console import Console

# Setup Rich console
console = Console()

# Redirect loguru to Rich console, disable loguru coloring
logger.remove()
logger.add(console.print, colorize=False)
