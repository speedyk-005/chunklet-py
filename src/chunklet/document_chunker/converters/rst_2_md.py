from pathlib import Path

try:
    from docutils.core import publish_string
except ImportError:
    publish_string = None

from chunklet.document_chunker.converters.html_2_md import html_to_md


def rst_to_md(file_path: str | Path) -> str:
    """
    Converts reStructuredText (RST) content into Markdown.

    Args:
        file_path (str | Path): Path to the rst file.

    Returns:
        str: The full text content in Markdown.
    """
    if publish_string is None:
        raise ImportError(
            "The 'docutils' library is not installed. "
            "Please install it with 'pip install 'docutils>=0.21.2'' or install the document processing extras "
            "with 'pip install 'chunklet-py[document]''"
        )

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        rst_content = f.read()

    # Convert the rst content to HTML first
    html_content = publish_string(source=rst_content, writer_name="html").decode(
        "utf-8"
    )

    # Now we can convert it to markdown
    markdown_content = html_to_md(raw_text=html_content)
    return markdown_content


# Example usage
if __name__ == "__main__":  # pragma: no cover
    markdown_result = rst_to_md("samples/What_is_rst.rst")
    print(markdown_result)
