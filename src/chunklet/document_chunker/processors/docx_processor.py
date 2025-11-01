from typing import Any, Generator
from more_itertools import chunked

# mammoth and docx are lazy imported

from chunklet.document_chunker.processors.base_processor import BaseProcessor
from chunklet.document_chunker.converters.html_2_md import html_to_md


class DocxProcessor(BaseProcessor):
    """Processor class for extracting text and metadata from DOCX files.

    This class can extract metadata and textual content from a DOCX file.
    Images are replaced with a placeholder, and Markdown conversion is applied.

    Attributes:
        file_path (str): Path to the DOCX file.
    """

    def extract_metadata(self) -> dict[str, Any]:
        """Extracts core metadata from the DOCX file.

        Returns:
            dict[str, Any]: A dictionary containing metadata fields:
                - title
                - author
                - subject
                - keywords
                - last_modified_by
                - created
                - modified
        """
        try:
            from docx import Document
        except ImportError as e:
            raise ImportError(
                "The 'python-docx' library is not installed. "
                "Please install it with 'pip install 'python-docx>=1.2.0'' or install the document processing extras "
                "with 'pip install 'chunklet-py[document]''"
            ) from e

        doc = Document(self.file_path)
        props = doc.core_properties
        metadata = {
            "source": str(self.file_path),
            "title": props.title,
            "author": props.author,
            "subject": props.subject,
            "keywords": props.keywords,
            "last_modified_by": props.last_modified_by,
            "created": props.created,
            "modified": props.modified,
        }
        return metadata

    def extract_text(self) -> Generator[str, None, None]:
        """Extracts the text content from the DOCX file in Markdown format.

        Images are replaced with a placeholder "[Image here]".
        Text is yielded in blocks of 200 lines to facilitate processing.

        Yields:
            str: A block of Markdown text, approximately 200 lines each.
        """
        try:  # Lazy import
            import mammoth
        except ImportError as e:
            raise ImportError(
                "The 'mammoth' library is not installed. "
                "Please install it with 'pip install 'mammoth>=1.9.0'' or install the document processing extras "
                "with 'pip install 'chunklet-py[document]''"
            ) from e

        def placeholder_images(image):
            """Replace all images with a placeholder text."""
            return [mammoth.html.text("[Image here]")]

        with open(self.file_path, "rb") as docx_file:
            # Convert DOCX to HTML first
            result = mammoth.convert_to_html(
                docx_file, convert_image=placeholder_images
            )
            html_content = result.value

        # Now we can convert it to markdown
        markdown_content = html_to_md(raw_text=html_content)

        for line_chunk in chunked(markdown_content.splitlines(keepends=True), 200):
            yield "".join(line_chunk)


if __name__ == "__main__":
    file_path = "/storage/emulated/0/Download/sample4.docx"
    processor = DocxProcessor(file_path)

    # Extract metadata
    metadata = processor.extract_metadata()
    print("Metadata:")
    for key, value in metadata.items():
        print(f"{key}: {value}")

    texts = list(processor.extract_text())

    from chunklet import Chunklet

    chunks = Chunklet().batch_chunk(texts=texts, max_sentences=20, overlap_percent=30)

    print("\nText Chunks:")
    for ch in chunks:
        print(ch)
        print("\n //////// \n")
