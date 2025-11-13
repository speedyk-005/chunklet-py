from typing import Any
from collections.abc import Generator

try:
    from ebooklib import epub
except ImportError:
    epub = None

from chunklet.document_chunker.processors.base_processor import BaseProcessor
from chunklet.document_chunker.converters.html_2_md import html_to_md


class EpubProcessor(BaseProcessor):
    """Processor class for extracting text and metadata from EPUB files."""

    METADATA_FIELDS = [
            "title",
            "creator",
            "contributor",
            "language",
            "subject",
            "publisher",
            "date",
            "rights",
        ] 
    
    def __init__(self, file_path: str):
        """
        Initializes the EpubProcessor with a path to the EPUB file
        and reads the EPUB book into memory.

        Args:
            file_path (str): Path to the EPUB file.
        """
        if not epub:
            raise ImportError(
                "The 'ebooklib' library is not installed. "
                "Please install it with 'pip install 'ebooklib>=0.19'' or install the document processing extras "
                "with 'pip install 'chunklet-py[document]''"
            )
        self.file_path = file_path
        self.book = epub.read_epub(file_path)

    def extract_metadata(self) -> dict[str, Any]:
        """
        Extracts metadata from the EPUB file limited to Dublin Core fields.

        Returns:
            dict[str, Any]: A dictionary containing metadata keys and their string values.
        """
        metadata = {"source": str(self.file_path)}
        for field in self.METADATA_FIELDS:
            values = [v[0] for v in self.book.get_metadata("DC", field)]
            if values:
                metadata[field] = ", ".join(values)
        return metadata

    def extract_text(self) -> Generator[str, None, None]:
        """
        Yields Markdown-converted text from all document items in the EPUB file.

        Yields:
            str: Markdown-formatted text of each document item.
        """
        for idref, _ in self.book.spine:
            item = self.book.get_item_with_id(idref)
            html_content = item.get_body_content().decode("utf-8", errors="ignore")
            md_content = html_to_md(raw_text=html_content)
            yield md_content.strip()


# Example usage
if __name__ == "__main__":
    file_path = "samples/minimal.epub"
    processor = EpubProcessor(file_path)

    metadata = processor.extract_metadata()
    print("Metadata:")
    for k, v in metadata.items():
        print(f"{k}: {v}")
    print("\nText content preview:\n")

    for no, t in enumerate(processor.extract_text(), start=1):
        print(f"### {no} ###")
        print(t[:512], "...")
        print("\n///*******/////\n")
