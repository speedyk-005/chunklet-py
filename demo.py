from typing import Any, Generator, Iterable, List
import regex as re
from more_itertools import ilen

# NOTE: This processor uses the 'paves' library, which assumes its base 
# library (referred to as 'playa' in the docs) is available.
# Installation requirement: pip install paves

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

# --- Utility Function to Extract Text Containers ---

def find_text_containers(layout_obj: Any, containers: List[Any]) -> None:
    """
    Recursively searches for LTTextBox-like objects within the layout tree.
    """
    # LTTextBoxHorizontal is the common text container in pdfminer/paves.
    # We check for a common attribute like 'get_text' and the 'bbox' attribute 
    # which is common for all layout components, but only append text boxes.
    if hasattr(layout_obj, "get_text") and not hasattr(layout_obj, "children"):
        # If it has get_text but no children, it's a leaf text element (like LTTextLine). 
        # This can be messy; we prefer to handle LTTextBox-like containers.
        pass
    elif hasattr(layout_obj, "get_text") and hasattr(layout_obj, "children"):
        # This is a good candidate (e.g., LTTextBoxHorizontal)
        containers.append(layout_obj)
        # Stop recursion down this branch as we want the text box's aggregate text.
        return

    # Continue recursion for layout containers
    if hasattr(layout_obj, "iter_layout"):
        children = layout_obj.iter_layout()
    elif hasattr(layout_obj, "children") and isinstance(layout_obj.children, Iterable):
        children = layout_obj.children
    else:
        children = []

    for child in children:
        find_text_containers(child, containers)


# --- PDF Processor Class ---

class PDFProcessor(BaseProcessor):
    """PDF extraction and cleanup utility using the paves/playa stack.

    Provides methods to extract text and metadata from PDF files,
    while cleaning and normalizing the text using regex patterns.
    """

    def __init__(self, file_path: str):
        """Initialize the PDFProcessor.

        Args:
            file_path (str): Path to the PDF file.
        """
        try:
            # Import necessary classes from paves.miner/pdfminer for LAParams compatibility
            from paves.miner import LAParams
            # Test for 'playa' which is the required base
            import playa
        except ImportError as e:
            raise ImportError(
                "The 'paves' and 'playa' libraries are not installed. "
                "Please install them with 'pip install paves' or install the document processing extras "
                "with 'pip install 'chunklet-py[document]''"
            ) from e
        self.file_path = file_path
        # LAParams is available through paves.miner for compatibility with its API
        self.laparams = LAParams(
            line_margin=0.5,
        )

    def _cleanup_text(self, text: str) -> str:
        """Clean and normalize extracted PDF text.
        ... (Cleanup logic remains unchanged) ...
        """
        if not text:
            return ""
        # Apply cleanup and normalization
        text = MULTIPLE_NEWLINE_PATTERN.sub("\n", text)
        text = HEADING_OR_LIST_PATTERN.sub(r"\1 ", text)
        text = STANDALONE_NUMBER_PATTERN.sub("", text)
        return text

    def extract_text(self, max_workers: int = 1) -> Generator[str, None, None]:
        """Yield cleaned text from each PDF page using paves.miner.

        Args:
            max_workers (int): Number of worker processes to use for parallel extraction. 
                               Defaults to 1 (single-process).

        Returns:
            Generator[str, None, None]: Cleaned text of each page.
        """
        from paves.miner import extract
        
        # Use paves.miner.extract, passing max_workers for parallel processing
        for page_layout in extract(
            self.file_path, 
            laparams=self.laparams, 
            max_workers=max_workers
        ):
            text_boxes = []
            
            # Use the recursive helper to find all LTTextBox-like objects
            find_text_containers(page_layout, text_boxes)
            
            page_raw_texts = []
            for box in text_boxes:
                # LTTextBoxHorizontal.get_text() returns the combined text of its children (LTTextLines), 
                # usually with internal newlines already included.
                text = box.get_text()
                if text:
                    page_raw_texts.append(text.strip())

            # Join the text from different text boxes with two newlines for paragraph separation
            raw_text = '\n\n'.join(page_raw_texts).strip()
            
            yield self._cleanup_text(raw_text)

    def extract_metadata(self) -> dict[str, Any]:
        """Extract PDF metadata using the playa library.
        ... (Metadata logic remains unchanged) ...
        """
        import playa
        
        metadata = {"source": str(self.file_path), "page_count": 0}
        
        # Open the PDF using the playa object model
        pdf = playa.open(self.file_path)

        # Get page count directly from the 'pages' attribute
        metadata["page_count"] = len(pdf.pages)
        
        # Extract document info fields
        if hasattr(pdf, "info") and pdf.info:
            
            # 1. Iterate through the list of info dictionaries (confirmed structure: [dict])
            for info_dict in pdf.info:
                
                # 2. Iterate through the items of the dictionary
                for k, v in info_dict.items(): 
                    
                    # 3. Decode byte strings into standard strings (confirmed by inspection)
                    if isinstance(v, bytes):
                        v = v.decode("utf-8", "ignore")
                        
                    # Key 'k' usually appears as a string, but adding a safe guard for consistency
                    if isinstance(k, bytes):
                        k = k.decode("utf-8", "ignore")
                        
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

        print("\n--- Pages (Using max_workers=2 for parallel processing) ---")
        # Use max_workers > 1 to leverage multiple CPU cores
        for i, page_text in enumerate(processor.extract_text(max_workers=2), start=1):
            # Print the content using slicing to demonstrate content exists
            print(f"\n--- Page {i} ---\n{page_text[:500]}...\n")
    except ImportError as e:
        print(f"Error: {e}")