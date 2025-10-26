from __future__ import annotations
import regex as re
from typing import Any, Iterator


class PDFProcessor:
    """
    A comprehensive utility class designed for the extraction, cleansing, and
    structured processing of text from PDF documents.
    """

    def __init__(self):
        # Pattern to merge single newlines within logical text blocks
        self.single_newline_pattern = re.compile(
            r"""
            (?<=             # Positive lookbehind: match if preceded by...
                [\p{L}\p{N}] # A Unicode letter or a Unicode number
                [.\-)*]      # Followed by a period, hyphen, closing parenthesis, or asterisk
            )
            \n               # The newline character to be replaced
            (?!              # Negative lookahead: do not match if followed by...
                \n           # A second consecutive newline (which signifies a true paragraph break)
            )
            """,
            re.UNICODE | re.VERBOSE,
        )

        # Pattern to normalize three or more consecutive newlines
        self.multiple_newline_pattern = re.compile(r"(?:\n\s*){3,}")

        # Pattern to remove lines with only numbers
        self.standalone_number_pattern = re.compile(r"\n\s*\p{N}+\s*\n", re.UNICODE)

        # Pattern to collapse multiple whitespace characters into a single space
        self.multiple_space_pattern = re.compile(r"[ ]{2,}")

        # Pattern to split words that are incorrectly concatenated with a number
        self.word_number_split_pattern = re.compile(
            r"""
            (
                \p{L}+         # Match and capture one or more Unicode letters (Group 1)
            )
            (
                \p{P}          # Match and capture a single Unicode punctuation character (Group 2)
            )
            (
                \p{N}[.\-)*]   # Match and capture a Unicode number followed by a period, hyphen, etc. (Group 3)
            )
            """,
            re.UNICODE | re.VERBOSE,
        )

    def _cleanup_text(self, text: str) -> str:

        """Cleans and normalizes extracted PDF text."""

        if not text:

            return ""

    

        text = self.multiple_newline_pattern.sub("\n\n", text)

        text = self.standalone_number_pattern.sub("\n", text)

        text = self.single_newline_pattern.sub(" ", text)

        text = self.word_number_split_pattern.sub(r"\1\2 \n\3", text)

        text = self.multiple_space_pattern.sub(" ", text)

    

        return text

    def extract_data(self, pdf_path: str) -> dict[str, Any]:
        """
        Extracts both metadata and cleaned, page-by-page text from a PDF document.
        Returns metadata and a generator for page content.
        """
        try:
            from pypdf import PdfReader
        except ImportError as e:
            raise ImportError(
                "The 'pypdf' library is not installed. Please install it with 'pip install 'pypdf>=5.0.8'' or "
                "install the document processing extras with 'pip install chunklet-py[document]'"
            ) from e

        # Inner generator function to process pages one by one
        def _extract_pages_generator(
            reader_obj: PdfReader, f_handle: Any
        ) -> Iterator[str]:
            for page in reader_obj.pages:
                text = page.extract_text()
                if text:
                    yield self._cleanup_text(text)
            # Explicitly close the file handle after all pages are processed
            f_handle.close()

        # Open the file and keep it open for the duration of the generator's use.
        # The file handle `f` is passed to the generator.
        file_handle = open(pdf_path, "rb")
        reader = PdfReader(file_handle)
        page_count = len(reader.pages)
        doc_metadata = reader.metadata

        metadata = {"source": pdf_path, "page_count": page_count}
        if doc_metadata:
            for key, value in doc_metadata.items():
                clean_key = key[1:] if key.startswith("/") else key
                metadata[clean_key.lower()] = value

        return {
            "metadata": metadata,
            "pages": _extract_pages_generator(reader, file_handle),
        }


# --- Usage example ---
if __name__ == "__main__":
    pdf_path = "samples/sample-pdf-a4-size.pdf"

    processor = PDFProcessor()

    result = processor.extract_data(pdf_path)

    # Print extracted metadata
    print("--- Metadata ---")
    for k, v in result["metadata"].items():
        print(f"{k}: {v}")

    # Iterate over the pages using the generator
    print("\n--- Page Content ---")
    try:
        for i, page_text in enumerate(result["pages"], start=1):
            print(f"\n--- Page {i} ---")
            print(page_text)
            print("\n" + "=" * 40 + "\n")
    except ValueError as e:
        print(f"An error occurred during page processing: {e}")
        print("This might be due to the file being closed prematurely.")
