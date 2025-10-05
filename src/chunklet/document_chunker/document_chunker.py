from __future__ import annotations
from pathlib import Path
from typing import Callable, Any, Generator, Iterable
from collections.abc import Iterable
from box import Box
from pydantic import ValidationError

try:
    from striprtf.striprtf import rtf_to_text
except ImportError:
    rtf_to_text = None
    
from chunklet import PlainTextChunker
from chunklet.sentence_splitter import SentenceSplitter
from .pdf_processor import PDFProcessor
from .docx_processor import DOCXProcessor
from chunklet.utils.rst_to_md import rst_to_markdown
from chunklet.utils.error_utils import pretty_errors
from chunklet.models import DocumentChunkerInitConfig, CustomProcessorConfig
from chunklet.exceptions import (
    InvalidInputError,
    UnsupportedFileTypeError,
    FileProcessingError,
    CallbackExecutionError,
)
from chunklet.utils.logger import logger

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
    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.md', '.rst', '.rtf'}
    
    def __init__(
        self,
        verbose: bool = True,
        use_cache: bool = True,
        continuation_marker: str = "...",
        sentence_splitter: SentenceSplitter | None = None,
        custom_processors: list[dict] | None = None,
    ):
        """
        Initializes the DocumentChunker.

        Args:
            verbose (bool): If True, enables verbose logging. Defaults to True.
            use_cache (bool): If True, enables caching for chunking operations. Defaults to True.
            continuation_marker (str): The marker to prepend to unfitted clauses. Defaults to '...'.
            sentence_splitter (SentenceSplitter | None): An optional SentenceSplitter instance.
                If None, a default SentenceSplitter will be initialized.
            custom_processors (list[dict] | None): List of custom document processors.
        """
        # Validate parameters
        try:
            config = DocumentChunkerInitConfig(
                verbose=verbose,
                use_cache=use_cache,
                continuation_marker=continuation_marker,
                custom_processors=custom_processors,
            )
        except ValidationError as e:
            pretty_err = pretty_errors(e)
            raise InvalidInputError(
                f"Invalid configuration.\n Details: {pretty_err}"
            ) from e

        self.verbose = verbose
        self.use_cache = use_cache
        self.continuation_marker = continuation_marker
        self._custom_processors = config.custom_processors
        
        if self.verbose:
            logger.debug(
                "Initialized with verbose=%s, use_cache=%s, continuation_marker='%s'",
                self.verbose,
                self.use_cache,
                self.continuation_marker,
            )

        # Use provided SentenceSplitter or create a default one
        self.sentence_splitter = (
            sentence_splitter
            if sentence_splitter
            else SentenceSplitter(verbose=self.verbose)
        )

        # Create PlainTextChunker internally, using the (provided or default) SentenceSplitter
        self.plain_text_chunker = PlainTextChunker(
            verbose=self.verbose,
            use_cache=self.use_cache,
            continuation_marker=self.continuation_marker,
            sentence_splitter=self.sentence_splitter,
        )

        # Prepare a set of supported extensions for custom processors
        self._custom_processor_extensions = set()
        if self._custom_processors:
            for processor in self._custom_processors:
                if isinstance(processor.file_extensions, str):
                    self._custom_processor_extensions.add(
                        processor.file_extensions
                    )
                else:
                    self._custom_processor_extensions.update(
                        set(processor.file_extensions)
                    )       

        self.pdf_processor = PDFProcessor()
        self.docx_processor = DOCXProcessor()

    @property
    def custom_processors(self) -> list[CustomProcessorConfig] | None:
        """
        Returns the list of custom processor configurations.
        """
        return self._custom_processors

    def validate_path_extension(self, path: str | Path) -> str:
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

        if (
            extension not in self.SUPPORTED_EXTENSIONS
            and extension not in self._custom_processor_extensions
        ):
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
        if self.plain_text_chunker.verbose:
            logger.debug(
                "Extracting text from file: %s with extension: %s", path, ext
            )

        text_content = ""
        try:
            if ext == ".docx":
                text_content = self.docx_processor.extract_text(path)
            else:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    raw_content = f.read()
                    if ext == ".rst":
                        text_content = rst_to_markdown(raw_content)
                    elif ext == ".rtf":
                        if rtf_to_text is None:
                            raise ImportError(
                                "The 'striprtf' library is not installed. Please install it with 'pip install striprtf' or install the document processing extras with 'pip install chunklet-py[document]'"
                            )
                        text_content = rtf_to_text(raw_content)
                    else:  # For .txt, .md, and others handled by simple read
                        text_content = raw_content

        except Exception as e:
            raise FileProcessingError(f"Error extracting text from file {path}.\n Details: {e}") from e

        return text_content

    def _use_custom_processor(self, path: str | Path, ext: str) -> str:
        """
        Processes a file using a custom processor registered for the given extension.

        Args:
            path (str | Path): The path to the file.
            ext (str): The file extension (e.g., ".json").

        Returns:
            str: The extracted text content.

        Raises:
             FileProcessingError: If a custom processor fails during execution.
        """
        for processor in self._custom_processors:
            supported_extensions = (
                [processor.file_extensions]
                if isinstance(processor.file_extensions, str)
                else processor.file_extensions
            )
            if ext in supported_extensions:
                if self.plain_text_chunker.verbose:
                    logger.debug(
                        "Using custom processor '%s' for file type: %s",
                        processor.name,
                        ext,
                    )
                # Handle validation and error wrapping.
                file_path = str(path)
                try:
                    result = processor.callback(file_path)
                except Exception as e:
                    raise CallbackExecutionError(
                       f"Custom processor '{processor.name}' callback failed for file: '{file_path}'. "
                        f"Details: {e}"
                    ) from e

                if not isinstance(result, str):
                    raise CallbackExecutionError(
                        f"Custom processor '{processor.name}' callback returned an invalid type. "
                        f"Expected a string, but got {type(result)}."
                    )
                return result
        

    def _create_chunk_boxes(
        self,
        chunks: Iterable[str],
        base_metadata: dict[str, Any],
    ) -> list[Box]:
        """
        Helper to create a list of Box objects for chunks with embedded metadata and auto-assigned chunk numbers.
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
                
    def chunk(
        self,
        path: str | Path,
        *,
        lang: str = "auto",
        mode: str = "sentence",
        max_tokens: int = 256,
        max_sentences: int = 12,
        overlap_percent: int | float = 20,
        offset: int = 0,
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
            mode (str): Chunking mode ('sentence', 'token', or 'hybrid'). Defaults to "sentence".
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
        """
        # Capture all parameters
        params = {
            k: v for k, v in locals().items()
            if k not in ["self", "path"]
        }

        ext = self.validate_path_extension(path)
        validated_path = Path(str(path))

        if self.plain_text_chunker.verbose:
            logger.debug(
                "Validated path: %s, detected extension: %s",
                validated_path,
                ext,
            )

        text_content = ""  # This will hold the text for chunking
        document_metadata = {"source": str(validated_path)}

        # Prioritize custom processors
        if ext in self._custom_processor_extensions:
            text_content = self._use_custom_processor(validated_path, ext)
        elif ext in self.SUPPORTED_EXTENSIONS - {'.pdf'}:
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

        if self.plain_text_chunker.verbose:
            logger.info(
                "Generated chunks for %s (from %s)",
                validated_path,
                "text-based file" if ext in self.SUPPORTED_EXTENSIONS - {'.pdf'} else "custom processor"
            )

        return chunk_boxes

    def chunk_pdfs(
        self,
        paths: Iterable[str | Path],
        *,
        lang: str = "auto",
        mode: str = "sentence",
        max_tokens: int = 256,
        max_sentences: int = 12,
        overlap_percent: int | float = 20,
        offset: int = 0,
        token_counter: Callable[[str], int] | None = None,
        n_jobs: int | None = None,
        show_progress: bool = True,
        on_errors: str = "raise",
    ) -> Generator[Box, None, None]:
        """
        Chunks multiple PDF documents from a list of file paths.

        This method is designed for optimal performance by processing PDF pages
        in a memory-efficient streaming fashion, leveraging generators.

        Args:
            paths (list[str | Path]): A list of paths to the PDF files.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto'). Defaults to "auto".
            mode (str): Chunking mode ('sentence', 'token', or 'hybrid'). Defaults to "sentence".
            max_tokens (int): Maximum number of tokens per chunk.
            max_sentences (int): Maximum number of sentences per chunk.
            overlap_percent (int | float): Percentage of overlap between chunks (0-85).
            offset (int): Starting sentence offset for chunking. Defaults to 0.
            token_counter (callable | None): Optional token counting function. Required for token-based modes only.
            n_jobs (int | None): Number of parallel workers to use. If None, uses all available CPUs.
                   Must be >= 1 if specified.
            show_progress (bool): Flag to show or disable the loading bar.
            on_errors (str): How to handle errors during processing. Can be 'raise', 'ignore', or 'break'.

        yields:
            Box: `Box` object, representing a chunk with its content and metadata.

        Raises:
            InvalidInputError: If the input arguments aren't valid.
            FileNotFoundError: If provided file path not found.
            UnsupportedFileTypeError: If any file in the list is not a PDF.
            FileProcessingError: If an error occurs during file reading or processing.
            MissingTokenCounter: If `mode` is "token" or "hybrid" but no `token_counter` is provided.
        """
        # Validate that paths is an iterable
        if not isinstance(paths, Iterable):
            raise InvalidInputError("The 'paths' parameter must be an iterable (e.g., a list or tuple) of file paths.")

        if self.plain_text_chunker.verbose:
            logger.info("Starting batch PDF chunking for %s documents.", len(paths))

        # Capture all parameters for the plain text chunker
        chunk_params = {
            k: v for k, v in locals().items()
            if k not in ["self", "paths"]
        }

        pdf_metadatas = []
        page_counts = []

        # Validate all paths upfront
        validated_paths_with_ext = []
        for i, path in enumerate(paths):
            try:
                ext = self.validate_path_extension(path)
                if ext != ".pdf":
                    raise UnsupportedFileTypeError(
                        f"File type '{ext}' is not supported by chunk_pdfs. "
                        "All files in the list must be .pdf files."
                    )
                validated_paths_with_ext.append((str(path), ext))
            except (FileNotFoundError, UnsupportedFileTypeError, InvalidInputError) as e:
                if self.plain_text_chunker.verbose:
                    logger.warning("Skipping file %s at index %s. Reason: %s", path, i, e)
                continue
        
        if not validated_paths_with_ext:
            logger.warning("No valid PDF files found after validation. Returning empty generator.")

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

        if self.plain_text_chunker.verbose and pdf_metadatas:
            logger.info(
                "Finished generating chunks for %d PDF document(s).",
                len(pdf_metadatas)
            )


    def batch_chunk(
        self,
        paths: Iterable[str | Path],
        *,
        lang: str = "auto",
        mode: str = "sentence",
        max_tokens: int = 256,
        max_sentences: int = 12,
        overlap_percent: int | float = 20,
        offset: int = 0,
        token_counter: Callable[[str], int] | None = None,
        n_jobs: int | None = None,
        show_progress: bool = True,
        on_errors: str = "raise",
    ) -> Generator[Box, None, None]:
        """
        Chunks multiple documents from a list of file paths.

        This method is a memory-efficient generator that yields chunks as they
        are processed, without loading all documents into memory at once. It
        handles various file types, but not PDFs.

        Args:
            paths (Iterable[str | Path]): An iterable of paths to the document files.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto'). Defaults to "auto".
            mode (str): Chunking mode ('sentence', 'token', or 'hybrid'). Defaults to "sentence".
            max_tokens (int): Maximum number of tokens per chunk.
            max_sentences (int): Maximum number of sentences per chunk.
            overlap_percent (int | float): Percentage of overlap between chunks (0-85).
            offset (int): Starting sentence offset for chunking. Defaults to 0.
            token_counter (callable | None): Optional token counting function. Required for token-based modes only.
            n_jobs (int | None): Number of parallel workers to use. If None, uses all available CPUs.
                   Must be >= 1 if specified.
            show_progress (bool): Flag to show or disable the loading bar.
            on_errors (str): How to handle errors during processing. Can be 'raise', 'ignore', or 'break'.

        yields:
            Box: `Box` object, representing a chunk with its content and metadata.

        Raises:
            InvalidInputError: If the input arguments aren't valid.
            FileNotFoundError: If provided file path not found.
            UnsupportedFileTypeError: If the file extension is not supported for the given mode,
                                     or if the file is a PDF.
            FileProcessingError: If an error occurs during file reading or processing.
            MissingTokenCounter: If `mode` is "token" or "hybrid" but no `token_counter` is provided.
        """
        # Validate that paths is an iterable
        if not isinstance(paths, Iterable):
            raise InvalidInputError("The 'paths' parameter must be an iterable (e.g., a list or tuple) of file paths.")

        if self.plain_text_chunker.verbose:
            logger.info("Starting batch chunking for %s documents.", len(paths))

        # Capture all parameters for the plain text chunker
        chunk_params = {
            k: v for k, v in locals().items()
            if k not in ["self", "paths"]
        }
        
        doc_metadatas = []

        # Validate all paths upfront
        validated_paths_with_ext = []
        for i, path in enumerate(paths):
            try:
                ext = self.validate_path_extension(path)
                validated_paths_with_ext.append((str(path), ext))
            except (FileNotFoundError, UnsupportedFileTypeError, InvalidInputError) as e:
                if self.plain_text_chunker.verbose:
                    logger.warning("Skipping file %s at index %s. Reason: %s", path, i, e)
                continue

        if not validated_paths_with_ext:
            logger.warning("No valid files found after validation. Returning empty generator.")
            return

        def _extract_texts() -> Generator[str, None, None]:
            for validated_path, ext in validated_paths_with_ext:

                if ext == ".pdf":
                    if self.plain_text_chunker.verbose:
                        logger.warning("Skipping file %s. Reason: batch_chunk does not support .pdf files. Use chunk_pdfs instead.", validated_path)
                    continue

                if self.plain_text_chunker.verbose:
                    logger.debug(
                        "Processing file: %s, detected extension: %s",
                        validated_path,
                        ext,
                    )
                
                base_metadata = {"source": validated_path}
                doc_metadatas.append(base_metadata)

                if ext in self._custom_processor_extensions:
                    yield self._use_custom_processor(validated_path, ext)
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
            if self.plain_text_chunker.verbose:
                logger.info(
                    "Finished generating chunks for %s",
                    metadata.get("source")
                )
                