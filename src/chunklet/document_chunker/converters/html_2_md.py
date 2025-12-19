import re
from pathlib import Path

try:
    from markdownify import markdownify as md
except ImportError:
    md = None


def html_to_md(
    file_path: str | Path = None, raw_text: str | None = None, max_url_length: int = 150
) -> str:
    """
    Convert HTML content to Markdown, remove hrefs from links, and truncate long URLs.

    Args:
        file_path (str | Path): Path to the html file.
        raw_text (str, optional): Raw HTML text. If both file_path and raw_text is provided,
            then raw_text will be used instead.
        max_url_length (int): The maximum length of a URL. Defaults to 150.

    Returns:
        str: The full text content in Markdown.
    """
    if md is None:
        raise ImportError(
            "The 'markdownify' library is not installed. "
            "Please install it with 'pip install markdownify' or install the document processing extras "
            "with 'pip install 'chunklet-py[document]''"
        )

    if raw_text:
        markdown_content = md(raw_text)
    elif file_path:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            markdown_content = md(f.read())
    else:
        raise ValueError("Either file_path or raw_text must be provided.")

    # Normalize consecutive newlines that are more than 2
    markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)

    # Truncate long URLs in Markdown links or images
    def truncate_url(match: re.Match) -> str:
        prefix, url = match.group(1), match.group(2)
        if len(url) > max_url_length:
            url = url[: max_url_length - 3] + "..."
        return f"{prefix}({url})"

    return re.sub(r"(!?\[[^\]]*\])\((.*?)\)", truncate_url, markdown_content)


# Example usage
if __name__ == "__main__":  # pragma: no cover
    import textwrap

    html_sample = textwrap.dedent(
        """
        <h2>Examples</h2>
        <p>Visit <a href="https://example.com/some/very/very/very/very/very/long/link/that/should/be/truncated/because/it/is/humongous.html">Example</a>.</p>
        <img
        src="https://example.com/image/with/a/really/really/really/long/path/that/needs/truncating.png" alt="Long Image">
    """
    )

    markdown_output = html_to_md(raw_text=html_sample)
    print(markdown_output)
