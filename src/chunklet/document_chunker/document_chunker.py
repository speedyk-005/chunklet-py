from pathlib import Path
from typing import Callable, Literal, Any, Generator, Annotated, Iterable
from pydantic import Field
from box import Box
from loguru import logger
from itertools import chain, tee
from more_itertools import ilen, split_at

try:
    from striprtf.striprtf import rtf_to_text
except ImportError:
    rtf_to_text = None

try:
    from charset_normalizer import from_path
except ImportError:
    from_path = None

from chunklet.base_chunker import BaseChunker
from chunklet.sentence_splitter import BaseSplitter
from chunklet.plain_text_chunker import PlainTextChunker
from chunklet.document_chunker.processors import (
    pdf_processor,
    epub_processor,
    docx_processor,
    odt_processor,
)
from chunklet.document_chunker.converters import (
    html_2_md,
    rst_2_md,
    latex_2_md,
    table_2_md,
)
from chunklet.document_chunker.registry import CustomProcessorRegistry
from chunklet.common.validation import validate_input, restricted_iterable
from chunklet.exceptions import InvalidInputError, UnsupportedFileTypeError


class DocumentChunker(BaseChunker):
    """
    A comprehensive document chunker that handles various file formats.

    This class provides a high-level interface to chunk text from different
    document types. It automatically detects the file format and uses the
    appropriate method to extract content before passing it to an underlying
    `PlainTextChunker` instance.

    Key Features:
    - Multi-Format Support: Chunks text from PDF, TXT, MD, and RST files.
    - Metadata Enrichment: Automatically adds source file path and other
      document-level metadata (e.g., PDF page numbers) to each chunk.
    - Bulk Processing: Efficiently chunks multiple documents in a single call.
    - Pluggable Document processors: Integrate custom processors allowing definition
    of specific logic for extracting text from various file types.
    """

    BUILTIN_SUPPORTED_EXTENSIONS = {
        ".csv",
        ".docx",
        ".epub",
        ".hml",
        ".html",
        ".md",
        ".odt",
        ".pdf",
        ".rst",
        ".rtf",
        ".tex",
        ".txt",
        ".xlsx",
    }

    def __init__(
        self,
        sentence_splitter: Any | None = None,
        verbose: bool = False,
        continuation_marker: str = "...",
        token_counter: Callable[[str], int] | None = None,
    ):
        """
        Initializes the DocumentChunker.

        Args:
            sentence_splitter (BaseSplitter | None): An optional BaseSplitter instance.
                If None, a default SentenceSplitter will be initialized.
            verbose (bool): Enable verbose logging.
            continuation_marker (str): The marker to prepend to unfitted clauses. Defaults to '...'.
            token_counter (Callable[[str], int] | None): Function that counts tokens in text.
                If None, must be provided when calling chunk() methods.

        Raises:
            InvalidInputError: If any of the input arguments are invalid or if the provided `sentence_splitter` is not an instance of `BaseSplitter`.
        """
        self._verbose = verbose
        self.token_counter = token_counter
        self.continuation_marker = continuation_marker

        # Explicit type validation for sentence_splitter
        if sentence_splitter is not None and not isinstance(
            sentence_splitter, BaseSplitter
        ):
            raise InvalidInputError(
                f"The provided sentence_splitter must be an instance of BaseSplitter, "
                f"but got {type(sentence_splitter).__name__}."
            )

        self.plain_text_chunker = PlainTextChunker(
            sentence_splitter=sentence_splitter,
            verbose=self._verbose,
            continuation_marker=self.continuation_marker,
            token_counter=self.token_counter,
        )

        self.processors = {
            ".pdf": pdf_processor.PDFProcessor,
            ".epub": epub_processor.EPUBProcessor,
            ".docx": docx_processor.DOCXProcessor,
            ".odt": odt_processor.ODTProcessor,
        }
        self.converters = {
            ".html": html_2_md.html_to_md,
            ".hml": html_2_md.html_to_md,
            ".rst": rst_2_md.rst_to_md,
            ".tex": latex_2_md.latex_to_md,
            ".csv": table_2_md.table_to_md,
            ".xlsx": table_2_md.table_to_md,
        }
        self.processor_registry = CustomProcessorRegistry()

    @property
    def supported_extensions(self):
        """Get the supported extensions, including the custom ones."""
        return (
            self.BUILTIN_SUPPORTED_EXTENSIONS
            | self.processor_registry.processors.keys()
        )

    @property
    def verbose(self) -> bool:
        """Get the verbosity status."""
        return self._verbose

    @verbose.setter
    def verbose(self, value: bool):
        """Set the verbosity and propagate to plain_text_chunker."""
        self._verbose = value
        self.plain_text_chunker.verbose = value

    def _validate_and_get_extension(self, path: Path) -> str:
        """
        Validates the file path and returns its lowercased extension.

        This method ensures the path exists and the file type is supported.

        Args:
            path (Path): The Path object of the document file.

        Returns:
            str: The lowercased file extension.

        Raises:
            FileNotFoundError: If provided file path not found.
            UnsupportedFileTypeError: If the file extension is not supported or is missing.
        """
        extension = path.suffix.lower()

        if not extension:
            raise UnsupportedFileTypeError(
                f"Invalid path '{path}' provided. Path must have a recognizable extension."
            )

        if not path.is_file():
            raise FileNotFoundError(
                f"The file '{path}' can't be found.\n"
                "💡 Hint: Check the path for typos, ensure the file exists, and verify it's not a directory."
            )

        if extension not in self.supported_extensions:
            raise UnsupportedFileTypeError(
                f"File type '{extension}' is not supported.\nSupported extensions are: "
                f"{self.supported_extensions}\n"
                "💡 Hint: You can add support for other file types by registring a custom processor."
            )

        return extension

    def _read(self, path: str | Path, ext: str) -> str:
        """
        Read text content from a file using charset detection, handling special formats like RTF.

        Args:
            path (str | Path): Path to the file
            ext (str): File extension

        Returns:
            str: The text content of the file
        """
        if from_path is None:
            raise ImportError(
                "The 'charset-normalizer' library is not installed. "
                "Please install it with 'pip install charset-normalizer>=3.4.0' "
                "or install the document processing extras with 'pip install chunklet-py[document]'"
            )

        match = from_path(str(path)).best()
        raw_content = str(match) if match else ""

        if ext == ".rtf":
            if rtf_to_text is None:
                raise ImportError(
                    "The 'striprtf' library is not installed. Please install it with 'pip install 'striprtf>=0.0.29'' or install the document processing extras with 'pip install chunklet-py[document]'"
                )
            return rtf_to_text(raw_content)
        else:  # For .txt, .md, and others handled by simple read
            return raw_content

    def _extract_data(
        self, path: str | Path, ext: str
    ) -> tuple[str | Generator[str, None, None], dict[str, Any]]:
        """
        Extracts data and metadata from a document.

        Args:
            path (str | Path): The path to the document file.
            ext (str): The file extension.

        Returns:
            tuple[str | Generator[str, None, None], dict[str, Any]]: A tuple containing
            either a string (for simple text files) or a generator of strings (for processed documents)
            and a dictionary of metadata.
        """
        self.log_info("Extracting text from file {}", path)

        # Prioritize custom processors from registry
        if self.processor_registry.is_registered(ext):
            texts_and_metadata, processor_name = self.processor_registry.extract_data(
                str(path), ext
            )
            self.log_info("Used registered processor: {}", processor_name)
            text_or_gen, metadata = texts_and_metadata
            metadata["source"] = metadata.get("source", str(path))
            return text_or_gen, metadata

        elif ext in self.processors:
            processor_class = self.processors[ext]
            processor = processor_class(path)
            return processor.extract_text(), processor.extract_metadata()

        elif ext in self.converters:
            text_content = self.converters[ext](path)

        else:
            text_content = self._read(path, ext)

        return text_content, {"source": str(path)}

    def _gather_all_data(self, paths: Iterable[str | Path], on_errors: str) -> dict:
        """
        Gathers and prepares data from paths for batch processing.

        This method iterates through a list of file paths,
        validates each path, handles any validation or processing errors,
        and extracts the content and metadata from each valid file. It uses a memory-efficient approach
        by creating a master generator for all text content rather than loading
        it all into memory.

        Args:
            paths (Iterable[str | Path]): An iterable of file paths to process.
            on_errors (Literal["raise", "skip", "break"]): Defines the error
                handling strategy for validation or processing failures.

        Returns:
            dict: A dictionary containing the prepared data, with the
                following keys:
                - "path_section_counts" (dict): A mapping of file paths to the
                  number of sections (e.g., pages) within them.
                - "all_texts_gen" (Generator): A single generator that yields
                  the text content of all documents sequentially.
                - "all_metadata" (list): A list of metadata dictionaries, one
                  for each successfully processed document.
        """
        path_section_counts = {}
        all_metadata = []
        text_gens_to_chain = []

        for i, path in enumerate(paths):
            try:
                path = Path(path)
                ext = self._validate_and_get_extension(path)

                text_content_or_generator, document_metadata = self._extract_data(
                    path, ext
                )
                all_metadata.append(document_metadata)

                if isinstance(text_content_or_generator, Generator):
                    g1, g2 = tee(text_content_or_generator)
                    path_section_counts[str(path)] = ilen(g1)
                    text_gens_to_chain.append(g2)
                else:
                    path_section_counts[str(path)] = 1

                    # Wrap in a list to prevent breakking the str into chars
                    text_gens_to_chain.append([text_content_or_generator])
            except Exception as e:
                if on_errors == "raise":
                    logger.error(
                        "Document processing failed for '{}'.\nReason: {}.",
                        path,
                        e,
                    )
                    raise
                elif on_errors == "break":
                    logger.error(
                        "Stopping due to validation error on '{}' at paths[{}].\nReason: {}.",
                        path,
                        i,
                        e,
                    )
                    break
                else:  # skip
                    logger.warning(
                        "Skipping document '{}' at paths[{}] due to validation failure.\nReason: {}.",
                        path,
                        i,
                        e,
                    )
                    continue

        all_texts_gen = chain.from_iterable(text_gens_to_chain)

        return {
            "path_section_counts": path_section_counts,
            "all_texts_gen": all_texts_gen,
            "all_metadata": all_metadata,
        }

    @validate_input
    def chunk(
        self,
        path: str | Path,
        *,
        lang: str = "auto",
        max_tokens: Annotated[int | None, Field(ge=12)] = None,
        max_sentences: Annotated[int | None, Field(ge=1)] = None,
        max_section_breaks: Annotated[int | None, Field(ge=1)] = None,
        overlap_percent: Annotated[int, Field(ge=0, le=75)] = 20,
        offset: Annotated[int, Field(ge=0)] = 0,
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
            max_tokens (int, optional): Maximum number of tokens per chunk. Must be >= 12.
            max_sentences (int, optional): Maximum number of sentences per chunk. Must be >= 1.
            max_section_breaks (int, optional): Maximum number of section breaks per chunk. Must be >= 1.
            overlap_percent (int | float): Percentage of overlap between chunks (0-85).
            offset (int): Starting sentence offset for chunking. Defaults to 0.
            token_counter (callable | None): Optional token counting function.
                Required if `max_tokens` is provided.

        Returns:
            list[Box]: A list of `Box` objects, each representing
            a chunk with its content and metadata.

        Raises:
            InvalidInputError: If the input arguments aren't valid.
            FileNotFoundError: If provided file path not found.
            UnsupportedFileTypeError: If the file extension is not supported or is missing.
            MissingTokenCounterError: If `max_tokens` is provided but no `token_counter` is provided.
            CallbackError: If a callback function (e.g., custom processors callbacks) fails during execution.
        """
        path = Path(path)
        ext = self._validate_and_get_extension(path)

        text_content_or_generator, document_metadata = self._extract_data(path, ext)

        if not isinstance(text_content_or_generator, str):
            raise UnsupportedFileTypeError(
                f"File type '{ext}' is not supported by the general chunk method.\n"
                "Reason: The processor for this file returns iterable, "
                "so it must be processed in parallel for efficiency.\n"
                "💡 Hint: use `chunker.batch_chunk([file.ext])` for this file type."
            )

        self.log_info("Starting chunk processing for path: {}.", path)

        text_content = text_content_or_generator

        # Process as a single block of text
        chunk_boxes = self.plain_text_chunker.chunk(
            text=text_content,
            lang=lang,
            max_tokens=max_tokens,
            max_sentences=max_sentences,
            max_section_breaks=max_section_breaks,
            overlap_percent=overlap_percent,
            offset=offset,
            token_counter=token_counter or self.token_counter,
            base_metadata=document_metadata,
        )

        self.log_info("Generated {} chunks for {}.", len(chunk_boxes), path)

        return chunk_boxes

    @validate_input
    def batch_chunk(
        self,
        paths: restricted_iterable(str | Path),
        *,
        lang: str = "auto",
        max_tokens: Annotated[int | None, Field(ge=12)] = None,
        max_sentences: Annotated[int | None, Field(ge=1)] = None,
        max_section_breaks: Annotated[int | None, Field(ge=1)] = None,
        overlap_percent: Annotated[int, Field(ge=0, le=75)] = 20,
        offset: Annotated[int, Field(ge=0)] = 0,
        token_counter: Callable[[str], int] | None = None,
        separator: Any = None,
        n_jobs: Annotated[int, Field(ge=1)] | None = None,
        show_progress: bool = True,
        on_errors: Literal["raise", "skip", "break"] = "raise",
    ) -> Generator[Box, None, None]:
        """
        Chunks multiple documents from a list of file paths.

        This method is a memory-efficient generator that yields chunks as they
        are processed, without loading all documents into memory at once. It
        handles various file types.

        Args:
            paths (restricted_iterable[str | Path]): A restricted iterable of paths to the document files.
            lang (str): The language of the text (e.g., 'en', 'fr', 'auto'). Defaults to "auto".
            max_tokens (int, optional): Maximum number of tokens per chunk. Must be >= 12.
            max_sentences (int, optional): Maximum number of sentences per chunk. Must be >= 1.
            max_section_breaks (int, optional): Maximum number of section breaks per chunk. Must be >= 1.
            overlap_percent (int | float): Percentage of overlap between chunks (0-85).
            offset (int): Starting sentence offset for chunking. Defaults to 0.
            token_counter (callable | None): Optional token counting function.
                Required if `max_tokens` is provided.
            separator (Any): A value to be yielded after the chunks of each text are processed.
                Note: None cannot be used as a separator.

            n_jobs (int | None): Number of parallel workers to use. If None, uses all available CPUs.
                   Must be >= 1 if specified.
            show_progress (bool): Flag to show or disable the loading bar.
            on_errors: How to handle errors during processing. Can be 'raise', 'ignore', or 'break'.

        yields:
            Box: `Box` object, representing a chunk with its content and metadata.

        Raises:
            InvalidInputError: If the input arguments aren't valid.
            FileNotFoundError: If provided file path not found.
            UnsupportedFileTypeError: If the file extension is not supported or is missing.
            MissingTokenCounterError: If `max_tokens` is provided but no `token_counter` is provided.
            CallbackError: If a callback function (e.g., custom processors callbacks) fails during execution.
        """
        sentinel = object()

        gathered_data = self._gather_all_data(paths, on_errors)

        all_chunks_gen = self.plain_text_chunker.batch_chunk(
            texts=gathered_data["all_texts_gen"],
            lang=lang,
            max_tokens=max_tokens,
            max_sentences=max_sentences,
            max_section_breaks=max_section_breaks,
            overlap_percent=overlap_percent,
            offset=offset,
            token_counter=token_counter or self.token_counter,
            separator=sentinel,
            n_jobs=n_jobs,
            show_progress=show_progress,
            on_errors=on_errors,
        )

        all_chunk_groups = split_at(all_chunks_gen, lambda x: x is sentinel)
        path_section_counts = gathered_data["path_section_counts"]
        all_metadata = gathered_data["all_metadata"]

        # HACK: Since a sentinel is always at the end of the gen,
        # the last list of the groups will be an empty one.
        # The only work-around to add a sentinel at paths
        paths = list(path_section_counts.keys()) + [None]

        # If no files were successfully processed, return empty
        if not path_section_counts:
            return

        doc_count = 0
        curr_path = paths[0]
        for chunks in all_chunk_groups:
            if path_section_counts.get(curr_path, 0) == 0:
                if separator is not None:
                    yield separator

                doc_count += 1
                curr_path = paths[doc_count]
                if curr_path is None:
                    return

            for i, ch in enumerate(chunks, start=1):
                doc_metadata = all_metadata[doc_count]
                doc_metadata["section_count"] = path_section_counts[curr_path]
                doc_metadata["curr_section"] = i

                ch["metadata"].update(doc_metadata)
                yield ch

            path_section_counts[curr_path] -= 1
