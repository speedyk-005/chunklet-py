def build_md_table(data: list[list[str]]) -> str:
    """
    Build a pipe-formatted Markdown table from a list of rows.

    The first row is treated as the header. Each cell's content is escaped
    so that literal pipe characters (``|``) do not break the table layout.

    Args:
        data: List of rows, where each row is a list of cell strings.
              The first element is the header row.

    Returns:
        A string containing the full pipe table, including leading/trailing
        newlines, ready to embed in Markdown output.

    Raises:
        ValueError: If *data* is empty or any row is empty.
    """
    if not data:
        raise ValueError("At least one row (the header) is required.")
    if any(not row for row in data):
        raise ValueError("Every row must contain at least one cell.")

    def _escape(cell: str) -> str:
        return cell.replace("|", "\\|")

    header = [_escape(c) for c in data[0]]
    sep = ["---"] * len(header)
    rows = [[_escape(c) for c in row] for row in data[1:]]

    lines = []
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(sep) + " |")
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")

    return "\n" + "\n".join(lines) + "\n"
