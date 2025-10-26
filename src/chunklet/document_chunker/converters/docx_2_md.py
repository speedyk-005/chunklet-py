import tempfile
from pathlib import Path
from chunklet.document_chunker.converters.html_2_md import html_to_md


def docx_to_md(file_path: str | Path) -> str:
    """
    Convert a DOCX file to Markdown, replacing images with placeholders.

    Args:
        file_path (str | Path): Path to the DOCX file.

    Returns:
        str: The full text content in Markdown.
    """
    try:  # Lazy import
        import mammoth
    except ImportError as e:
        raise ImportError(
            "The 'mammoth' library is not installed. "
            "Please install it with 'pip install 'mammoth>=1.9.0'' or install the document processing extras "
            "with 'pip install 'chunklet-py[document]''"
        ) from e

    image_count = 0
    def placeholder_images(image):
        # Replace all images with a placeholder text
        nonlocal image_count
        image_count += 1
        return [mammoth.html.text(f"[Image-{image_count}]")]

    # Convert the DOCX content to HTML first
    with open(file_path, "rb") as docx_file:
        result = mammoth.convert_to_html(docx_file, convert_image=placeholder_images)
        html_content = result.value

    # Write HTML to a temporary file 
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", encoding="utf-8") as temp_html_file:
        temp_html_file.write(html_content)
        temp_html_file.flush() # Ensure content is written to disk    

        # Now we can convert it to markdown
        markdown_content = html_to_md(temp_html_file.name)
    
    return markdown_content


# Example usage
if __name__ == "__main__":
    word_path = "samples/Lorem Ipsum.docx"
    markdown_output = docx_to_md(word_path)
    print(markdown_output)