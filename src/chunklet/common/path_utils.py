import errno
import mimetypes
import sys
from pathlib import Path

import regex as re

# charset_normalizer is lazy imported
from chunklet.common.validation import validate_input
from chunklet.exceptions import FileProcessingError

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


def _is_binary_file(path: str | Path) -> bool:
    """
    Determine whether a file is binary or text.

    First tries to guess the file type based on its MIME type derived from
    the file extension. If MIME type is unavailable or ambiguous, reads the
    first 1024 bytes of the file and checks for null bytes (`b'\0'`), which
    indicate binary content.

    Args:
        path (str | Path): Path to the file.

    Returns:
        bool: True if the file is likely binary, False if text.
    """
    path = Path(path)
    mime_type, _ = mimetypes.guess_type(path)
    if mime_type:
        return not mime_type.startswith("text")

    with open(path, "rb") as f:
        chunk = f.read(1024)
        return b"\0" in chunk


@validate_input
def is_path_like(text: str) -> bool:
    """
    Check if a string looks like a filesystem path (file or folder),
    including Unix/Windows paths, hidden files, and scripts without extensions.

    Args:
        text (str): text to check.

    Returns:
        bool: True if string appears to be a filesystem path.

    Examples:
        >>> is_path_like("/home/user/document.txt")
        True
        >>> is_path_like("C:\\Users\\User\\file.pdf")
        True
        >>> is_path_like("folder/subfolder/script.sh")
        True
        >>> is_path_like(".hidden_file")
        True
        >>> is_path_like("no_extension_script")
        True
        >>> is_path_like("path/with/newline\\nchar")
        False
        >>> is_path_like("string_with_null_byte\\x00")
        False
    """
    if not text or "\n" in text or "\0" in text:
        return False
    if sys.platform == "win32" and any(c in text for c in '<>:"|?*'):
        return False

    try:
        # Attempt to call is_file() to trigger OS-level path validation,
        # especially for path length.
        Path(text).is_file()
    except OSError as e:
        # If an OSError occurs, check if it's specifically due to the name being too long.
        if e.errno == errno.ENAMETOOLONG:
            return False
        else:
            # For other OSErrors (e.g., permission denied, invalid characters not caught by initial checks),
            # we let the regex check proceed, as the focus is on structural validity, not existence or access.
            pass

    return bool(PATH_PATTERN.match(text))


@validate_input
def read_text_file(path: str | Path) -> str:
    """Read text file with automatic encoding detection.

    Args:
        path: File path to read.

    Returns:
        str: File content.

    Raises:
        FileProcessingError: If file cannot be read.
    """
    from charset_normalizer import from_path

    path = Path(path)

    if not path.exists():
        raise FileProcessingError(f"File does not exist: {path}")

    if _is_binary_file(path):
        raise FileProcessingError(f"Binary file not supported: {path}")

    match = from_path(str(path)).best()
    return str(match) if match else ""
