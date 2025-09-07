import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from concurrent.futures import ThreadPoolExecutor
from box import Box
from chunklet import (
    PlainTextChunker,
    DocumentChunker,
    InvalidInputError,
    ChunkletError,
    CustomProcessorConfig,
)
import shutil
import sys

@pytest.fixture
def mock_plain_text_chunker():
    """Mock PlainTextChunker to isolate DocumentChunker logic"""
    mock = MagicMock(spec=PlainTextChunker)
    mock.verbose = False

    def mock_chunk(text, **kwargs):
        lines = text.splitlines()
        chunks = []
        for i in range(0, len(lines), 2):
            chunk_content = "\n".join(lines[i:i + 2])
            chunks.append(chunk_content) # Append string directly
        return chunks # This will be List[str]

    def mock_batch_chunk(texts, **kwargs):
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(mock_chunk, text) for text in texts]
            return [future.result() for future in futures]

    mock.chunk.side_effect = mock_chunk
    mock.batch_chunk.side_effect = mock_batch_chunk
    return mock


@pytest.fixture
def document_chunker(mock_plain_text_chunker):
    return DocumentChunker(mock_plain_text_chunker)


# Test DocumentChunker Initialization
@pytest.mark.parametrize("input, expected_exception, match_string", [
    (MagicMock(spec=PlainTextChunker), None, ""),
    ("not a PlainTextChunker instance", TypeError, "plain_text_chunker must be an instance of PlainTextChunker"),
])
def test_document_chunker_init(input, expected_exception, match_string):
    """Test DocumentChunker initialization with valid and invalid PlainTextChunker instances."""
    if expected_exception:
        with pytest.raises(expected_exception, match=match_string):
            DocumentChunker(input)
    else:
        chunker = DocumentChunker(input)
        assert isinstance(chunker.plain_text_chunker, PlainTextChunker)


# Test validate_path for both existent/non-existent files and correct/incorrect modes
@pytest.mark.parametrize(
    "path, mode, expected_exception, patch_target, patch_side_effect",
    [
        # Happy Path: Existent files with correct modes (should pass, so no exception)
        ("samples/Lorem.docx", "general", None, None, None),
        ("samples/Registration-11.xlsx", "table", None, None, None),
        ("file_without_extension", "general", InvalidInputError, None, None),

        # Failure Path: Existent files with incorrect modes (should raise ValueError)
        ("samples/Lorem.docx", "table", ValueError, None, None),
        ("samples/sample.xyz", "general", FileNotFoundError, None, None),

        # Failure Path: Non-existent files (should raise FileNotFoundError)
        ("non_existent_file.txt", "general", FileNotFoundError, None, None),

        # Failure Path: Exception during Path object creation
        ("any/path", "general", InvalidInputError, "chunklet.document_chunker.Path", Exception("Test Exception")),
    ]
)
def test_validate_path_correctly_handles_all_cases(document_chunker, path, mode, expected_exception, patch_target, patch_side_effect, tmp_path):
    """Test file path validation for different modes and file types."""
    if "file_without_extension" in str(path):
        p = tmp_path / path
        p.write_text("test")
        path = p

    if patch_target:
        with patch(patch_target, side_effect=patch_side_effect):
            with pytest.raises(expected_exception):
                document_chunker.validate_path(path, mode=mode)
    elif expected_exception:
        with pytest.raises(expected_exception):
            document_chunker.validate_path(path, mode=mode)
    else:
        # For valid cases, ensure the function returns a Path object
        validated_path, _ = document_chunker.validate_path(path, mode=mode)
        assert isinstance(validated_path, Path)




# Test chunk method for different file types
@pytest.mark.parametrize("path, expected_chunk_call_method", [
    ("samples/sample-pdf-a4-size.pdf", "batch_chunk"),
    ("samples/Lorem.docx", "chunk"),
    ("samples/What_is_rst.rst", "chunk"),
    ("samples/complex-layout.rtf", "chunk"),
])
def test_chunk_method_processes_files_correctly(document_chunker, mock_plain_text_chunker, path, expected_chunk_call_method):
    """Test the main chunk method with various supported file types."""
    mock_plain_text_chunker.verbose = True
    chunks = document_chunker.chunk(path)
    assert len(chunks) > 0
    assert "source" in chunks[0].metadata

    if expected_chunk_call_method == "batch_chunk":
        assert "page_num" in chunks[0].metadata
        mock_plain_text_chunker.batch_chunk.assert_called_once()
    else:
        mock_plain_text_chunker.chunk.assert_called_once()


def test_chunk_unsupported_file_type(document_chunker, tmp_path):
    """Test that chunking raises an error for unsupported file types."""
    # Test with a file type that is not in GENERAL_TEXT_EXTENSIONS
    unsupported_file = tmp_path / "test.xyz"
    unsupported_file.write_text("test")
    with pytest.raises(ValueError, match="File type '.xyz' is not supported for general document chunking."):
        document_chunker.chunk(unsupported_file)

    # Test with a tabular file type
    with pytest.raises(ValueError, match="File type '.csv' is not supported for general document chunking."):
        document_chunker.chunk("samples/Registration-100.csv")


# Test bulk_chunk method with multiple files
def test_bulk_chunk(document_chunker, mock_plain_text_chunker, tmp_path):
    """Test bulk chunking with multiple files, including edge cases."""
    mock_plain_text_chunker.verbose = True
    paths = ["samples/sample-pdf-a4-size.pdf", "samples/Lorem.docx"]
    all_document_chunks = document_chunker.bulk_chunk(paths) # This is List[List[Box]]
    
    assert len(all_document_chunks) == len(paths) # Should be one list of chunks per path
    mock_plain_text_chunker.batch_chunk.assert_called_once()

    # Flatten the list of lists for easier assertion on individual chunks
    all_chunks_flat = [chunk for doc_chunks in all_document_chunks for chunk in doc_chunks]

    # Verify that chunks from both files are present and correctly tagged
    pdf_chunks = [chunk for chunk in all_chunks_flat if "sample-pdf-a4-size.pdf" in chunk.metadata["source"]]
    docx_chunks = [chunk for chunk in all_chunks_flat if "Lorem.docx" in chunk.metadata["source"]]
    
    assert len(pdf_chunks) > 0
    assert len(docx_chunks) > 0

    # Test with non-existent file
    paths_with_non_existent = ["samples/Lorem.docx", "non_existent_file.txt"]
    result_non_existent = document_chunker.bulk_chunk(paths_with_non_existent)
    assert len(result_non_existent) == 1 # Only Lorem.docx should be processed
    assert "Lorem.docx" in result_non_existent[0][0].metadata["source"]

    # Test with unsupported file type
    unsupported_file = tmp_path / "test.xyz"
    unsupported_file.write_text("test")
    paths_with_unsupported = ["samples/Lorem.docx", unsupported_file]
    result_unsupported = document_chunker.bulk_chunk(paths_with_unsupported)
    assert len(result_unsupported) == 1 # Only Lorem.docx should be processed
    assert "Lorem.docx" in result_unsupported[0][0].metadata["source"]

    # Test with empty list
    assert document_chunker.bulk_chunk([]) == []

    # Test with only invalid paths
    invalid_paths = ["non_existent_file.txt", str(tmp_path / "unsupported.xyz")]
    (tmp_path / "unsupported.xyz").write_text("test")
    result_invalid = document_chunker.bulk_chunk(invalid_paths)
    assert result_invalid == []


# Test chunk_table method
@pytest.mark.parametrize("path", [
    "samples/Registration-11.xlsx",
    "samples/Registration-100.csv",
])
def test_chunk_table_processes_files_correctly(document_chunker, mock_plain_text_chunker, path):
    """Test table chunking for CSV and XLSX files."""
    mock_plain_text_chunker.verbose = True
    chunks = document_chunker.chunk_table(path)
    assert len(chunks) > 0
    assert "content" in chunks[0]
    assert isinstance(chunks[0].content, list)
    assert len(chunks[0].content) > 1
    assert "source" in chunks[0].metadata


@pytest.mark.parametrize(
    "path, max_lines, expected_exception",
    [
        ("samples/Registration-100.csv", 0, InvalidInputError),
        ("samples/Registration-100.csv", 1, InvalidInputError),
        ("non_existent_file.xlsx", 100, FileNotFoundError),
        ("empty.csv", 100, None),
    ],
)
def test_chunk_table_edge_cases(document_chunker, tmp_path, path, max_lines, expected_exception):
    """Test edge cases for table chunking, such as invalid max_lines and empty files."""
    if "empty.csv" in path:
        p = tmp_path / path
        p.write_text("")
        path = p

    if expected_exception:
        with pytest.raises(expected_exception):
            document_chunker.chunk_table(path, max_lines=max_lines)
    else:
        chunks = document_chunker.chunk_table(path, max_lines=max_lines)
        assert chunks == []

def test_chunk_method_with_custom_processor(document_chunker, mock_plain_text_chunker, tmp_path):
    """Test that the chunk method correctly uses a custom processor."""
    # Define a mock custom processor callback
    def mock_custom_processor_callback(file_path: str) -> str:
        return f"Custom processed content from {file_path}. Line 1. Line 2. Line 3."

    # Create a custom processor
    custom_processor = [
        {
            "name":"MockProcessor",
            "file_extensions":".mock",
            "callback":mock_custom_processor_callback
        }
    ]

    # Re-initialize DocumentChunker with the custom processor
    document_chunker = DocumentChunker(mock_plain_text_chunker, custom_processors=custom_processor)

    # Create a dummy file with the custom extension
    dummy_file = tmp_path / "test.mock"
    dummy_file.write_text("Original content that should be ignored by custom processor.")

    # Chunk the dummy file
    chunks = document_chunker.chunk(dummy_file)

    # Assert that the custom processor's output was used
    expected_content_prefix = f"Custom processed content from {dummy_file}"
    assert len(chunks) > 0
    assert chunks[0].content.startswith(expected_content_prefix)
    assert "source" in chunks[0].metadata
    assert chunks[0].metadata["source"] == str(dummy_file)

    # Verify that plain_text_chunker.chunk was called with the custom processed text
    mock_plain_text_chunker.chunk.assert_called_once_with(
        text=f"Custom processed content from {dummy_file}. Line 1. Line 2. Line 3.",
        lang="auto", mode="sentence", max_tokens=256, max_sentences=12, overlap_percent=20, offset=0, token_counter=None
    )