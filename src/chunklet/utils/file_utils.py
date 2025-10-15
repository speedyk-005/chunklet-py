import mimetypes
from pathlib import Path


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
