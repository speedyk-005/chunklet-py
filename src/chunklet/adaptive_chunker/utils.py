import re

CODE_LINE_PREFIX = {
    "def",
    '"""',
    "'''",
    "///",
    "//",
    "/*",
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
CODE_LINE_PREFIX_PATTERN = re.compile(
    rf"^[ \t]*(?:{'|'.join(_CODE_PREFIXES)})(?:[ \t]|$)",
    re.M,
)

LINE_ENDING_SEMICOLON_PATTERN = re.compile(r";[ \t]*$", re.M)
CODE_SYMBOL_CHARS = r"={}[]()?.!%#/%^-+*&|!=><:__"
CODE_LIKE_SCORE_THRESHOLD = 47


def is_code_like(text: str) -> bool:
    """Determine whether text has a code-like structural profile.

    The classifier computes a weighted score from several structural
    signals:

    - indentation whitespace as a percentage of total characters
    - lines ending in a semicolon as a percentage of total lines
    - symbol concentration
    - code-like line prefixes as a percentage of total lines
    - lines as a percentage of total characters


    A Unix shebang adds a fixed bonus of 20 points.

    The final score is compared against ``CODE_LIKE_SCORE_THRESHOLD`` to
    determine whether the text is considered code-like.

    Examples:
        >>> is_code_like('printf("hello");\\n')
        True
        >>> is_code_like("int main(void) {\\n    printf(\\"hello\\");\\n    return 0;\\n}\\n")
        True
        >>> is_code_like("The quick brown fox jumps over the lazy dog.\\n")
        False
        >>> is_code_like(open("samples/sample_module.py").read())
        True
        >>> is_code_like(open("samples/sample_text.txt").read())
        False

    Args:
        text: Text to classify.

    Returns:
        Whether the computed code-like score meets the threshold.
    """
    if not text:
        return False

    lines = text.splitlines()

    if not lines:
        return False

    line_count = len(lines)
    weight = 0.0

    if re.match(r"^#!/usr/bin/", text):
        weight += 20

    # Indentation density
    indent_chars = sum(len(line) - len(line.lstrip(" \t")) for line in lines)
    indent_percent = indent_chars / len(text) * 100
    weight += indent_percent

    # Symbol density
    symbol_percent = (
        sum(text.count(char) for char in CODE_SYMBOL_CHARS) / len(text) * 100
    )
    weight += symbol_percent

    # Line-terminating semicolon density
    semicolon_count = len(LINE_ENDING_SEMICOLON_PATTERN.findall(text))
    semicolon_percent = semicolon_count / line_count * 100
    weight += semicolon_percent

    # Line density
    newline_percent = line_count / len(text) * 100
    weight += newline_percent * 2

    # Code-like line-prefix density
    prefix_count = len(CODE_LINE_PREFIX_PATTERN.findall(text))
    prefix_percent = prefix_count / line_count * 100
    weight += prefix_percent * 2

    return weight >= CODE_LIKE_SCORE_THRESHOLD


if __name__ == "__main__":  # pragme: no cover
    text = open("samples/sample_text.txt").read()
    print("sample_text.txt:", is_code_like(text))

    code = """def hello():
        print("hello world")

    hello()
    """
    print("sample code:", is_code_like(code))
