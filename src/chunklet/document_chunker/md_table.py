def build_md_table(data: list[list[object]]) -> str:
    """
    Build a pipe-formatted Markdown table from a list of rows.

    The first row is treated as the header. Each cell's content is converted
    to a string and escaped so that literal pipe characters (``|``) do not
    break the table layout.

    Args:
        data: List of rows, where each row is a list of cell values.
              The first element is the header row.

    Returns:
        A string containing the full pipe table, including leading/trailing
        newlines, ready to embed in Markdown output.

    Raises:
        ValueError: If *data* is empty.
    """
    if not data:
        raise ValueError("At least one row (the header) is required.")

    def _escape(cell: object) -> str:
        return str(cell).replace("|", "\\|")

    header = [_escape(c) for c in data[0]]
    sep = ["---"] * len(header)
    rows = [[_escape(c) for c in row] for row in data[1:] if row]

    lines = []
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(sep) + " |")
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")

    return "\n" + "\n".join(lines) + "\n"
