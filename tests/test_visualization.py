"""Tests for the visualizer module."""

import json
import socket
import threading
import time
import urllib.error
import urllib.request
from contextlib import closing
from pathlib import Path

import msgpack
import pytest

from chunklet.visualizer import Visualizer


def _multipart_post(
    url: str,
    *,
    file_content: bytes,
    file_name: str,
    fields: dict | None,
    headers: dict | None,
) -> urllib.request.Request:
    """POST a multipart/form-data upload using urllib."""
    boundary = "----chunklet-boundary"
    body = bytearray()
    for key, value in (fields or {}).items():
        body += (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{key}"\r\n\r\n'
            f"{value}\r\n"
        ).encode()
    body += (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; '
        f'filename="{file_name}"\r\nContent-Type: text/plain\r\n\r\n'
    ).encode()
    body += file_content
    body += f"\r\n--{boundary}--\r\n".encode()

    request_headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    request_headers.update(headers or {})
    return urllib.request.urlopen(
        urllib.request.Request(
            url, data=bytes(body), headers=request_headers, method="POST"
        ),
        timeout=10,
    )


def get_free_port() -> int:
    """Find a free port to use for testing."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_for_server(url: str, timeout: float = 10.0) -> bool:
    """Wait for server to be ready with retry logic."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = urllib.request.urlopen(f"{url}/health", timeout=2)
            if response.getcode() == 200:
                return True
        except (urllib.error.URLError, ConnectionError):
            pass

        time.sleep(0.5)  # Brief delay between checks

    raise TimeoutError(f"Server not ready at {url} after {timeout} seconds")


@pytest.fixture(scope="session")
def visualizer_server():
    """Start visualizer server in daemon thread for testing."""
    host = "127.0.0.1"
    port = get_free_port()

    visualizer = Visualizer(host=host, port=port)
    thread = threading.Thread(target=visualizer.serve, daemon=True)
    thread.start()

    url = f"http://{host}:{port}"  # noqa: S310
    wait_for_server(url)

    yield {
        "url": url,
        "host": host,
        "port": port,
        "thread": thread,
        "visualizer": visualizer,
    }


# --- API Endpoints Testing---


def test_visualizer_token_counter_status(visualizer_server):
    """Test that the token counter status endpoint is working."""
    url = f"{visualizer_server['url']}/api/token_counter_status"

    # Test initially - should be False (no token counter set)
    response = urllib.request.urlopen(url, timeout=5)
    assert response.getcode() == 200

    data = json.loads(response.read().decode())
    assert "token_counter_available" in data
    assert data["token_counter_available"] is False

    # Add token counter
    visualizer_server["visualizer"].token_counter = lambda x: len(x.split())

    # Small delay to ensure property update
    time.sleep(0.1)

    # Test again - should be True now
    response = urllib.request.urlopen(url, timeout=5)
    assert response.getcode() == 200

    data = json.loads(response.read().decode())
    assert "token_counter_available" in data
    assert data["token_counter_available"] is True


def test_chunk_file(visualizer_server):
    """Test file upload and chunking functionality."""
    url = f"{visualizer_server['url']}/api/chunk"

    # Path to sample text file
    sample_file_path = Path(__file__).parent.parent / "samples" / "sample_text.txt"
    assert sample_file_path.exists(), f"Sample file not found: {sample_file_path}"

    # Test with MessagePack format (explicit request)
    data = {
        "mode": "document",
        "params": json.dumps(
            {"max_sentences": 3, "overlap_percent": 20}  # Chunk by 3 sentences
        ),
    }
    headers = {"Accept": "application/msgpack"}

    response = _multipart_post(
        url,
        file_content=sample_file_path.read_bytes(),
        file_name="sample_text.txt",
        fields=data,
        headers=headers,
    )
    assert response.getcode() == 200

    result = msgpack.unpackb(response.read(), raw=False)
    assert "text" in result
    assert "chunks" in result
    assert "stats" in result

    # Verify chunking worked
    assert result["stats"]["chunk_count"] > 1  # Should have multiple chunks
    assert len(result["chunks"]) == result["stats"]["chunk_count"]

    # Verify chunk structure
    for chunk in result["chunks"]:
        assert "content" in chunk
        assert "metadata" in chunk


def test_chunk_file_json_backward_compatible(visualizer_server):
    """Test that JSON response works for backward compatibility."""
    url = f"{visualizer_server['url']}/api/chunk"

    sample_file_path = Path(__file__).parent.parent / "samples" / "sample_text.txt"
    assert sample_file_path.exists(), f"Sample file not found: {sample_file_path}"

    # Test JSON (default - backward compatible)
    data = {
        "mode": "document",
        "params": json.dumps({"max_sentences": 2}),
    }
    # No Accept header = JSON default

    response = _multipart_post(
        url,
        file_content=sample_file_path.read_bytes(),
        file_name="sample_text.txt",
        fields=data,
        headers=None,
    )
    assert response.getcode() == 200

    result = json.loads(response.read().decode())
    assert "text" in result
    assert "chunks" in result
    assert "stats" in result
    assert result["stats"]["chunk_count"] > 1


def test_chunk_file_invalid_format(visualizer_server):
    """Test uploading invalid file format."""
    url = f"{visualizer_server['url']}/api/chunk"

    # Create a mock binary file
    binary_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"  # PNG header
    data = {"mode": "document"}

    with pytest.raises(urllib.error.HTTPError) as exc_info:
        _multipart_post(
            url,
            file_content=binary_data,
            file_name="fake.png",
            fields=data,
            headers=None,
        )

    response = exc_info.value
    assert response.getcode() == 400
    error_detail = json.loads(response.read().decode())
    assert "detail" in error_detail
    assert error_detail["detail"].lower() == "only text files are supported."
