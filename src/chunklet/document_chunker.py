import csv
from pathlib import Path
from typing import Union, List, Optional, Callable, Dict, Any, Tuple
from box import Box
from loguru import logger
from chunklet.plain_text_chunker import PlainTextChunker
from chunklet.utils.pdf_processor import PDFProcessor
from chunklet.utils.docx_processor import DOCXProcessor
from chunklet.utils.rst_to_md import rst_to_markdown
from chunklet.exceptions import InvalidInputError

class DocumentChunker:
    """
    A comprehensive document chunker that handles various file formats.

    This class provides a high-level interface to chunk text from different
    document types. It automatically detects the file format and uses the
    appropriate method to extract content before passing it to an underlying
    `PlainTextChunker` instance.

    Key Features:
    - Multi-Format Support: Chunks text from PDF, DOCX, TXT, MD, and RST files.
    - Tabular Data Handling: Provides a separate method (`chunk_table`) for
      intelligently chunking CSV and Excel files.
    - Metadata Enrichment: Automatically adds source file path and other
      document-level metadata (e.g., PDF page numbers) to each chunk.
    - Bulk Processing: Efficiently chunks multiple documents in a single call.
    """
    # Supported file extensions for general-purpose text documents
    GENERAL_TEXT_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".rst"}
    # Supported file extensions for tabular data (spreadsheets and CSVs)
    TABULAR_FILE_EXTENSIONS = {".xls", ".xlsx", ".csv"}

    def __init__(self, plain_text_chunker: PlainTextChunker):
        """
        Initializes the DocumentChunker.

        Args:
            text_chunker (PlainTextChunker): An instance of `PlainTextChunker` to be
                used for chunking the text extracted from documents.

        Raises:
            TypeError: If `plain_text_chunker` is not an instance of `PlainTextChunker`.
        """
        if not isinstance(plain_text_chunker, PlainTextChunker):
            raise TypeError("plain_text_chunker must be an instance of PlainTextChunker")
        self.plain_text_chunker = plain_text_chunker
        self.pdf_processor = PDFProcessor()
        self.docx_processor = DOCXProcessor()

    def validate_path(self, path: Union[str, Path], mode: str = "general") -> Tuple[Path, str]:
        """
        Validates the file path and its extension against supported types.

        Args:
            path (Union[str, Path]): The path to the document file.
            mode (str): The validation mode, either "general" for text documents or
                "table" for tabular data. Defaults to "general".

        Returns:
            Tuple[Path, str]: A tuple containing the resolved `Path` object and the
            file's lowercase extension.

        Raises:
            InvalidInputError: If the path is invalid or cannot be resolved.
            ValueError: If the file extension is not supported for the given mode.
        """
        try:
            path = Path(str(path))
        except Exception as e:
            raise InvalidInputError from e

        extension = path.suffix.lower()
        if not extension:
            raise InvalidInputError(f"Invalid path: '{path}'. Path must have a recognizable extension.")

        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")

        if mode == "general":
            if extension not in self.GENERAL_TEXT_EXTENSIONS:
                raise ValueError(f"File type '{extension}' is not supported for general document chunking.")
        elif mode == "table":
            if extension not in self.TABULAR_FILE_EXTENSIONS:
                raise ValueError(f"File type '{extension}' is not supported for tabular data chunking.")

        return path, extension

    def _read_file(self, path: Union[str, Path], ext: str) -> str:
        """
        Reads the content of a text-based file and performs necessary conversions.

        This helper method handles reading from .txt, .md, and .rst files.
        It specifically converts .rst content to Markdown.

        Args:
            path (Union[str, Path]): The path to the file.
            ext (str): The file extension (e.g., ".txt", ".rst").

        Returns:
            str: The content of the file as a string.
        """
        if self.plain_text_chunker.verbose:
            logger.debug(f"Reading file: {path} with extension: {ext}")

        with open(path, "r", encoding="utf-8") as f:
            text_content = f.read()
        if ext == ".rst":
            text_content = rst_to_markdown(text_content)

        return text_content

    def chunk(
        self,
        path: Union[str, Path],
        *,
        lang: str = "auto",
        mode: str = "sentence",
        max_tokens: int = 512,
        max_sentences: int = 100,
        overlap_percent: Union[int, float] = 20,
        offset: int = 0,
        token_counter: Optional[Callable[[str], int]] = None,
        n_jobs: Optional[int] = None, # only used for pdf
    ) -> List[Box]:
        """
        Chunks a single document from a given path.

        This method automatically detects the file type and uses the appropriate
        processor to extract text before chunking. It then adds document-level
        metadata to each resulting chunk.

        Args:
            path (Union[str, Path]): The path to the document file.
            lang (str): The language of the text. Defaults to "auto".
            mode (str): The chunking mode ('sentence', 'token', etc.).
            max_tokens (int): The maximum number of tokens per chunk.
            max_sentences (int): The maximum number of sentences per chunk.
            overlap_percent (Union[int, float]): The percentage of overlap.
            offset (int): The starting sentence offset for chunking.
            token_counter (Optional[Callable[[str], int]]): A custom token counter.
            n_jobs (Optional[int]): The number of parallel jobs (only used for PDFs).

        Returns:
            List[Box]: A list of `Box` objects, each representing a chunk with its
            content and metadata.

        Raises:
            NotImplementedError: If the file type is tabular or not supported for
                this method.
            ValueError: If the file path or extension is invalid.
        """
        # Capture all parameters
        params = locals()
        params.pop("self")
        params.pop("path")
        params.pop("n_jobs")

        validated_path, ext = self.validate_path(path, mode="general")
        
        if self.plain_text_chunker.verbose:
            logger.debug(f"Validated path: {validated_path}, detected extension: {ext}")

        text_content = "" # This will hold the text for chunking
        document_metadata = {"source":str(validated_path)}
        
        if ext in {".txt", ".md", ".rst", ".docx"}: 
            if self.plain_text_chunker.verbose:
                logger.debug(f"Processing text-based file: {ext}")
            if ext == ".docx":
                text_content = self.docx_processor.extract_text(validated_path)
            else:
                text_content = self._read_file(validated_path, ext)
            
            # Process as a single block of text
            chunks = self.plain_text_chunker.chunk(
                text=text_content,
                **params
            )
            
            # Append document-level metadata to each chunk
            for chunk in chunks:
                chunk.metadata = document_metadata
            
            if self.plain_text_chunker.verbose:
                logger.info(f"Generated {len(chunks)} chunks for {validated_path}")

            return chunks

        elif ext == ".pdf":
            if self.plain_text_chunker.verbose:
                logger.debug("Processing PDF file with PDFProcessor")
            pdf_data = self.pdf_processor.extract_text(str(validated_path))
            
            # Prepare texts for plain_text_chunker.batch_chunk
            pages_text = pdf_data.pop("pages", [])
            document_metadata.update(pdf_data)
            
            # Call plain_text_chunker.batch_chunk
            all_pages_chunks = self.plain_text_chunker.batch_chunk(
                texts=pages_text,
                n_jobs=n_jobs,
                **params
            )

            final_chunks = []
            for page_num, chunks_from_page in enumerate(all_pages_chunks, start=1):
                # Append page-specific and document-level metadata to each chunk
                for chunk in chunks_from_page:
                    # Add page_num
                    page_metadata = document_metadata.copy()
                    page_metadata["page_num"] = page_num
                    chunk.metadata = page_metadata
                    final_chunks.append(chunk)
            
            if self.plain_text_chunker.verbose:
                logger.info(f"Generated {len(final_chunks)} chunks for {validated_path} (from PDF)")

            return final_chunks
    
    def bulk_chunk(
        self,
        paths: List[Union[str, Path]],
        *,
        lang: str = "auto",
        mode: str = "sentence",
        max_tokens: int = 512,
        max_sentences: int = 100,
        overlap_percent: Union[int, float] = 20,
        offset: int = 0,
        token_counter: Optional[Callable[[str], int]] = None,
        n_jobs: Optional[int] = None,
    ) -> List[Box]:
        """
        Chunks multiple documents from a list of file paths.

        This method iterates through a list of paths, calling the `chunk()` method
        for each one and consolidating the results into a single list.

        Args:
            paths (List[Union[str, Path]]): A list of paths to the document files.
            lang (str): The language of the text.
            mode (str): The chunking mode.
            max_tokens (int): Maximum tokens per chunk.
            max_sentences (int): Maximum sentences per chunk.
            overlap_percent (Union[int, float]): Overlap percentage between chunks.
            offset (int): Token offset for subsequent chunks.
            token_counter (Optional[Callable[[str], int]]): Custom token counter.
            n_jobs (Optional[int]): Number of parallel jobs to use within each call
                to `chunk()` (e.g., for PDFs).

        Returns:
            List[Box]: A single list of `Box` objects containing all chunks from
            all processed documents.
        """
        if self.plain_text_chunker.verbose:
            logger.info(f"Starting bulk chunking for {len(paths)} documents.")
            
        # Parameters to pass to plain_text_chunker.batch_chunk  
        chunk_params = {k: v for k, v in locals().items() if k not in ['self', 'paths']}

        all_texts = []
        all_document_metadata = []
        for file_path_str in paths:
            file_path = Path(file_path_str)
            if not file_path.is_file():
                if self.plain_text_chunker.verbose:
                    logger.warning(f"Skipping non-file path: {file_path}")
                continue    

            try:
                validated_path, ext = self.validate_path(file_path, mode="general")
            except ValueError:
                if self.plain_text_chunker.verbose:
                    logger.warning(f"Skipping unsupported file type: {file_path}")
                continue
            document_metadata = {"source":str(validated_path)}       

            if self.plain_text_chunker.verbose:
                logger.debug(f"Processing file: {validated_path}, detected extension: {ext}")
                
            if ext == ".pdf":
                pdf_data = self.pdf_processor.extract_text(str(validated_path))
                pages_text = pdf_data.pop("pages", [])
                document_metadata.update(pdf_data)
                
                # For PDFs, each page is a separate text in the batch
                all_texts.extend(pages_text)
                for i in range(len(pages_text)):
                    page_metadata = document_metadata.copy()
                    page_metadata["page_num"] = i + 1
                    all_document_metadata.append(page_metadata) 
            elif ext == ".docx":
                text_content = self.docx_processor.extract_text(validated_path)
                all_texts.append(text_content)
                all_document_metadata.append(document_metadata)  
            elif ext in self.GENERAL_TEXT_EXTENSIONS - {".pdf", ".docx"}:
                text_content = self._read_file(validated_path, ext)
                all_texts.append(text_content)
                all_document_metadata.append(document_metadata)
            else:
                if self.plain_text_chunker.verbose:
                    logger.warning(f"File type {ext} not supported for bulk chunking: {validated_path}")
                continue    

        if not all_texts:
            if self.plain_text_chunker.verbose:
                logger.info("No valid texts found for batch chunking. Returning empty list.")
                return [] 
 
        # Perform a single batch chunking operation
        all_chunks = self.plain_text_chunker.batch_chunk(
            texts=all_texts,
            **chunk_params
        )
        
        final_chunks = []
         # Iterate through the results and attach metadata
        for doc_idx, doc_chunks in enumerate(all_chunks):
            curr_doc_metadata = all_document_metadata[doc_idx]
            for chunk in doc_chunks:
                chunk.metadata = curr_doc_metadata
                final_chunks.append(chunk) 
        
        if self.plain_text_chunker.verbose:
            logger.info(f"Finished bulk chunking. Generated {len(final_chunks)} chunks from {len(paths)} documents.")
        return final_chunks

    def chunk_table(
        self,
        path: Union[str, Path],
        *,
        max_lines: int = 100,
    ) -> List[Box]:
        """
        Chunks a tabular data file (Excel or CSV) into smaller tables.

        Each chunk is a list of lists, with the header row repeated at the top
        of each chunk. This method is designed for structured tabular data.

        Args:
            path (Union[str, Path]): The path to the Excel or CSV file.
            max_lines (int): The maximum number of lines (header + data rows)
                per chunk. Must be greater than 1.

        Returns:
            List[Box]: A list of `Box` objects, where each chunk's content is a
            smaller table (list of lists).

        Raises:
            FileNotFoundError: If the specified path does not exist.
            ValueError: If `max_lines` is not greater than 1.
            RuntimeError: If there is an error processing the file.
        """
        try:
            import openpyxl
        except ImportError:
            raise ImportError(
                "The 'openpyxl' library is not installed. "
                "Please install it with 'pip install openpyxl' or install the document processing extras "
                "with 'pip install 'chunklet-py[document]''"
            )
        if self.plain_text_chunker.verbose:
            logger.info(f"Starting tabular chunking for {path}")

        path, file_extension = self.validate_path(path, mode="table")
        
        document_metadata: Dict[str, Any] = {"source":str(path)}
        rows: List[List[Any]] = []

        try:
            if file_extension in {".xls", ".xlsx"}:
                workbook = openpyxl.load_workbook(path)
                sheet = workbook.active 
                rows = [list(row) for row in sheet.iter_rows(values_only=True) if any(row)]
                
                if workbook.properties.creator:
                    document_metadata["author"] = workbook.properties.creator
                if workbook.properties.title:
                    # Add active sheet name
                    document_metadata["title"] = workbook.properties.title
                document_metadata["sheet_name"] = sheet.title
                document_metadata["sheet_count"] = len(workbook.sheetnames)
            elif file_extension == '.csv':
                with open(path, "r", encoding="utf-8", newline='') as f:
                    reader = csv.reader(f)
                    rows = [list(row) for row in reader]
            
            if not rows:
                if self.plain_text_chunker.verbose:
                    logger.info(f"No data found in {path}. Returning empty list.")
                return []

            header, *data_rows = rows
            
        except Exception as e:
            raise RuntimeError(f"Error processing file {path}: {e}") from e
            
        chunks = []
        # chunk_size is the number of data rows per chunk
        chunk_size = max_lines - 1 
        if chunk_size <= 0:
            raise ValueError("max_lines must be greater than 1 to include the header and at least one data row.")

        for i in range(0, len(data_rows), chunk_size):
            chunk_box = Box()
            chunk_box.content = [header] + data_rows[i:i + chunk_size]
            chunk_box.metadata = document_metadata.copy()
            chunk_box.metadata.start_row = i + 2 # 1-based index + header
            chunk_box.max_lines = max_lines 
            chunks.append(chunk_box)
            
        if self.plain_text_chunker.verbose:
            logger.info(f"Generated {len(chunks)} chunks for tabular file {path}")

        return chunks
