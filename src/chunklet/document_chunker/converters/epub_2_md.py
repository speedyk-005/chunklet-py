import tempfile
from pathlib import Path
try:
    from ebooklib import epub
except:
    epub = None
from chunklet.document_chunker.converters.html_2_md import html_to_md


def epub_to_md(file_path: str | Path) -> str:
    """
    Convert an EPUB file to Markdown.

    Args:
        file_path (str | Path): Path to the EPUB file.

    Returns:
        str: The full text content in Markdown.
    """
    if not epub:
        raise ImportError(
            "The 'ebooklib' library is not installed. "
            "Please install it with 'pip install 'ebooklib>=0.19'' or install the document processing extras "
            "with 'pip install 'chunklet-py[document]''"
        )
        
    book = epub.read_epub(file_path)
    html_content = []
    
    for item in book.get_items():
        if item.get_type() == 9:  # 9 corresponds to ITEM_DOCUMENT
            html_content.append(
                item.get_body_content().decode("utf-8", errors="ignore")
            )
    html_content = "\n\n".join(html_content)
    
    # Write HTML to a temporary file 
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", encoding="utf-8") as temp_html_file:
        temp_html_file.write(html_content)
        temp_html_file.flush() # Ensure content is written to disk    

        # Now we can convert it to markdown
        markdown_content = html_to_md(temp_html_file.name)

    return markdown_content


# Example usage
if __name__ == "__main__":
    file_path = "samples/minimal.epub"
    md_content = epub_to_md(file_path)
    print(md_content[:2000])  # Print first 2000 chars