import csv
from pathlib import Path

# openpyxyl is lazy imported

try:
    from tabulate2 import tabulate
except ImportError:
    tabulate = None


def table_to_md(file_path: str | Path) -> str:
    """
    Convert a CSV or XLSX file into a Markdown-formatted table string.

    Args:
        file_path (str | Path): Path to the input file (.csv or .xlsx).

    Returns:
        str: Markdown table representation of the file contents.
    """
    file_path = Path(file_path)
    ext = file_path.suffix.lower()

    # Read CSV
    if ext == ".csv":
        with open(file_path, newline="", encoding="utf-8") as f:
            data = list(csv.reader(f))

    # Read Excel (.xlsx)
    elif ext == ".xlsx":
        try:
            from openpyxl import load_workbook
        except ImportError as e:
            raise ImportError(
                "The 'openpyxl' library is not installed. "
                "Please install it with 'pip install openpyxl>=3.1.2' "
                "or install the document processing extras with "
                "'pip install chunklet-py[document]'"
            ) from e
        wb = load_workbook(file_path, read_only=True)
        sheet = wb.active
        data = list(sheet.iter_rows(values_only=True))
        wb.close()

    else:
        raise ValueError(f"Unsupported file type: {ext}")

    headers = data[0]
    rows = data[1:]

    if not tabulate:
        raise ImportError(
            "The 'tabulate2' library is not installed. "
            "Please install it with 'pip install tabulate2>=1.10.0' "
            "or install the document processing extras with "
            "'pip install chunklet-py[document]'"
        )

    return tabulate(rows, headers=headers, tablefmt="pipe")


# Exemple usage
if __name__ == "__main__":  # pragma: no cover
    # Convert sample Excel file to Markdown
    sample_file = "samples/example.xlsx"
    md_table = table_to_md(sample_file)
    print(f"\nMarkdown output for {sample_file}:\n")
    print(md_table)
