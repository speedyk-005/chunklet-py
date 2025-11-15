import sys
import errno
import regex as re
from pathlib import Path
from chunklet.common.validation import validate_input

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
