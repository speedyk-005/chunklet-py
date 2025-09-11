from __future__ import annotations
import subprocess
from pathlib import Path
import regex as re
from loguru import logger
from typing import Any 

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
        # Pattern to merge accidental single newlines inside lists or headings
        self.single_newline_pattern = re.compile(
            r"""
            (?<=             # match if preceded by...
                [\p{L}\p{N}] # a letter or number
                [.\-)*]       # followed by ., -, ), or * (FIXED: The hyphen is escaped)
            )
            \n               # match a newline
            (?! 
                \n           # do not match if followed by another newline
            )
            """,
            re.UNICODE | re.VERBOSE,
        )

        # Pattern to normalize 3+ consecutive newlines to 2
        self.multiple_newline_pattern = re.compile(r"(?:\n\s*){3,}")

        # Pattern to remove lines containing only numbers
        self.standalone_number_pattern = re.compile(
            r"\n\s*\p{N}+\s*\n",
            re.UNICODE
        )

        # Pattern to normalize two or more spaces into a single space
        self.multiple_space_pattern = re.compile(r"[ ]{2,}")
        
        # Split a word that's immediately followed by a number
        # e.g., "report.1." -> "report.\n1."
        self.word_number_split_pattern = re.compile(
            r"(\p{L}+)(\p{P})(\p{N}[.\-)*])",
            re.UNICODE
        )

    def _cleanup_text(self, text: str) -> str:
        """
        Cleans and normalizes extracted PDF text.

        This internal method applies a series of regex-based cleaning steps:
        - Normalizes multiple consecutive newlines to ensure consistent paragraph breaks.
        - Removes lines containing only numbers, which are often page numbers or artifacts.
        - Merges single newlines within paragraphs to restore continuous text flow.
        - Splits words that are incorrectly attached to a number.
        - Normalizes multiple spaces into single spaces for cleaner output.

        Args:
            text (str): The raw text extracted from a PDF page.

        Returns:
            str: The cleaned and normalized text.
        """ 
        if not text:
            return ""

        # Normalize multiple consecutive newlines
        text = self.multiple_newline_pattern.sub("\n\n", text)

        # Remove lines containing only numbers
        text = self.standalone_number_pattern.sub("\n", text)

        # Merge accidental single newlines inside paragraphs
        text = self.single_newline_pattern.sub(" ", text)

        # Detach words from numbers, 
        text = self.word_number_split_pattern.sub(r"\1\2 \n\3", text)

        # Normalize multiple spaces into one
        text = self.multiple_space_pattern.sub(" ", text)

        return text

    def extract_text(self, pdf_path: str) -> dict[str, Any]:
        """
        Extracts and cleans text from all pages of a PDF, along with its metadata.

        This method uses `pypdf` for extraction then clean each page's content. 
        It also extracts the document metadata alongside.

        Args:
            pdf_path (str): The absolute path to the PDF file.

        Returns:
            dict[str, Any]: A dictionary containing:
                - `pages` (list[str]): A list of cleaned text strings, one for each page.
                - Other metadata like page_count, Author, ...
        """
        try:
            from pypdf import PdfReader # Lazy import
        except ImportError as e:
            raise ImportError(
                "The 'pypdf' library is not installed. Please install it with 'pip install pypdf' or install the document processing extras with 'pip install chunklet-py[document]'"
            ) from e
            
        # Extract text and metadat then combine them.
        with open(pdf_path, "rb") as file:
            reader = PdfReader(file)
            page_count = len(reader.pages)

            # Extract metadata from the document
            metadata = {
                    "source": pdf_path,
                    "page_count": page_count  
                }
            doc_metadata = reader.metadata

            if doc_metadata:
                # Add all metadata fields to our dictionary
                for key, value in doc_metadata.items():
                    # Sanitize keys by removing leading slash if present
                    clean_key = key[1:] if key.startswith('/') else key
                    metadata[clean_key] = value

            # Extract pages content
            pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    cleaned_text = self._cleanup_text(text)
                    pages.append(cleaned_text)  
                
        return {"pages": pages, **metadata}


# --- Usage example ---
if __name__ == "__main__":
    # Path to the pdf file
    pdf_path = "samples/sample-pdf-a4-size.pdf"

    processor = PDFProcessor()

    # The extract_text method returns a dictionary
    result = processor.extract_text(pdf_path)
    pages_text = result["pages"]
    
    for k, v in result.items():
        if k != "pages":
            print(f"{k}: {v}")
            
    for i, page_text in enumerate(pages_text, start=1):
        print(f"\n--- Page {i} ---")
        print(page_text)
        print("\n" + "=" * 40 + "\n")
