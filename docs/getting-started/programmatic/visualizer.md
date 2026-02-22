# Text Chunk Visualizer

<p align="center">
  <img src="../../../img/visualization.gif" alt="Text Chunk Visualizer Demo" width="600"/>
  <br><em>Interactive chunking in action - upload, process, and explore!</em>
</p>

## Quick Install

```bash
pip install chunklet-py[visualization]
```

## Text Chunk Visualizer: Your Window into the Chunking Abyss

This installs the web interface dependencies (FastAPI + Uvicorn) for interactive chunk visualization! 🌐

Ever wondered what your text or code looks like after being chopped up by a chunking algorithm? The Text Chunk Visualizer demystifies text segmentation with a clean web interface - [WYSIWYG](https://en.wikipedia.org/wiki/WYSIWYG) (what you see is what you get).

No more guessing games - see your chunking results in real-time!

### So How Do I Get This Running?

First, make sure you have the visualization dependencies:

```bash
pip install "chunklet-py[visualization]"
```

Here's the basic code to get it running:

``` py linenums="1"
from chunklet.visualizer import Visualizer

# Optional: Define a custom token counter
# def my_token_counter(text: str) -> int:
#     return len(text.split())  # Simple word-based counting

visualizer = Visualizer(
    host="127.0.0.1",    #(1)!
    port=8000,          #(2)!
    # token_counter=my_token_counter  # Uncomment if using custom counter
)

visualizer.serve()  # Blocks until Ctrl+C
```

1. **Host**: The IP address where the server will listen. Use `"127.0.0.1"` for localhost or `"0.0.0.0"` to allow access from other devices on your network.
2. **Port**: The port number for the web server. The visualizer will be accessible at `http://host:port`.  

??? success "Click to show output"
    ```linenums="0"
    Starting Chunklet Visualizer...
    URL: http://127.0.0.1:8000
    Press Ctrl+C to stop the server
    Opened in default browser
     = = = = = = = = = = = = = = = = = = = = = = = = = =

    TEXT CHUNK VISUALIZER
    = = = = = = = = = = = = = = = = = = = = = = = = = =
    URL: http://127.0.0.1:8000
    INFO:     Started server process [30999]
    INFO:     Waiting for application startup.
    INFO:     Application startup complete.
    INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
    INFO:     127.0.0.1:45482 - "GET / HTTP/1.1" 200 OK
    INFO:     127.0.0.1:45490 - "GET /static/js/app.js HTTP/1.1" 200 OK
    INFO:     127.0.0.1:45482 - "GET /static/css/style.css HTTP/1.1" 304 Not Modified
    INFO:     127.0.0.1:45490 - "GET /api/token_counter_status HTTP/1.1" 200 OK
    ```

Run this and you'll see the server start up with the URL where your visualizer is ready!

(But honestly, the CLI `chunklet visualize` command is way easier for most use cases!)

!!! tip "Prefer command line?"
    For quick access without writing code, check out the [CLI visualize command](../cli.md#the-visualize-command-your-interactive-chunk-playground).

### What's the Web Interface Like?

Open your browser to the URL shown in the terminal output. You'll find a clean interface designed for quick chunking experiments.

??? question "How do I upload files?"

    Simple: drag and drop your text files (`.txt`, `.md`, `.py`, etc.) onto the upload area, or click "Browse Files" to select them manually. The visualizer accepts any text-based file.

??? question "What's the difference between Document and Code mode?"

    Choose your chunking strategy after upload:
    
    - **Document Mode**: For general text, articles, and documents - focuses on sentences and sections
    - **Code Mode**: For source code - understands functions, classes, and code structure

    Each mode has its own parameter controls because text and code need different chunking approaches.

??? question "How Do I Process My Content?"

    Select your mode and parameters, then click "Process Document" or "Process Code". The visualizer applies your settings and shows exactly how your content gets chunked.

??? question "What About the Interactive Features?"

    The interface gives you great visibility:
    
    - **Click to Highlight**: Click text to see which chunk(s) contain it
    - **Double-Click for Details**: Get full metadata popups with span, chunk number, and source info
    - **Overlap Toggle**: Use "Reveal Overlaps" to see where chunks share content

??? question "Can I Export My Results?"

    Absolutely! Click "Download Chunks" to get a JSON file with all chunks, their content, and complete [metadata](../metadata.md) - perfect for further processing or analysis.

    The exported JSON follows this structure:

    ```json
    {
        "chunks": [
         {
            "content": "The actual text content of this chunk...",
            "metadata": {
                "source": "path/to/source/file.txt",
                "chunk_num": 1,
                "span": [0, 150],
                // ... other metadata fields
            }
        },
        // ... more chunks
        ],
         "stats": {
        "chunk_count": 3,
        "overlap_count": 2,
        "text_length": 696,
        "mode": "document",
        "generated": "2025-12-18T15:16:11.379Z"
      }
    }
    ```

!!! tip "Quick Tips for Better Results"

    - Start with small files to get familiar with the interface
    - Experiment with different parameter combinations to see their effects
    - Use the metadata views to understand chunk boundaries
    - The visualizer is perfect for comparing chunking strategies side-by-side

    Go experiment! The visualizer makes it easy to see exactly what your settings produce, so you can fine-tune for optimal chunking.

### Headless/REST API Usage

The `Visualizer` isn't just a web interface - it also provides a complete REST API for headless chunking operations. This means you can use Chunklet's interactive features programmatically without the web UI!

#### Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check endpoint |
| `GET` | `/api/token_counter_status` | Check if token counter is configured |
| `POST` | `/api/chunk` | Upload and chunk a file |

#### Chunking Files Programmatically

##### Option 1: CLI Headless Server (Recommended)

The easiest way to start a headless visualizer server is with the CLI:

```bash
chunklet visualize --headless --port 8000
```

!!! tip "CLI Headless Mode"
    See the [Scenario 3: Headless Mode](../cli.md#headless-cli) in the CLI documentation for more details on headless CLI usage with custom tokenizers.

##### Option 2: Python Server Script

For more programmatic control, create a custom server script (`server.py`):

``` py linenums="1"
#!/usr/bin/env python3
"""Headless visualizer server for programmatic chunking."""

from chunklet.visualizer import Visualizer

# Configure your visualizer
visualizer = Visualizer(
    host="127.0.0.1",
    port=8000,
    # token_counter=lambda text: len(text.split())  # Optional custom tokenizer
)

print("Starting headless visualizer server...")
print("Press Ctrl+C to stop")
visualizer.serve()
```

Run the server:

```bash
python server.py
```

##### Using the REST API Client

Use this Python client to chunk files programmatically:

``` py linenums="1"
import requests

# Connect to your running server
base_url = "http://127.0.0.1:8000"

# Check if token counter is available
response = requests.get(f"{base_url}/api/token_counter_status")
print(response.json())  # {"token_counter_available": false}

# Chunk a file
with open("my_document.txt", "rb") as f:
    files = {"file": ("my_document.txt", f, "text/plain")}
    data = {
        "mode": "document",  # or "code"
        "params": '{"max_sentences": 3, "overlap_percent": 20}'
    }

    response = requests.post(f"{base_url}/api/chunk", files=files, data=data)

if response.status_code == 200:
    result = response.json()
    print(f"Created {result['stats']['chunk_count']} chunks")

    # Access chunks
    for chunk in result["chunks"]:
        print(f"Chunk content: {chunk['content']}")
        print(f"Metadata: {chunk['metadata']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```



#### Response Format

The `/api/chunk` endpoint returns:

```json
{
  "text": "Original file content...",
  "chunks": [
    {
      "content": "Chunk text content...",
      "metadata": {
        "source": "filename.txt",
        "chunk_num": 1,
        "span": [0, 150],
        // ... additional metadata
      }
    }
  ],
  "stats": {
    "text_length": 696,
    "chunk_count": 3,
    "mode": "document"
  }
}
```

!!! tip "Perfect for Integration"
    Use the REST API to integrate Chunklet's visualizer capabilities into your own applications, automation scripts, or testing pipelines!

??? info "API Reference"
    For complete technical details on the `Visualizer` class, check out the [API documentation](../../reference/chunklet/visualizer/visualizer.md).
