try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None
import subprocess
from pathlib import Path
import regex as re
import shutil
import warnings
from loguru import logger
from typing import Dict, Any

class PDFProcessor:
    """
    A utility for extracting, cleaning, and processing text from PDF documents.

    This class handles the complexities of PDF text extraction, offering
    features such as:
    - Preserving paragraph structures.
    - Removing standalone numbers that might be artifacts of OCR or layout.
    - Merging accidental single line breaks to maintain text flow.
    - Utilizing `pdftotext` for faster extraction when available, with `pypdf` as a fallback.
    """

    def __init__(self):
        """
        Initializes the PDFProcessor and compiles necessary regex patterns.

        It also checks for the availability of the `pdftotext` utility (from Poppler)
        for potentially faster text extraction, falling back to `pypdf` if not found.
        """
        # Merge accidental single newlines inside paragraphs
        self.single_newline_remover = re.compile(
            r"""
            \n               # a newline
            (?!              # negative lookahead: do not match if...
                \n           # another newline (double newline)
                |            # OR
                [\p{L}\p{N}] # a letter or number
                [.)-]        # followed by ., ), or -
                |            # OR
                [-*]           # An hyphen or asterisk
                |            # OR
                \#\s+           # a # symbol
            )
            """,
            re.UNICODE | re.VERBOSE
        )
        
        # Normalize 3+ consecutive newlines to 2
        self.multiple_newline_normalizer = re.compile(r"(?:\n\s*){3,}")

        # Remove lines containing only numbers
        self.standalone_number_remover = re.compile(r"\n\s*\p{N}+\s*\n")

        # Normalize two or more spaces into a single space
        self.multiple_space_normalizer = re.compile(r"[ ]{2,}")

        # Detect if Poppler (`pdftotext`) is available
        self.use_poppler = shutil.which("pdftotext") is not None
        if not self.use_poppler:
            warnings.warn(
                "Poppler (`pdftotext`) not detected in your environment. Falling back to pypdf, "
                "which works the same but may be slower."
            )

    def _cleanup_text(self, text: str) -> str:
        """
        Cleans and normalizes extracted PDF text.

        This internal method applies a series of regex-based cleaning steps:
        - Normalizes multiple consecutive newlines to ensure consistent paragraph breaks.
        - Removes lines containing only numbers, which are often page numbers or artifacts.
        - Merges single newlines within paragraphs to restore continuous text flow.
        - Normalizes multiple spaces into single spaces for cleaner output.

        Args:
            text (str): The raw text extracted from a PDF page.

        Returns:
            str: The cleaned and normalized text.
        """
        if not text:
            return ""

        # Normalize multiple consecutive newlines
        text = self.multiple_newline_normalizer.sub("\n\n", text)

        # Remove lines containing only numbers
        text = self.standalone_number_remover.sub("\n", text)

        # Merge accidental single newlines inside paragraphs
        text = self.single_newline_remover.sub(" ", text)

        # Normalize multiple spaces into one
        text = self.multiple_space_normalizer.sub(" ", text)

        return text

    def extract_text(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extracts and cleans text from all pages of a PDF, along with its metadata.

        This method attempts to use `pdftotext` for extraction if available,
        otherwise it falls back to `pypdf`. It then applies the internal
        `_cleanup_text` method to each page's content.

        Args:
            pdf_path (str): The absolute path to the PDF file.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - `pages` (List[str]): A list of cleaned text strings, one for each page.
                - `author` (str | None): The author of the document, if available in metadata.
                - `title` (str | None): The title of the document, if available in metadata.
                - `page_count` (int | None): The total number of pages in the document.

        Raises:
            FileNotFoundError: If the specified PDF file does not exist.
            RuntimeError: If `pdftotext` is used and encounters an error during extraction.
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"{pdf_path} does not exist")

        if PdfReader is None and not self.use_poppler:
            raise ImportError(
                "Neither 'pypdf' nor 'pdftotext' (from Poppler) is available. "
                "Please install 'pypdf' with 'pip install pypdf' or install the document processing extras "
                "with 'pip install 'chunklet-py[document]''",
                "or install Poppler and ensure 'pdftotext' is in your PATH."
            )

        pages = []
        metadata = {
            "author": None,
            "title": None,
            "page_count": None,
        }

        # Use pypdf to get metadata regardless of text extraction method
        if PdfReader is not None: 
            try: # Keep a try-except for potential PDF reading errors, but not ImportError
                reader = PdfReader(str(pdf_path))
                info = reader.metadata
                if info:
                    metadata["author"] = info.author
                    metadata["title"] = info.title
                metadata["page_count"] = len(reader.pages)
            except Exception as e: # Catching general exceptions during PDF reading
                logger.warning(f"Could not extract metadata from {pdf_path}: {e}")

        if self.use_poppler:
            # Use pdftotext for faster extraction
            try:
                result = subprocess.run(
                    ["pdftotext", "-layout", str(pdf_path), "-"],
                    capture_output=True,
                    text=True,
                    check=True
                )
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"pdftotext failed: {e}") from e

            # Split output by form feed (\f) to separate pages
            raw_pages = result.stdout.split("\f")
            for page in raw_pages:
                cleaned = self._cleanup_text(page.strip())
                if cleaned:
                    pages.append(cleaned)

        else:
            # Fallback to pypdf
            reader = PdfReader(str(pdf_path))
            for page in reader.pages:
                raw_text = page.extract_text()
                if raw_text:
                    pages.append(self._cleanup_text(raw_text))

        return {"pages": pages, **metadata}


# --- Usage example ---
if __name__ == "__main__":
    # Path to the pdf file
    pdf_path = "samples/Lorem.pdf"
    
    processor = PDFProcessor()

    # The extract_text method returns a dictionary
    result = processor.extract_text(pdf_path)
    pages_text = result.get("pages", [])

    print(f"Author: {result.get('author')}")
    print(f"Title: {result.get('title')}")
    print(f"Page Count: {result.get('page_count')}")
    print("\n" + "=" * 40 + "\n")

    for i, page_text in enumerate(pages_text, start=1):
        print(f"--- Page {i} ---")
        print(page_text)
        print("\n" + "=" * 40 + "\n")
