from typing import Any, Generator

# odfpy is lazy imported

from chunklet.document_chunker.processors.base_processor import BaseProcessor


class ODTProcessor(BaseProcessor):
    """
    ODT extraction and processing utility using `odfpy`.

    Provides methods to extract text and metadata from ODT (OpenDocument Text) files,
    while processing the extracted text into manageable chunks.

    This processor extracts **metadata** from the ODT document's **Dublin Core** and
    **OpenDocument** standard properties.

    For more details on ODF metadata fields and `odfpy` usage, refer to:
    https://odfpy.readthedocs.io/en/latest/
    """

    def __init__(self, file_path: str):
        """Initialize the ODTProcessor.

        Args:
            file_path (str): Path to the ODT file.
        """
        try:
            from odf.opendocument import load

            self._load_odf = load
        except ImportError as e:
            raise ImportError(
                "The 'odfpy' library is not installed. "
                "Please install it with 'pip install odfpy>=1.4.1' "
                "or install the document processing extras with "
                "'pip install chunklet-py[document]'"
            ) from e

        self.file_path = file_path
        self.doc = self._load_odf(self.file_path)

    def extract_metadata(self) -> dict[str, Any]:
        """Extracts metadata from the ODT file, focusing on Dublin Core and OpenDocument fields.

        Parses the document's metadata elements, extracting fields such as:

        Only present fields are included in the returned dictionary.

        Returns:
            dict[str, Any]: A dictionary containing metadata fields:
                 - title
                 - creator
                 - initial_creator
                 - created
                 - chapter
                 - author_name

        """
        from odf import text, meta, dc

        metadata = {}
        for field in [
            dc.Title,
            dc.Creator,
            meta.InitialCreator,
            meta.CreationDate,
            text.Chapter,
            text.AuthorName,
        ]:
            elems = self.doc.getElementsByType(field)
            value = "".join(
                node.data
                for e in elems
                for node in e.childNodes
                if node.nodeType == node.TEXT_NODE
            ).strip()
            if value:  # Only store if not empty
                key = field.__name__

                # To keep metadata uniform with the other processors
                key = "created" if key == "CreationDate" else key
                key = "author" if key == "Creator" else key
                key = "creator" if key == "InitialCreator" else key

                metadata[key.lower()] = value

        metadata["source"] = str(self.file_path)
        return metadata

    def extract_text(self) -> Generator[str, None, None]:
        """Extracts text content from ODT paragraphs, yielding chunks for efficient processing.

        Iterates through paragraph elements in the document, extracting text content
        and buffering it into chunks of approximately 4000 characters. This allows for memory-efficient
        processing of large documents by yielding text blocks that simulate pages and enhance parallel execution.

        Yields:
            str: A chunk of text, approximately 4000 characters each.
        """
        from odf import text

        curr_chunk = []
        curr_size = 0
        max_size = 4000

        for p_elem in self.doc.getElementsByType(text.P):
            para_text = "".join(
                node.data
                for node in p_elem.childNodes
                if node.nodeType == node.TEXT_NODE
            ).strip()
            if not para_text:
                continue

            para_len = len(para_text)

            # If adding this paragraph would exceed the limit, yield current chunk
            if curr_size + para_len > max_size and curr_chunk:
                yield "\n".join(curr_chunk)
                curr_chunk = []
                curr_size = 0

            curr_chunk.append(para_text)
            curr_size += para_len

        # Yield any remaining content
        if curr_chunk:
            yield "\n".join(curr_chunk)


if __name__ == "__main__":  # pragma: no cover
    file_path = "samples/file-sample_100kB.odt"
    processor = ODTProcessor(file_path)

    # Extract metadata
    metadata = processor.extract_metadata()
    print("Metadata:")
    for key, value in metadata.items():
        print(f"{key}: {value}")

    print("\nText content preview:\n")
    for i, chunk in enumerate(processor.extract_text(), start=1):
        print(f"--- {i} ---")
        print(chunk, "...")
        print("\n --- \n")
