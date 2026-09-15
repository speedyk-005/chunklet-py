import re

CODE_LINE_PREFIX = {
    "def",
    '"""',
    "'''",
    "///",
    "fun",
    "func",
    "class",
    "int",
    "string",
    "object",
    "str",
    "use",
    "self",
    "this",
    "for",
    "while",
    "print",
    "console",
    "import",
    "using",
    "set",
    "var",
    "if",
    "elif",
    "else",
    "foreach",
    "void",
    "end",
    "done",
    "switch",
    "case",
    "default",
    "break",
    "continue",
    "try",
    "catch",
    "except",
    "finally",
    "throw",
    "raise",
    "yield",
    "async",
    "await",
    "from",
    "export",
    "public",
    "private",
    "protected",
    "static",
    "new",
    "return",
    "del",
    "extends",
    "implements",
    "interface",
    "enum",
    "struct",
    "namespace",
    "package",
    "module",
    "lambda",
    "assert",
}

_CODE_PREFIXES = sorted(
    (re.escape(prefix) for prefix in CODE_LINE_PREFIX),
    key=len,
    reverse=True,
)

CODE_LINE_PREFIX_PAT = re.compile(
    rf"^[ \t]*(?:{'|'.join(_CODE_PREFIXES)})(?:[ \t]|$)",
    re.M,
)

MIN_WEIGHT = 47

CODE_SYMBOLS = r"={}[]()?.!%#/"


def is_code_like(text: str) -> bool:
    """Determine whether text has a code-like structural profile.

    The classifier computes a weighted score from three structural
    signals:

    - indentation whitespace as a percentage of total characters
    - lines as a percentage of total characters
    - symbol concentration
    - code-like line prefixes as a percentage of total lines

    A Unix shebang adds a fixed bonus of 20 points.

    The final score is compared against ``MIN_WEIGHT`` to determine
    whether the text is considered code-like.

    Args:
        text: Text to classify.

    Returns:
        A tuple containing the computed score and a boolean indicating
        whether the score meets the code-like threshold.
    """
    if not text:
        return 0.0, False

    lines = text.splitlines()

    if not lines:
        return 0.0, False

    weight = 0.0

    if re.match(r"^#!/usr/bin/", text):
        weight += 20

    # Indentation density
    indent_chars = sum(len(line) - len(line.lstrip(" \t")) for line in lines)
    indent_percent = indent_chars / len(text) * 100
    weight += indent_percent

    # Line density
    newline_percent = len(lines) / len(text) * 100
    weight += newline_percent * 2

    # Symbol density
    symbol_percent = sum(text.count(char) for char in CODE_SYMBOLS) / len(text) * 100
    weight += symbol_percent

    # Code-like line-prefix density
    prefix_count = len(CODE_LINE_PREFIX_PAT.findall(text))
    prefix_percent = prefix_count / len(lines) * 100
    weight += prefix_percent * 2

    return weight, weight >= MIN_WEIGHT


if __name__ == "__main__":  # pragme: no cover
    text = open("samples/sample_text.txt").read()
    print("sample_text.txt:", is_code_like(text))

    code = """def hello():
        print("hello world")

    hello()
    """
    print("sample code:", is_code_like(code))
