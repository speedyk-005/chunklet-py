from typing import Any, Generator
import regex as re
from io import StringIO

# pdfminer is lazy imported

from chunklet.document_chunker.processors.base_processor import BaseProcessor


# --- Regex Patterns ---
# Pattern to remove lines with only numbers
STANDALONE_NUMBER_PATTERN = re.compile(r"\n\s*\p{N}+\s*\n", re.U)

# Pattern to collapse multiple whitespace characters into a single space
MULTIPLE_SPACE_PATTERN = re.compile(r"[ ]{2,}")

# Pattern to normalize three or more consecutive newlines
MULTIPLE_NEWLINE_PATTERN = re.compile(r"(\n\s*){3,}")

# Pattern to merge single newlines within logical text blocks
SINGLE_NEWLINE_PATTERN = re.compile(
    r"""
    (?<=             # Match if preceded by..
        [\p{L}\p{N}] # A Unicode letter or a Unicode number
        [.\-)*]      # Followed by a punctuation
    )
    \n               # The newline character to be replaced
    (?!\n)           # Do not match if followed by another newline (true paragraph break)
    """,
    re.U | re.VERBOSE,
)

# Pattern to split words that are incorrectly concatenated with a number
WORD_NUMBER_SPLIT_PATTERN = re.compile(
    r"""
    (\p{L}+)        # Match and capture one or more Unicode letters
    (\p{P})         # Match and capture a punctuation character
    (\p{N}[.\-)*])  # Match and capture a number followed by a symbol
    """,
    re.U | re.VERBOSE,
)


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
            line_margin=0.2,
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
        text = STANDALONE_NUMBER_PATTERN.sub("", text)
        text = MULTIPLE_NEWLINE_PATTERN.sub("\n\n", text)
        text = WORD_NUMBER_SPLIT_PATTERN.sub(r"\1\2 \n\3", text)
        text = MULTIPLE_SPACE_PATTERN.sub(" ", text)
        return text.strip()

    def extract_text(self) -> Generator[str, None, None]:
        """Yield cleaned text from each PDF page.

        Returns:
            Generator[str, None, None]: Cleaned text of each page.
        """
        from pdfminer.high_level import extract_text_to_fp
        from pdfminer.pdfpage import PDFPage

        with open(self.file_path, "rb") as fp:
            for page_num, _ in enumerate(PDFPage.get_pages(fp)):
                buffer = StringIO()
                fp.seek(0)  # reset pointer for each page
                extract_text_to_fp(
                    fp,  # positional: input file
                    buffer,  # positional: output buffer
                    laparams=self.laparams,
                    page_numbers=[page_num],
                )
                yield self._cleanup_text(buffer.getvalue())

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
            parser = PDFParser(f)
            doc = PDFDocument(parser)
            metadata["page_count"] = sum(1 for _ in PDFPage.get_pages(f))
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
    pdf_file = "/storage/emulated/0/Documents/Pdf/Les-bases-de-la-theorie-musicale-EDMProduction.pdf"
    processor = PDFProcessor(pdf_file)

    meta = processor.extract_metadata()
    print("--- Metadata ---")
    for k, v in meta.items():
        print(f"{k}: {v}")

    print("\n--- Pages ---")
    for i, page_text in enumerate(processor.extract_text(), start=1):
        print(f"\n--- Page {i} ---\n{page_text}\n")
