import os
import json
import tempfile
import traceback
import mimetypes
from typing import Callable
import aiofiles

try:
    import uvicorn
    from charset_normalizer import detect
    from fastapi import FastAPI, UploadFile, File, Form, HTTPException
    from fastapi.responses import HTMLResponse
    from fastapi.staticfiles import StaticFiles
except ImportError:
    # Lambda placeholders prevent "None is not callable" errors when imports fail
    # This allows the module to be imported without dependencies, with proper error handling later
    uvicorn = None
    detect = None
    FastAPI = None
    UploadFile = None
    File = lambda x: x  # noqa: E731
    Form = lambda x: x  # noqa: E731
    HTTPException = None
    HTMLResponse = lambda x: x  # noqa: E731
    StaticFiles = None

from chunklet.document_chunker import DocumentChunker
from chunklet.code_chunker import CodeChunker
from chunklet.common.validation import validate_input


class Visualizer:
    """A FastAPI-based web interface for visualizing document and code chunks.

    This server allows users to upload text or code files, processes them with
    Chunklet's `DocumentChunker` or `CodeChunker`, and returns the chunked
    data along with statistics. A minimal frontend interface is served at the
    root endpoint.

    Attributes:
        host (str): Host IP to bind the FastAPI server.
        port (int): Port number to run the server on.
        document_chunker (DocumentChunker): Chunklet document chunker instance.
        code_chunker (CodeChunker): Chunklet code chunker instance.
        app (FastAPI): FastAPI application instance.
    """

    @validate_input
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8000,
        token_counter: Callable[[str], int] | None = None,
    ):
        """Initializes the Visualizer server and configures chunkers.

        Args:
            host (str): Host IP to run the server. Defaults to "127.0.0.1".
            port (int): Port number to run the server. Defaults to 8000.
            token_counter (Optional[Callable[[str], int]]): Function to count tokens
                in text/code. Required for chunkers if used with `max_tokens`.
        """
        if FastAPI is None:
            raise ImportError(
                "The 'fastapi' library is not installed. "
                "Please install it with 'pip install fastapi>=0.115.12' or install the visualization extras "
                "with 'pip install 'chunklet-py[visualization]''"
            )

        self.host = host
        self.port = port
        self._token_counter = token_counter

        self.app = FastAPI()

        # Initialize chunkers
        self.document_chunker = DocumentChunker(token_counter=token_counter)
        self.code_chunker = CodeChunker(token_counter=token_counter)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        static_dir = os.path.join(base_dir, "static")

        self.app.mount("/static", StaticFiles(directory=static_dir), name="static")

        # API endpoints
        self.app.get("/api/token_counter_status")(self._get_token_counter_status)
        self.app.get("/health")(self._get_health_check)
        self.app.get("/")(self._get_index)
        self.app.post("/api/chunk")(self._chunk_file)

    # Instance endpoint methods
    def _get_token_counter_status(self):
        return {"token_counter_available": self.token_counter is not None}

    def _get_health_check(self):
        """Health check endpoint for testing."""
        return {"status": "healthy"}

    async def _get_index(self):
        """Serves the main HTML interface for the visualizer.

        Returns:
            HTMLResponse: The content of index.html if exists, else a default heading.
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        static_dir = os.path.join(base_dir, "static")
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            async with aiofiles.open(index_path, "r", encoding="utf-8") as f:
                content = await f.read()
                return HTMLResponse(content=content)
        return HTMLResponse(content="<h1>Text Chunk Visualizer</h1>")

    @validate_input
    async def _chunk_file(
        self,
        file: UploadFile = File(...),
        mode: str = Form("document"),
        params: str = Form("{}"),
    ) -> dict:
        """Processes an uploaded file and returns chunked output.

        Args:
            self: The Visualizer instance.
            file (UploadFile): File uploaded by the client.
            mode (str): Determines which chunker to use ("document" or "code").
            params (str): JSON string containing chunking parameters.

        Returns:
            dict: Contains original text, chunked content, and statistics.

        Raises:
            HTTPException: If chunking fails.
        """
        # Parse params JSON and filter out None values
        try:
            chunker_params = json.loads(params)
            chunker_params = {k: v for k, v in chunker_params.items() if v is not None}
        except (json.JSONDecodeError, TypeError):
            raise HTTPException(400, f"Invalid chunking parameters JSON: {params}")

        # Use Python mimetypes instead of browser content_type
        mimetype, _ = mimetypes.guess_type(file.filename or "")
        if not mimetype or not mimetype.startswith("text/"):
            raise HTTPException(400, "Only text files are supported.")

        if detect is None:
            raise HTTPException(
                400,
                "charset-normalizer library is not available. Please install visualization dependencies."
                "with 'pip install 'chunklet-py[visualization]''",
            )

        # Saved as txt file since they are all plaintext anyway
        async with aiofiles.tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as tmp:
            content = await file.read()
            await tmp.write(content)
            tmp_path = tmp.name

        encoding = detect(content).get("encoding", "utf-8")
        text = content.decode(encoding, errors="ignore")
        chunker = self.code_chunker if mode == "code" else self.document_chunker

        try:
            chunks = [
                dict(chunk) for chunk in chunker.chunk(tmp_path, **chunker_params)
            ]

            return {
                "text": text,
                "chunks": chunks,
                "stats": {
                    "text_length": len(text),
                    "chunk_count": len(chunks),
                    "mode": mode,
                },
            }

        except Exception as e:
            traceback.print_exc()
            raise HTTPException(
                500,
                f"Chunking failed. Please check the server terminal for specific error details. ({str(e)})",
            )
        finally:
            # Always cleanup temp file
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    @property
    def token_counter(self):
        """Get the current token counter function."""
        return self._token_counter

    @token_counter.setter
    @validate_input
    def token_counter(self, value):
        """Set the token counter and update both chunkers."""
        self._token_counter = value
        self.document_chunker.token_counter = value
        self.code_chunker.token_counter = value

    def serve(self):
        """Starts the FastAPI server and prints the server URL."""
        if uvicorn is None:
            raise ImportError(
                "The 'uvicorn' library is not installed. "
                "Please install it with 'pip install uvicorn>=0.34.0' or install the visualization extras "
                "with 'pip install 'chunklet-py[visualization]''"
            )

        print(" =" * 20)
        print("\nTEXT CHUNK VISUALIZER")
        print("= " * 20)
        print(f"URL: http://{self.host}:{self.port}")

        uvicorn.run(self.app, host=self.host, port=self.port)


if __name__ == "__main__":  # pragma: no cover
    visualizer = Visualizer()
    visualizer.serve()
