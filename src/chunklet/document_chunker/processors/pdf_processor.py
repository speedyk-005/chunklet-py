from typing import Any, Generator
from io import StringIO
import regex as re
from more_itertools import ilen

# pdfminer is lazy imported

from chunklet.document_chunker.processors.base_processor import BaseProcessor


# --- Regex Patterns ---

# Pattern to normalize consecutive newlines
MULTIPLE_NEWLINE_PATTERN = re.compile(r"(\n\s*){2,}")

# Pattern to remove lines with only numbers
STANDALONE_NUMBER_PATTERN = re.compile(r"\n\s*\p{N}+\s*\n", re.U)

# Pattern to merge single newlines within logical text blocks
HEADING_OR_LIST_PATTERN = re.compile(
    r"""
    (
        \n             # A newline
        [\p{L}\p{N}] # A Unicode letter or a Unicode number
        [.\-)*]       # Followed by a punctuation
    )
    \n                 # The newline character to be replaced
    """,
    re.U | re.VERBOSE,
)

# --- PDF Processor Class ---

class PDFProcessor(BaseProcessor):
    """PDF extraction and cleanup utility using pdfminer.six.

    Provides methods to extract text and metadata from PDF files,
    while cleaning and normalizing the text using regex patterns.
    """

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
        return text

    def extract_text(self) -> Generator[str, None, None]:
        """Yield cleaned text from each PDF page.

        Uses pdfminer.high_level.extract_text for efficient page-by-page extraction.

        Returns:
            Generator[str, None, None]: Cleaned text of each page.
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
        """Extract PDF metadata.

        Includes source path, page count, and PDF info fields.

        Returns:
            dict[str, Any]: Metadata dictionary.
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
                        if isinstance(k, bytes):
                            k = k.decode("utf-8", "ignore")
                        if isinstance(v, bytes):
                            v = v.decode("utf-8", "ignore")
                        metadata[k.lower()] = v
        return metadata


# --- Example usage ---
if __name__ == "__main__":
    pdf_file = "samples/sample-pdf-a4-size.pdf"
    
    try:
        processor = PDFProcessor(pdf_file)

        meta = processor.extract_metadata()
        print("--- Metadata ---")
        for k, v in meta.items():
            print(f"{k}: {v}")

        print("\n--- Pages ---")
        for i, page_text in enumerate(processor.extract_text(), start=1):
            print(f"\n--- Page {i} ---\n{page_text[:500]}...\n")
    except ImportError as e:
        print(f"Error: {e}")