import re
from pathlib import Path

try:
    from markdownify import markdownify as md
except ImportError:
    md = None

# This fix is needed for PyDocX to work with Python 3.10 and newer,
# as the collections.Hashable ABC was removed from the main module.
try:
    import collections.abc

    collections.Hashable = collections.abc.Hashable
except (ImportError, AttributeError):
    pass


class DOCXProcessor:
    """
    A utility for extracting text content from DOCX files and converting it
    to Markdown.

    This processor uses the `pydocx` library to perform the conversion from
    DOCX to HTML and then `markdownify` to convert the HTML to a clean
    Markdown format, explicitly removing image tags.
    """

    def extract_text(self, docx_path: str) -> str:
        """
        Extracts text from a DOCX file and converts it to Markdown.

        This method uses `pydocx` for the initial conversion to HTML and then
        `markdownify` to clean the HTML and convert it to Markdown,
        explicitly stripping out image elements.

        Args:
            docx_path (str): The absolute path to the DOCX file.

        Returns:
            str: The extracted and cleaned content of the DOCX file in
                 Markdown format.
        """
        try:  # Lazy import
            from pydocx import PyDocX
        except ImportError as e:
            raise ImportError(
                "The 'pydocx' library is not installed. "
                "Please install it with 'pip install pydocx' or install the document processing extras "
                "with 'pip install 'chunklet-py[document]''"
            ) from e

        # Open the document and convert to HTML.
        html_content = PyDocX.to_html(docx_path)

        if not md:
            raise ImportError(
                "The 'markdownify' library is not installed. "
                "Please install it with 'pip install markdownify' or install the document processing extras "
                "with 'pip install 'chunklet-py[document]''"
            )

        # Convert HTML to Markdown, explicitly stripping all <img> tags.
        markdown_content = md(html_content, strip=["img"])

        return markdown_content


# Usage Example
if __name__ == "__main__":
    docx_path = "samples/Lorem.docx"

    processor = DOCXProcessor()

    try:
        content = processor.extract_text(docx_path)
        print("=== Extracted Content ===")
        print(content)
    except FileNotFoundError:
        print(f"Error: The file '{docx_path}' was not found.")
    except ImportError as e:
        print(f"Error: {e}")
