from typing import Any, Generator
import regex as re
from more_itertools import ilen

# pdfminer is lazily imported

from chunklet.document_chunker.processors.base_processor import BaseProcessor


# Pattern to normalize consecutive newlines
MULTIPLE_NEWLINE_PATTERN = re.compile(r"(\n\s*){2,}")

# Pattern to remove lines with only numbers
STANDALONE_NUMBER_PATTERN = re.compile(r"\n\s*\p{N}+\s*\n")

# Pattern to merge single newlines within logical text blocks
HEADING_OR_LIST_PATTERN = re.compile(
    r"(\n"  # A newline
    r"[\p{L}\p{N}]"  # A Unicode letter or a Unicode number
    r"[.\-)*]"  # Followed by a punctuation
    r")\n",  # The newline character to be replaced
    re.U,
)

PAGE_PATTERN = re.compile(
    r"Page \p{N}+ of \p{N}+.*|"  # standalone page number
    r"-\s*\p{N}+\s*-|"  # Page numbers with dashes
    r"\s*\|\s*Page\s+\p{N}+\s*\|\s*",  # Boxed page numbers
    re.M,
)


class PDFProcessor(BaseProcessor):
    """
    PDF extraction and cleanup utility using `pdfminer.six`.

    Provides methods to extract text and metadata from PDF files,
    while cleaning and normalizing the extracted text using regex patterns.

    This processor extracts **metadata** from the PDF document's **information
    dictionary**, focusing on core metadata rather than all available fields.

    For more details on PDF metadata extraction using `pdfminer.six`, refer to
    this relevant Stack Overflow discussion:

    https://stackoverflow.com/questions/75591385/extract-metadata-info-from-online-pdf-using-pdfminer-in-python
    """

    METADATA_FIELDS = [
        "title",
        "author",
        "creator",
        "producer",
        "publisher",
        "created",
        "modified",
    ]

    def __init__(self, file_path: str):
        """Initialize the PDFProcessor.

        Args:
            file_path (str): Path to the PDF file.
        """
        try:
            from pdfminer.layout import LAParams
        except ImportError as e:
            raise ImportError(
                "The 'pdfminer.six' library is not installed. "
                "Please install it with 'pip install 'pdfminer.six>=20250324'' or install the document processing extras "
                "with 'pip install 'chunklet-py[document]''"
            ) from e
        self.file_path = file_path
        self.laparams = LAParams(
            line_margin=0.5,
        )

    def _cleanup_text(self, text: str) -> str:
        """Clean and normalize extracted PDF text.

        Performs:
            - Collapse multiple newlines
            - Remove lines containing only numbers (page numbers)
            - Split concatenated words with punctuation and numbers
            - Collapse multiple spaces
            - Remove zero-width / non-breaking characters

        Args:
            text (str): Raw text extracted from PDF page.

        Returns:
            str: Cleaned and normalized text.
        """
        if not text:
            return ""
        text = MULTIPLE_NEWLINE_PATTERN.sub("\n", text)
        text = HEADING_OR_LIST_PATTERN.sub(r"\1 ", text)
        text = STANDALONE_NUMBER_PATTERN.sub("", text)
        text = PAGE_PATTERN.sub("", text)
        return text

    def _safe_decode(self, value: str | bytes):
        """Utility to decode bytes to str, ignoring errors, otherwise return as-is.

        Args:
            value (str | bytes): The input value, which may be a string or a byte sequence.

        Returns:
            str: The decoded string if the input was bytes, or the original string
                 if the input was already a string.
        """
        if isinstance(value, bytes):
            return value.decode("utf-8", "ignore")
        return value

    def extract_text(self) -> Generator[str, None, None]:
        """Yield cleaned text from each PDF page.

        Extracts text content page by page using pdfminer.high_level.extract_text
        for efficient processing. Each page is processed individually to avoid
        memory issues with large PDF files. The extracted text is cleaned using
        the _cleanup_text method to remove artifacts and normalize formatting.

        Yields:
            str: Cleaned text content from each PDF page.
        """
        from pdfminer.high_level import extract_text
        from pdfminer.pdfpage import PDFPage

        with open(self.file_path, "rb") as fp:
            page_count = ilen(PDFPage.get_pages(fp))

            for page_num in range(page_count):
                # Call extract_text on the file path, specifying the page number.
                # This is efficient as it avoids repeated file seeks/parsing
                # within the loop that was present in the old `extract_text_to_fp` approach.
                raw_text = extract_text(
                    self.file_path,
                    page_numbers=[page_num],
                    laparams=self.laparams,
                )
                yield self._cleanup_text(raw_text)

    def extract_metadata(self) -> dict[str, Any]:
        """Extracts metadata from the PDF document's information dictionary.

        Includes source path, page count, and PDF info fields.

        Returns:
            dict[str, Any]: A dictionary containing metadata fields:
                - title
                - author
                - creator
                - producer
                - publisher
                - created
                - modified
        """
        from pdfminer.pdfpage import PDFPage
        from pdfminer.pdfparser import PDFParser
        from pdfminer.pdfdocument import PDFDocument

        metadata = {"source": str(self.file_path), "page_count": 0}
        with open(self.file_path, "rb") as f:
            # Initialize parser on the file stream
            parser = PDFParser(f)

            # The PDFDocument constructor reads file structure and advances the pointer
            doc = PDFDocument(parser)

            # Count pages: Reset pointer to the start of the file stream to count pages correctly
            f.seek(0)

            metadata["page_count"] = ilen(PDFPage.get_pages(f))

            # Extract info fields from the document object
            if hasattr(doc, "info") and doc.info:
                for info in doc.info:
                    for k, v in info.items():
                        k = self._safe_decode(k)
                        v = self._safe_decode(v)

                        # To keep metadata uniform with the other processorss
                        k = "created" if k == "CreationDate" else k
                        k = "modified" if k == "ModDate" else k

                        if k.lower() in self.METADATA_FIELDS:
                            metadata[k.lower()] = v
        return metadata


# --- Example usage ---
if __name__ == "__main__":  # pragma: no cover
    pdf_file = "samples/sample-pdf-a4-size.pdf"

    processor = PDFProcessor(pdf_file)
    meta = processor.extract_metadata()

    print("Metadata:")
    for k, v in meta.items():
        print(f"{k}: {v}")

    print("\nText content preview:\n")
    for i, page_text in enumerate(processor.extract_text(), start=1):
        print(f"--- page {i} ---")
        print(page_text[:512], "...")
        print("\n --- \n")
