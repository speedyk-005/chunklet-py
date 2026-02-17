import ast
from pathlib import Path

import regex as re
from pygments.lexers import guess_lexer
from pygments.util import ClassNotFound

from chunklet.common.path_utils import is_path_like
from chunklet.common.validation import validate_input


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
