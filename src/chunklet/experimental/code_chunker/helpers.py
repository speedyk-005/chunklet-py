import sys
import regex as re
from pathlib import Path
import mimetypes
from pygments.lexers import guess_lexer
from pygments.util import ClassNotFound

# Pattern to check if source args provided in the chunk method is a path
PATH_PATTERN = re.compile(
    r"""
    ^                                   # start of string
    (?:/|[\p{Lu}]:\\)?                 # optional root (Unix or Windows drive)
    (?:[\p{L}\p{N}_\-. ]+[/\\])*       # intermediate folders
    (?:[\p{L}\p{N}_\-. ])+             # file name (hidden or normal)
    (?:\.[\p{L}\p{N}]+)?               # optional extension
    $                                   # end of string
""",
    re.VERBOSE,
)


def is_path_like(text: str) -> bool:
    """
    Check if a string looks like a filesystem path (file or folder),
    including Unix/Windows paths, hidden files, and scripts without extensions.

    Args:
        text (str): text to check.

    Returns:
        bool: True if string appears to be a filesystem path.
    """
    if not text or "\n" in text or "\0" in text:
        return False
    if sys.platform == "win32" and any(c in text for c in '<>:"|?*'):
        return False

    return bool(PATH_PATTERN.fullmatch(text))  # Fixed: changed full_match to fullmatch


def is_binary_file(file_path: str | Path) -> bool:
    """
    Determine whether a file is binary or text.

    First tries to guess the file type based on its MIME type derived from
    the file extension. If MIME type is unavailable or ambiguous, reads the
    first 1024 bytes of the file and checks for null bytes (`b'\0'`), which
    indicate binary content.

    Args:
        file_path (str | Path): Path to the file.

    Returns:
        bool: True if the file is likely binary, False if text.
    """
    file_path = Path(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return not mime_type.startswith("text")

    with open(file_path, "rb") as f:
        chunk = f.read(1024)
        return b"\0" in chunk


def is_python_code(source: str | Path) -> bool:
    """
    Heuristically check if a source is written in Python

    This function uses multiple indicators to determine whether the input
    is likely Python code, including:
      - File extension check (".py")
      - Shebang line detection (e.g., "#!/usr/bin/python" or "#!/usr/bin/env python")
      - Syntax pattern recognition via Pygments lexer guessing

    Note:
        This is a heuristic approach and may produce false positives or
        false negatives for short, ambiguous, or unconventional code snippets.

    Args:
        source (str | Path): raw code string or Path to source file to check.

    Returns:
        bool: True if the source is written in Python.
    """
    if isinstance(source, Path) or (isinstance(source, str) and is_path_like(source)):
        path = Path(source)
        return path.suffix.lower() == ".py"

    if re.match(r"#!/usr/bin/(env\s+)?python", source.strip()):
        return True

    try:
        lexer = guess_lexer(source)
        return lexer.name.lower() == "python"
    except ClassNotFound:
        return False
