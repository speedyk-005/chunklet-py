import tempfile
from pathlib import Path
from chunklet.document_chunker.converters.html_2_md import html_to_md


def rst_to_md(file_path: str | Path) -> str:
    """
    Converts reStructuredText (RST) content into Markdown.

    Args:
        file_path (str | Path): Path to the rst file.

    Returns:
        str: The full text content in Markdown.
    """
    try:  # Lazy imports
        from docutils.core import publish_string
    except ImportError as e:
        raise ImportError(
            "The 'docutils' library is not installed. "
            "Please install it with 'pip install 'docutils>=0.21.2'' or install the document processing extras "
            "with 'pip install 'chunklet-py[document]''"
        ) from e

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        rst_content = f.read()
        
    # Convert the rst content to HTML first
    html_content = publish_string(source=rst_content, writer_name="html").decode("utf-8")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", encoding="utf-8") as temp_html_file:
        temp_html_file.write(html_content)
        temp_html_file.flush() # Ensure content is written to disk    

        # Now we can convert it to markdown
        markdown_content = html_to_md(temp_html_file.name)
    return markdown_content


# Example usage
if __name__ == "__main__":
    markdown_result = rst_to_md("samples/What_is_rst.rst")
    print(markdown_result)