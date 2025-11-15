import sys
import time
import shutil
from typing import Iterable, Iterator
from io import TextIOWrapper
from itertools import tee
from more_itertools import ilen
from stringcolor import cs


# --- Constants ---
CLEAR_LINE_CHAR = "\r\033[2K"

_GRADIENT = [
    "red", "orangered", "darkorange", "orange", "gold",
    "yellow", "greenyellow", "chartreuse", "lime", "green",
]


def get_colored_text(text: str, percent: int) -> str:
    """Return text colorized by progress percentage.

    Args:
        text (str): The text to colorize.
        percent (int): Progress percentage (0–100).

    Returns:
        str: Colorized text with ANSI escape codes.
    """
    index = max(0, min(percent * len(_GRADIENT) // 100, len(_GRADIENT) - 1))
    return str(cs(text, _GRADIENT[index]))


class ProgressBar(TextIOWrapper):
    """Terminal progress bar with dynamic coloring and stdout hijack."""

    def __init__(
        self,
        iterable: Iterable,
        total: int | None = None,
        width: int | None = None,
        fill_char: str = "█",
        empty_char: str = "_",
        refresh_per_second: float = 60.0,
        display: bool = True,
    ):
        """Initialize the progress bar.

        Args:
            iterable (Iterable): Iterable to wrap.
            total (int, optional): Total number of elements.
            width (int, optional): Bar width in characters.
            fill_char (str, optional): Symbol for filled area. Defaults to "█".
            empty_char (str, optional): Symbol for empty area. Defaults to " ".
            refresh_per_second (float, optional): Refresh rate in updates per second.
            display (bool, optional): Whether to display the progress bar. Defaults to True.
        """
        self._iterable = iterable
        self._width = width
        self._fill_char = fill_char
        self._empty_char = empty_char
        self._refresh_rate = 1.0 / max(refresh_per_second, 1e-6)
        self._display = display
        
        self._was_last_line_pbar = False  # track last line type

        if not total: 
            try:
                self._total = len(iterable)
                self._iterator = iter(self._iterable)
            except TypeError:  # Then it is an iterator-like object
                iterator, iterator_copy = tee(iterable)
                self._iterator = iterator
                self._total = ilen(iterator_copy)
        else:
            self._total = total

        self._index = 0
        self._original_stdout = None 
        self._last_update = 0.0

    def _humanize_number(self, num, width):
        """Return a human-readable number string (e.g., 1.2k, 3.4M)."""
        for unit in ["", "k", "M", "B", "T"]:
            if abs(num) < 1000:
                if width < 30:
                    num_str = f"{num:.0f}{unit}"
                if width < 50:
                    num_str = f"{num:.1f}{unit}"
                else:
                    num_str = f"{num:.2f}{unit}"
                return num_str.rstrip("0").rstrip(".")
                
            num /= 1000

    def __iter__(self):
        """Initialize iteration and display the first bar."""
        self._start_time = time.time()
        self._index = 0
        self._iterator = iter(self._iterable)
        if self._total:
            self._display_bar()
        return self

    def __next__(self):
        """Advance iteration and update the display."""
        try:
            item = next(self._iterator)
            self._index += 1
        except StopIteration:
            sys.stdout = self._original_stdout
            self._display_bar(is_final=True)
            raise
            
        if not self._display:
            return item
            
        now = time.time()
        if now - self._last_update >= self._refresh_rate:
            self._display_bar()
            self._last_update = now
        return item

    def write(self, msg: str, context: str = "log"):
        """Write to stdout. Clears previous progress bar if needed."""
        if self._was_last_line_pbar:
            sys.__stdout__.write(CLEAR_LINE_CHAR)

        sys.__stdout__.write(msg)
        self.flush()

        self._was_last_line_pbar = (context == "progress")

    def flush(self):
        """Flush the output stream."""
        sys.__stdout__.flush()

    def _display_bar(self, is_final=False):
        """Render the progress bar with ETA and color gradient."""
        term_size = shutil.get_terminal_size(fallback=(32, 32))
        term_width = term_size.columns

        avg_time_per_item = 0
        if self._index > 0:
            elapsed = time.time() - self._start_time
            avg_time_per_item = elapsed / self._index

        remaining = max(0.0, avg_time_per_item * (self._total - self._index))
        eta_text = f"ETA {remaining:.1f}s"
        percent = self._index * 100 // self._total

        pct_text = f"{percent}%"
        count_text = f"| {self._humanize_number(self._index, term_width)}/{self._humanize_number(self._total, term_width)}"

        fixed_len = len(eta_text) + len(pct_text) + len(count_text) + 5 # spaces
        available_width = term_width - fixed_len
        bar_width = self._width or available_width

        fill_len = int(bar_width * percent / 100) if self._total else 0
       
        if not is_final:
           bar = (
                f"[{get_colored_text(self._fill_char * fill_len, percent)}{pct_text}"
                f"{get_colored_text(self._empty_char * (bar_width - fill_len), percent)}]"
            )
            
           self.write(f"{bar} {eta_text} {count_text} ",  context="progress")
        else:
            for i in range(5):  # It will fit
                bar = (
                    f"[{get_colored_text(self._fill_char * (fill_len + i), percent)}{pct_text}]"
                )
                self.write(f"{bar} Done! ^_^", context="progress")
                time.sleep(0.01)
            self.write(f"{bar} Done! ^_^\n") # Prevent complete removal if a log is print just after
              
    def __enter__(self):
        """Redirect stdout to this instance for duration of the context."""
        self._original_stdout = sys.stdout
        sys.stdout = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore original stdout when the context ends."""
        sys.stdout = self._original_stdout
        return False


# --- Example usage ---
if __name__ == "__main__":
    print("Initializing computation...")

    TOTAL_ITEMS = 150
    with ProgressBar(range(TOTAL_ITEMS)) as bar:
        for i in bar:
            time.sleep(0.01)
            if (i + 1) % 15 == 0:
                print(f"LOG: Milestone {i // 15 + 1} reached.")
            if i == TOTAL_ITEMS // 2:
                print ("Halfway there!")
