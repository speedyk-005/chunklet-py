try:
    from markdownify import markdownify as md
except ImportError:
    md = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


def rst_to_markdown(rst_text: str) -> str:
    """
    Converts reStructuredText (RST) content into Markdown.

    This function takes an RST formatted string and converts it into its
    Markdown equivalent using `docutils` to first convert to HTML, and then
    `markdownify` to convert HTML to Markdown.

    Args:
        rst_text (str): The input RST string to be converted.

    Returns:
        str: The Markdown-formatted text.
    """
    if md is None:
        raise ImportError(
            "The 'markdownify' library is not installed. "
            "Please install it with 'pip install markdownify' or install the document processing extras "
            "with 'pip install 'chunklet-py[document]''"
        )

    try:  # Lazy imports
        from docutils.core import publish_string
    except ImportError as e:
        raise ImportError(
            "The 'docutils' library is not installed. "
            "Please install it with 'pip install docutils' or install the document processing extras "
            "with 'pip install 'chunklet-py[document]''"
        ) from e

    # Step 1: Convert RST => HTML
    html = publish_string(source=rst_text, writer_name="html").decode("utf-8")

    if BeautifulSoup is None:
        raise ImportError(
            "The 'beautifulsoup4' library is not installed. "
            "Please install it with 'pip install beautifulsoup4' or install the document processing extras "
            "with 'pip install 'chunklet-py[document]''"
        )

    # Parse HTML and extract body content to remove boilerplate
    soup = BeautifulSoup(html, "html.parser")
    body_content = (
        soup.body.prettify() if soup.body else html
    )  # Use prettify for better formatting

    # Step 2: Convert HTML => Markdown
    markdown_text = md(body_content)

    return markdown_text


# --- Example usage ---
if __name__ == "__main__":
    with open("samples/What_is_rst.rst") as f:
        rst_sample = f.read()
    markdown_result = rst_to_markdown(rst_sample)
    print(markdown_result)
