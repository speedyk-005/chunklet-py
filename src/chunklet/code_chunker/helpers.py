import regex as re
import ast
import mimetypes
from pathlib import Path
from pygments.lexers import guess_lexer
from pygments.util import ClassNotFound
from chunklet.common.validation import validate_input
from chunklet.common.path_utils import is_path_like


@validate_input
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


@validate_input
def is_python_code(source: str | Path) -> bool:
    """
    Check if a source is written in Python.

    This function uses multiple indicators, prioritizing syntactic validity
    via the Abstract Syntax Tree (AST) parser for maximum confidence.

    Indicators used:
      - File extension check for path inputs (e.g., .py, .pyi, .pyx, .pyw).
      - Shebang line detection (e.g., "#!/usr/bin/python").
      - Definitive syntax check using Python's `ast.parse()`.
      - Fallback heuristic via Pygments lexer guessing.

    Note:
        The function is definitive for complete, syntactically correct code blocks.
        It falls back to a Pygments heuristic only for short, incomplete, or
        ambiguous code snippets that fail AST parsing.

    Args:
        source (str | Path): raw code string or Path to source file to check.

    Returns:
        bool: True if the source is written in Python.
    """
    # Path-based check
    if isinstance(source, Path) or (isinstance(source, str) and is_path_like(source)):
        path = Path(source)
        return path.suffix.lower() in {".py", ".pyi", ".pyx", ".pyw"}

    if isinstance(source, str):
        # Shebang line check
        if re.match(r"#!/usr/bin/(env\s+)?python", source.strip()):
            return True

        # Definitive syntactic check (Highest confidence)
        try:
            ast.parse(source)
            # If parsing succeeds, it's definitely Python code
            return True
        except Exception:  # noqa: S110
            # If fails, it might still be Python code (e.g., incomplete snippet), so continue with heuristics
            pass

    # Pygments heuristic (Lowest confidence, last resort)
    try:
        lexer = guess_lexer(source)
        return lexer.name.lower() == "python"
    except ClassNotFound:
        return False
