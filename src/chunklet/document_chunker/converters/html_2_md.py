import re
from pathlib import Path
try:
    from markdownify import markdownify as md
except ImportError:
    md = None


def html_to_md(file_path: str | Path, max_url_length: int = 150) -> str:
    """
    Convert HTML content to Markdown, remove hrefs from links, and truncate long URLs.

    Args:
        file_path (str | Path): Path to the html file.

    Returns:
        str: The full text content in Markdown.
    """
    if md is None:
        raise ImportError(
            "The 'markdownify' library is not installed. "
            "Please install it with 'pip install markdownify' or install the document processing extras "
            "with 'pip install 'chunklet-py[document]''"
        )

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        markdown_content = md(f.read())

    # Normalize consecutive newlines that are more than 2
    markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)
    
    # Truncate long URLs in Markdown links or images
    def truncate_url(match: re.Match) -> str:
        prefix, url = match.group(1), match.group(2)
        if len(url) > max_url_length:
            url = url[:max_url_length - 3] + "..."
        return f"{prefix}({url})"
        
    return re.sub(r'(!?\[.*?\])\((.*?)\)', truncate_url, markdown_content)
    

# Example usage
if __name__ == "__main__":
    import textwrap
    import tempfile
    
    html_sample = textwrap.dedent("""
        <h2>Examples</h2>
        <p>Visit <a href="https://example.com/some/very/very/very/very/very/long/link/that/should/be/truncated/because/it/is/humongous.html">Example</a>.</p>
        <img
        src="https://example.com/image/with/a/really/really/really/long/path/that/needs/truncating.png" alt="Long Image">
    """)
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", encoding="utf-8") as temp_html_file:
        temp_html_file.write(html_sample)
        temp_html_file.flush() # Ensure content is written to disk    
        
        markdown_output = html_to_md(temp_html_file.name)
        print(markdown_output)