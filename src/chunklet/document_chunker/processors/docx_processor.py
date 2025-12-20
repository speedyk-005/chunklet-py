from typing import Any, Generator

# mammoth and docx are lazily imported

from chunklet.document_chunker.processors.base_processor import BaseProcessor
from chunklet.document_chunker.converters.html_2_md import html_to_md


class DOCXProcessor(BaseProcessor):
    """
    Processor class for extracting text and metadata from DOCX files.

    Text content is extracted, images are replaced with a placeholder,
    and the resulting text is formatted using Markdown conversion.

    This class extracts **metadata** which typically uses a mix of
    **Open Packaging Conventions (OPC)** properties and elements that align
    with **Dublin Core** standards.

    For more details on the DOCX core properties processed, refer to the
    `python-docx` documentation:
    https://python-docx.readthedocs.io/en/latest/dev/analysis/features/coreprops.html
    """

    METADATA_FIELDS = [
        "title",
        "author",
        "publisher",
        "last_modified_by",
        "created",
        "modified",
        "rights",
        "version",
    ]

    def extract_metadata(self) -> dict[str, Any]:
        """Extracts core properties (a mix of OPC and Dublin Core elements) from the DOCX file.

        Returns:
            dict[str, Any]: A dictionary containing metadata fields:
                - title
                - author
                - publisher
                - last_modified_by
                - created
                - modified
                - rights
                - version
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
        metadata = {"source": str(self.file_path)}
        for field in self.METADATA_FIELDS:
            value = getattr(props, field, "")
            if value:
                metadata[field] = str(value)
        return metadata

    def extract_text(self) -> Generator[str, None, None]:
        """Extracts text content from DOCX file in Markdown format, yielding chunks for efficient processing.

        Images are replaced with a placeholder "[Image - num]".
        Text is yielded in chunks of approximately 4000 characters each to simulate pages and enhance parallel execution.

        Yields:
            str: A chunk of text, approximately 4000 characters each.
        """
        try:  # Lazy import
            import mammoth
        except ImportError as e:
            raise ImportError(
                "The 'mammoth' library is not installed. "
                "Please install it with 'pip install 'mammoth>=1.9.0'' or install the document processing extras "
                "with 'pip install 'chunklet-py[document]''"
            ) from e

        count = 0

        def placeholder_images(image):
            """Replace all images with a placeholder text."""
            nonlocal count
            count += 1
            return [mammoth.html.text(f"[Image - {count}]")]

        with open(self.file_path, "rb") as docx_file:
            # Convert DOCX to HTML first
            result = mammoth.convert_to_html(
                docx_file, convert_image=placeholder_images
            )
            markdown_content = html_to_md(raw_text=result.value)

        # Split into paragraphs and accumulate by character count (~4000 chars per chunk)
        curr_chunk = []
        curr_size = 0
        max_size = 4000

        for paragraph in markdown_content.split("\n\n"):
            para_len = len(paragraph)

            # If adding this paragraph would exceed the limit, yield current chunk
            if curr_size + para_len > max_size and curr_chunk:
                yield "\n\n".join(curr_chunk)
                curr_chunk = []
                curr_size = 0

            curr_chunk.append(paragraph)
            curr_size += para_len

        # Yield any remaining content
        if curr_chunk:
            yield "\n\n".join(curr_chunk)


if __name__ == "__main__":  # pragma: no cover
    file_path = "samples/Lorem Ipsum.docx"
    processor = DOCXProcessor(file_path)

    # Extract metadata
    metadata = processor.extract_metadata()
    print("Metadata:")
    for key, value in metadata.items():
        print(f"{key}: {value}")

    print("\nText content preview:\n")
    for i, text in enumerate(processor.extract_text(), start=1):
        print(f"--- {i} ---")
        print(text[:512], "...")
        print("\n --- \n")
