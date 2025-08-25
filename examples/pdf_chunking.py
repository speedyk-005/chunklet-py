import regex as re
try:
    from pypdf import PdfReader
except ImportError:
    print("pypdf not found. Please install it with: pip install pypdf")
    exit()
from chunklet import Chunklet

class PDFProcessor:
    """
    Extract, clean, and chunk PDF text by sentences.
    Preserves meaningful newlines like headings and numbered lists,
    removes standalone numbers, and chunks pages using Chunklet.
    """

    def __init__(self, pdf_path: str, chunker=None):
        self.pdf_path = pdf_path
        # Use Chunklet for sentence-based chunking
        self.chunker = chunker or Chunklet(verbose=False, use_cache=True)

    def extract_text(self):
        """Extracts and cleans text from all pages of the PDF."""
        reader = PdfReader(self.pdf_path)
        return [
            self._cleanup_text(page.extract_text())
            for page in reader.pages
            if page.extract_text()
        ]

    def _cleanup_text(self, text: str):
        """Clean text, preserving meaningful newlines and removing standalone numbers."""
        if not text:
            return ""

        # Normalize 3+ consecutive newlines to 2
        text = re.sub(r"(?:\n\s*){3,}", "\n\n", text)

        # Remove lines that contain only numbers
        text = re.sub(r"\n\s*\p{N}+\s*\n", "\n", text)

        # Patterns for numbered lists and headings
        numbered = re.compile(r"\n(\d+\) .+?)\n")
        heading = re.compile(r"\n\s*#*\s*[\p{L}\p{N}].*?\n")

        # Merge accidental line breaks that are NOT numbered lists or headings
        text = re.sub(r"(?<!\n)\n(?!\d+\)|[\p{L}\p{N}])", " ", text)

        # Reapply patterns to preserve newlines
        text = numbered.sub(r"\n\1\n", text)
        text = heading.sub(lambda m: "\n" + m.group(0).strip() + "\n", text)

        return text

    def batch_chunk_pages(self, max_sentences=5):
        """Extract text and chunk all pages using sentence mode (safe for mobile)."""
        pages_text = self.extract_text()  # list of page texts
        all_chunks = self.chunker.batch_chunk(
            pages_text,
            mode="sentence",       # sentence-based chunking
            max_sentences=max_sentences,
            n_jobs=1,              # single-threaded to avoid mpire issues
            lang="fr"
        )
        return all_chunks


# --- Usage example ---
pdf_path = "examples/Les-bases-de-la-theorie-musicale-EDMProduction 1.pdf"
processor = PDFProcessor(pdf_path)

# Chunk all pages by sentences
pages_chunks = processor.batch_chunk_pages(max_sentences=15)

# Print the chunks per page
for i, page_chunks in enumerate(pages_chunks, start=1):
    print(f"--- Page {i} Chunks ---")
    for j, chunk in enumerate(page_chunks, start=1):
        print(f"Chunk {j}: {chunk}\n")
    print("="*50 + "\n")