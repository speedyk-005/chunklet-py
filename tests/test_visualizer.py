"""Tests for the visualizer module."""

import pytest
import json
import time
import requests
import urllib.request
import urllib.error
import threading
from pathlib import Path
from chunklet.visualizer import Visualizer


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
    port = 8001

    try:
        visualizer = Visualizer(host=host, port=port)
        thread = threading.Thread(target=visualizer.serve, daemon=True)
        thread.start()

        url = f"http://{host}:{port}"
        wait_for_server(url)

        yield {
            "url": url,
            "host": host,
            "port": port,
            "thread": thread,
            "visualizer": visualizer,
        }
    except ImportError as e:
        pytest.skip(f"Visualization dependencies not available: {e}")
    except TimeoutError as e:
        pytest.skip(f"Visualizer server failed to start: {e}")


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

    # Test
    with open(sample_file_path, "rb") as f:
        files = {"file": ("sample_text.txt", f, "text/plain")}
        data = {
            "mode": "document",
            "params": json.dumps(
                {"max_sentences": 3, "overlap_percent": 20}  # Chunk by 3 sentences
            ),
        }

        response = requests.post(url, files=files, data=data)
        assert response.status_code == 200

        result = response.json()
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


def test_chunk_file_invalid_format(visualizer_server):
    """Test uploading invalid file format."""
    url = f"{visualizer_server['url']}/api/chunk"

    # Create a mock binary file
    import io

    binary_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"  # PNG header

    files = {"file": ("fake.png", io.BytesIO(binary_data), "image/png")}
    data = {"mode": "document"}

    response = requests.post(url, files=files, data=data)
    assert response.status_code == 400

    error_detail = response.json()
    assert "detail" in error_detail
    assert "only text files are supported." == error_detail["detail"].lower()
