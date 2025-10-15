from pathlib import Path
from typing import Callable, Literal, Any, Generator
from collections.abc import Iterable
from pydantic import conint
from box import Box
from loguru import logger
try:
    from striprtf.striprtf import rtf_to_text
except ImportError:
    rtf_to_text = None

from chunklet.plain_text_chunker import PlainTextChunker
from chunklet.document_chunker.pdf_processor import PDFProcessor
from chunklet.document_chunker.docx_processor import DOCXProcessor
from chunklet.document_chunker.rst_to_md import rst_to_markdown
from chunklet.document_chunker.registry import is_registered, use_registered_processor
from chunklet.utils.validation import validate_input
from chunklet.exceptions import (
    InvalidInputError,
    UnsupportedFileTypeError,
    FileProcessingError,
)


class DocumentChunker:
    """
    A comprehensive document chunker that handles various file formats.

    This class provides a high-level interface to chunk text from different
    document types. It automatically detects the file format and uses the
    appropriate method to extract content before passing it to an underlying
    `PlainTextChunker` instance.

    Key Features:
    - Multi-Format Support: Chunks text from PDF, DOCX, TXT, MD, and RST files.
    - Metadata Enrichment: Automatically adds source file path and other
      document-level metadata (e.g., PDF page numbers) to each chunk.
    - Bulk Processing: Efficiently chunks multiple documents in a single call.
    - Pluggable Document processors: Integrate custom processors allowing definition
    of specific logic for extracting text from various file types.
    """

    # Supported file extensions for general-purpose text documents
    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".rst", ".rtf"}

    @validate_input
    def __init__(
        self,
        verbose: bool = True,
        plain_text_chunker: Any | None = None,
    ):
        """
        Initializes the DocumentChunker.

        Args:
            verbose (bool): If True, enables verbose logging. Defaults to True.
            plain_text_chunker (PlainTextChunker | None): An optional PlainTextChunker instance.
                If None, a default PlainTextChunker will be initialized.

        Raises:
            InvalidInputError: If any of the input arguments are invalid or if the provided `plain_text_chunker` is not an instance of `PlainTextChunker`.
        """
        self._verbose = verbose

        # Explicit type validation for plain_text_chunker
        if plain_text_chunker is not None and not isinstance(
            plain_text_chunker, PlainTextChunker
        ):
            raise InvalidInputError(
                f"The provided plain_text_chunker must be an instance of PlainTextChunker, "
                f"but got {type(plain_text_chunker).__name__}."
            )

        self.plain_text_chunker = plain_text_chunker or PlainTextChunker(
            verbose=self._verbose
        )

        if self._verbose:
            logger.debug(
                "DocumentChunker initialized with verbose={}.",
                self._verbose,
            )

        self.pdf_processor = PDFProcessor()
        self.docx_processor = DOCXProcessor()

    @property
    def verbose(self) -> bool:
        """Get the verbosity status."""
        return self._verbose

    @verbose.setter
    def verbose(self, value: bool):
        """Set the verbosity and propagate to plain_text_chunker."""
        self._verbose = value
        self.verbose = value

    def _validate_path_extension(self, path: str | Path) -> str:
        """
        Validates the file path and returns its lowercase extension.

        This method ensures the path exists and the file type is supported.

        Args:
            path (str | Path): The path to the document file.

        Returns:
            str: The file's lowercase extension.

        Raises:
            InvalidInputError: If the path is invalid or cannot be resolved.
            FileNotFoundError: If provided file path not found.
            UnsupportedFileTypeError: If the file extension is not supported.
        """
        path = Path(str(path))
        extension = path.suffix.lower()

        if not extension:
            raise InvalidInputError(
                f"Invalid path '{path}' provided. Path must have a recognizable extension."
            )

        if not path.is_file():
            raise FileNotFoundError(f"The file '{path}' can't be found.")

        if extension not in self.SUPPORTED_EXTENSIONS and not is_registered(extension):
            raise UnsupportedFileTypeError(
                f"File type '{extension}' is not supported.\n"
                f"Supported extensions are: {self.SUPPORTED_EXTENSIONS}\n"
                "💡 Hint: You can add support for other file types by providing a custom processor."
            )

        return extension

    def _extract_text(self, path: str | Path, ext: str) -> str:
        """
        Extracts the content of a text-based file, including DOCX, and performs
        necessary conversions.

        Args:
            path (str | Path): The path to the file.
            ext (str): The file extension (e.g., ".txt", ".rst", ".docx").

        Returns:
            str: The content of the file as a string.
        """
        if self.verbose:
            logger.debug("Extracting text from file: {} with extension: {}", path, ext)

        try:
            if ext == ".docx":
                return self.docx_processor.extract_text(path)

            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                raw_content = f.read()

            if ext == ".rst":
                return rst_to_markdown(raw_content)
            elif ext == ".rtf":
                if rtf_to_text is None:
                    raise ImportError(
                        "The 'striprtf' library is not installed. Please install it with 'pip install striprtf' or install the document processing extras with 'pip install chunklet-py[document]'"
                    )
                return rtf_to_text(raw_content)
            else:  # For .txt, .md, and others handled by simple read
                return raw_content

        except Exception as e:
            raise FileProcessingError(
                f"Error extracting text from file {path}.\n Details: {e}"
            ) from e

    def _create_chunk_boxes(
        self,
        chunks: Iterable[str],
        base_metadata: dict[str, Any],
    ) -> list[Box]:
        """
        Helper to create a list of Box objects for chunks with embedded metadata and auto-assigned chunk numbers.



        Args:
            chunks (Iterable[str]): An iterable (e.g., list or generator) of raw text strings,
                                    each representing a chunk of content.
            base_metadata (dict[str, Any]): A dictionary containing document-level metadata
                                            (e.g., 'source' file path, 'page_count' for PDFs)
                                            to be embedded into each chunk's metadata.

        Returns:
            list[Box]: A list of `Box` objects. Each `Box` contains:
                       - 'content' (str): The text of the chunk.
                       - 'metadata' (dict): A dictionary including 'chunk_num' (int)
                                            and all key-value pairs from `base_metadata`.
        """
        chunk_boxes = []
        for i, chunk_str in enumerate(chunks, start=1):
            chunk_box = Box(
                {
                    "content": chunk_str,
                    "metadata": {
                        "chunk_num": i,
                    },
                }
            )
            chunk_box.metadata.update(base_metadata)
            chunk_boxes.append(chunk_box)
        return chunk_boxes

    @validate_input
    def chunk(
        self,
        path: str | Path,
        *,
        lang: str = "auto",
        mode: Literal["sentence", "token", "hybrid"] = "sentence",
        max_tokens: conint(ge=30) = 256,
        max_sentences: conint(ge=1) = 12,
        overlap_percent: conint(ge=0, le=75) = 20,
        offset: conint(ge=0) = 0,
        token_counter: Callable[[str], int] | None = None,
    ) -> list[Box]:
        """
        Chunks a single document from a given path.

        This method automatically detects the file type and uses the appropriate
        processor to extract text before chunking. It then adds document-level
        metadata to each resulting chunk.

        Args:
            path (str | Path): The path to the document file.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto'). Defaults to "auto".
            mode (Literal["sentence", "token", "hybrid"]): Chunking mode. Defaults to "sentence".
            max_tokens (int): Maximum number of tokens per chunk.
            max_sentences (int): Maximum number of sentences per chunk.
            overlap_percent (int | float): Percentage of overlap between chunks (0-85).
            offset (int): Starting sentence offset for chunking. Defaults to 0.
            token_counter (callable | None): Optional token counting function. Required for token-based modes only.

        Returns:
            list[Box]: A list of `Box` objects, each representing
            a chunk with its content and metadata.

        Raises:
            InvalidInputError: If the input arguments aren't valid.
            FileNotFoundError: If provided file path not found.
            UnsupportedFileTypeError: If the file extension is not supported for the given mode.
            FileProcessingError: If an error occurs during file reading or processing.
            MissingTokenCounter: If `mode` is "token" or "hybrid" but no `token_counter` is provided.
            CallbackExecutionError: If a callback function (e.g., custom processors callbacks) fails during execution.
        """    
        # Capture all parameters
        params = {k: v for k, v in locals().items() if k not in ["self", "path"]}

        ext = self._validate_path_extension(path)
        validated_path = Path(str(path))

        if self.verbose:
            logger.info("Starting chunk processing for path: {}.", validated_path)

        document_metadata = {"source": str(validated_path)}

        # Prioritize custom processors from registry
        if is_registered(ext):
            text_content, processor_name = use_registered_processor(
                str(validated_path), ext
            )
            if self.verbose:
                logger.info("Used registered processor: {}", processor_name)
        elif ext in self.SUPPORTED_EXTENSIONS - {".pdf"}:
            text_content = self._extract_text(validated_path, ext)
        elif ext == ".pdf":
            raise UnsupportedFileTypeError(
                "File type '.pdf' is not supported by the general chunk method. "
                "\n Reason: pdfs are made of pages and each page text needs to be processed in parallel."
                "\n💡 Hint: use `chunker.chunk_pdfs(['example.pdf', ...])` instead."
            )
        else:
            raise UnsupportedFileTypeError(
                f"File type '{ext}' is not supported.\n"
                f"Supported extensions are: {self.SUPPORTED_EXTENSIONS}\n"
                "💡 Hint: You can add support for other file types by providing a custom processor."
            )
        # Process as a single block of text
        chunks = self.plain_text_chunker.chunk(text=text_content, **params)
        chunk_boxes = list(self._create_chunk_boxes(chunks, document_metadata))

        if self.verbose:
            logger.info(
                "Generated chunks for {}.", validated_path
            )

        return chunk_boxes

    @validate_input
    def chunk_pdfs(
        self,
        paths: Iterable[str | Path],
        *,
        lang: str = "auto",
        mode: Literal["sentence", "token", "hybrid"] = "sentence",
        max_tokens: conint(ge=30) = 256,
        max_sentences: conint(ge=1) = 12,
        overlap_percent: conint(ge=0, le=75) = 20,
        offset: conint(ge=0) = 0,
        token_counter: Callable[[str], int] | None = None,
        n_jobs: int | None = None,
        show_progress: bool = True,
        on_errors: Literal["raise", "skip", "break"] = "raise",
    ) -> Generator[Box, None, None]:
        """
        Chunks multiple PDF documents from a list of file paths.

        This method is designed for optimal performance by processing PDF pages
        in a memory-efficient streaming fashion, leveraging generators.

        Args:
            paths (list[str | Path]): A list of paths to the PDF files.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto'). Defaults to "auto".
            mode (Literal["sentence", "token", "hybrid"]): Chunking mode. Defaults to "sentence".
            max_tokens (int): Maximum number of tokens per chunk.
            max_sentences (int): Maximum number of sentences per chunk.
            overlap_percent (int | float): Percentage of overlap between chunks (0-85).
            offset (int): Starting sentence offset for chunking. Defaults to 0.
            token_counter (callable | None): Optional token counting function. Required for token-based modes only.
            n_jobs (int | None): Number of parallel workers to use. If None, uses all available CPUs.
                   Must be >= 1 if specified.
            show_progress (bool): Flag to show or disable the loading bar.
            on_errors (Literal["raise", "skip", "break"]):
                How to handle errors during processing. Defaults to 'raise'.

        yields:
            Box: `Box` object, representing a chunk with its content and metadata.

        Raises:
            InvalidInputError: If the input arguments aren't valid.
            FileNotFoundError: If provided file path not found.
            UnsupportedFileTypeError: If any file in the list is not a PDF.
            FileProcessingError: If an error occurs during file reading or processing.
            MissingTokenCounter: If `mode` is "token" or "hybrid" but no `token_counter` is provided.
        """
        if self.verbose:
            logger.info("Starting batch PDF chunking for {} documents.", len(paths))

        # Capture all parameters for the plain text chunker
        chunk_params = {k: v for k, v in locals().items() if k not in ["self", "paths"]}

        pdf_metadatas = []
        page_counts = []

        # Validate all paths upfront
        validated_paths_with_ext = []
        for i, path in enumerate(paths):
            try:
                ext = self._validate_path_extension(path)
                if ext != ".pdf":
                    raise UnsupportedFileTypeError(
                        f"File type '{ext}' is not supported by chunk_pdfs. "
                        "All files in the list must be .pdf files."
                    )
                validated_paths_with_ext.append((str(path), ext))
            except Exception as e:
                if self.verbose:
                    logger.warning(
                        "Skipping file {} at index {}. Reason: {}", path, i, e
                    )
                continue

        if not validated_paths_with_ext:
            logger.warning(
                "No valid PDF files found after validation. Returning empty generator."
            )
            return iter([])

        # Generator needed to process the pdfs pages one by one
        def _extract_pdf_pages():
            for validated_path, ext in validated_paths_with_ext:
                pdf_data = self.pdf_processor.extract_data(validated_path)
                document_metadata = pdf_data.get("metadata", {})
                pages_generator = pdf_data["pages"]

                page_counts.append(document_metadata.get("page_count", 0))
                pdf_metadatas.append(document_metadata)

                yield from pages_generator

        all_pages_chunks_gen = self.plain_text_chunker.batch_chunk(
            texts=_extract_pdf_pages(),
            _document_context=True,
            **chunk_params,
        )

        # To track pdf file and insert the correct metadata
        pdf_index = 0
        pages_so_far = 0
        for page_num, chunks_list in enumerate(all_pages_chunks_gen, start=1):
            # Move to the next pdf if we have processed all pages from the current one
            if (
                pdf_index < len(page_counts)
                and pages_so_far + page_counts[pdf_index] < page_num
            ):
                pages_so_far += page_counts[pdf_index]
                pdf_index += 1

            pdf_metadata = pdf_metadatas[pdf_index]
            page_num_in_doc = page_num - pages_so_far

            page_metadata = pdf_metadata.copy()
            page_metadata["page_num"] = page_num_in_doc
            yield from self._create_chunk_boxes(chunks_list, page_metadata)

        if self.verbose and pdf_metadatas:
            logger.info(
                "Finished generating chunks for {} PDF document(s).", len(pdf_metadatas)
            )

    @validate_input
    def batch_chunk(
        self,
        paths: Iterable[str | Path],
        *,
        lang: str = "auto",
        mode: Literal["sentence", "token", "hybrid"] = "sentence",
        max_tokens: conint(ge=30) = 256,
        max_sentences: conint(ge=1) = 12,
        overlap_percent: conint(ge=0, le=75) = 20,
        offset: conint(ge=0) = 0,
        token_counter: Callable[[str], int] | None = None,
        n_jobs: int | None = None,
        show_progress: bool = True,
        on_errors: Literal["raise", "skip", "break"] = "raise",
    ) -> Generator[Box, None, None]:
        """
        Chunks multiple documents from a list of file paths.

        This method is a memory-efficient generator that yields chunks as they
        are processed, without loading all documents into memory at once. It
        handles various file types, but not PDFs.

        Args:
            paths (Iterable[str | Path]): An iterable of paths to the document files.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto'). Defaults to "auto".
            mode (Literal["sentence", "token", "hybrid"]): Chunking mode. Defaults to "sentence".
            max_tokens (int): Maximum number of tokens per chunk.
            max_sentences (int): Maximum number of sentences per chunk.
            overlap_percent (int | float): Percentage of overlap between chunks (0-85).
            offset (int): Starting sentence offset for chunking. Defaults to 0.
            token_counter (callable | None): Optional token counting function. Required for token-based modes only.
            n_jobs (int | None): Number of parallel workers to use. If None, uses all available CPUs.
                   Must be >= 1 if specified.
            show_progress (bool): Flag to show or disable the loading bar.
            on_errors (Literal["raise", "skip", "break"]):
                How to handle errors during processing. Can be 'raise', 'ignore', or 'break'.

        yields:
            Box: `Box` object, representing a chunk with its content and metadata.

        Raises:
            InvalidInputError: If the input arguments aren't valid.
            FileNotFoundError: If provided file path not found.
            UnsupportedFileTypeError: If the file extension is not supported for the given mode,
                                     or if the file is a PDF.
            FileProcessingError: If an error occurs during file reading or processing.
            MissingTokenCounter: If `mode` is "token" or "hybrid" but no `token_counter` is provided.
            CallbackExecutionError: If a callback function (e.g., custom processors callbacks) fails during execution.
        """
        if self.verbose:
            logger.info("Starting batch chunking for {} documents.", len(paths))

        # Capture all parameters for the plain text chunker
        chunk_params = {k: v for k, v in locals().items() if k not in ["self", "paths"]}

        doc_metadatas = []

        # Validate all paths upfront
        validated_paths_with_ext = []
        for i, path in enumerate(paths):
            try:
                ext = self._validate_path_extension(path)
                validated_paths_with_ext.append((str(path), ext))
            except Exception as e:
                if self.verbose:
                    logger.warning(
                        "Skipping file {} at index {}. Reason: {}", path, i, e
                    )
                continue

        if not validated_paths_with_ext:
            logger.warning(
                "No valid files found after validation. Returning empty generator."
            )
            return iter([])

        def _extract_texts() -> Generator[str, None, None]:
            for validated_path, ext in validated_paths_with_ext:

                if ext == ".pdf":
                    if self.verbose:
                        logger.warning(
                            "Skipping file {}. Reason: batch_chunk does not support .pdf files. Use chunk_pdfs instead.",
                            validated_path,
                        )
                    continue

                if self.verbose:
                    logger.debug(
                        "Processing file: {}, detected extension: {}",
                        validated_path,
                        ext,
                    )

                base_metadata = {"source": validated_path}
                doc_metadatas.append(base_metadata)

                # Prioritize custom processors from registry
                if is_registered(ext):
                    text_content, processor_name = use_registered_processor(
                        validated_path, ext
                    )
                    if self.verbose:
                        logger.debug("Used registered processor: {}", processor_name)
                    yield text_content
                else:
                    yield self._extract_text(validated_path, ext)

        all_docs_chunks_gen = self.plain_text_chunker.batch_chunk(
            texts=_extract_texts(),
            _document_context=True,
            **chunk_params,
        )

        for i, chunks_list in enumerate(all_docs_chunks_gen):
            metadata = doc_metadatas[i]
            yield from self._create_chunk_boxes(chunks_list, metadata)
        if self.verbose and metadata:
            logger.info(
                "Finished generating chunks for {} document(s).", len(metadata)
            )