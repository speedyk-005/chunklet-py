import sys
import json
import typer
from typing import Optional, List
from pathlib import Path
from enum import Enum
import subprocess
import shlex
import socket
from importlib.metadata import version, PackageNotFoundError

from chunklet.sentence_splitter import SentenceSplitter
from chunklet.plain_text_chunker import PlainTextChunker

try:
    from chunklet.document_chunker import DocumentChunker
except ImportError:
    DocumentChunker = None

try:
    from chunklet.code_chunker import CodeChunker
except ImportError:
    CodeChunker = None

try:
    from chunklet.visualizer import Visualizer
except ImportError:
    Visualizer = None

from chunklet.common.path_utils import is_path_like


try:
    __version__ = version("chunklet-py")
except PackageNotFoundError:
    __version__ = "unknown"


class ChunkMode(str, Enum):
    sentence = "sentence"
    token = "token"
    hybrid = "hybrid"


class OnError(str, Enum):
    raise_ = "raise"
    skip = "skip"
    break_ = "break"


class DocstringMode(str, Enum):
    summary = "summary"
    all_ = "all"
    excluded = "excluded"


app = typer.Typer(
    name="chunklet",
    help="Advanced text, code, and document chunking for LLM applications. Split content semantically, visualize chunks interactively, and process multiple file formats with flexible, context-aware segmentation.",
    rich_help_panel=True,
    add_completion=False,
)


def _create_external_tokenizer(command_str: str):
    command_list = shlex.split(command_str)

    def external_tokenizer(text):
        try:
            process = subprocess.run(
                command_list,
                shell=False,
                input=text,
                capture_output=True,
                text=True,
                check=True,
            )
            return int(process.stdout.strip())
        except (subprocess.CalledProcessError, ValueError) as e:
            print(f"Error executing tokenizer command: {e}", file=sys.stderr)
            sys.exit(1)

    return external_tokenizer


def _check_port_available(host: str, port: int) -> bool:
    """Check if a port is available on the given host."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result != 0  # 0 means connection successful (port in use)
    except Exception:
        return False


def _extract_files(source: Optional[List[Path]]) -> List[Path]:
    """Extract and validate file paths from the source list."""
    file_paths = []

    for path in source:
        path = path.resolve()

        if is_path_like(str(path)):
            if path.is_file():
                file_paths.append(path)
            elif path.is_dir():
                file_paths.extend([p for p in path.glob("**/*") if p.is_file()])
            else:
                # This single 'else' catches paths that pass the heuristic but
                # either don't exist OR exist but are special file types
                # (e.g., pipes, sockets, broken symlinks, etc.)
                typer.echo(
                    f"Warning: '{path}' is path-like but was not found "
                    "or is not a processable file/directory. Skipping.",
                    err=True,
                )
        else:
            # Fails the path-like regex heuristic check
            typer.echo(
                f"Warning: '{path}' does not resemble a valid file system path "
                "(failed heuristic check). Skipping.",
                err=True,
            )

    if not file_paths:
        typer.echo(
            "Warning: No processable files found in the specified source(s). Exiting.",
            err=True,
        )
        raise typer.Exit(code=0)

    return file_paths


def _write_chunks(chunks, destination: Path, metadata: bool):
    """Write chunks to a destination (file as JSON or directory as separate files)."""
    if destination.suffix == ".json" or destination.is_file():
        # Write as JSON
        if destination.suffix != ".json":
            typer.echo(
                f"Warning: Writing to a non-JSON file extension '{destination.suffix}'. Output will be JSON format.",
                err=True,
            )

        all_chunks = [chunk_box.to_dict() for chunk_box in chunks]

        if not metadata:
            for chunk_dict in all_chunks:
                del chunk_dict["metadata"]

        json_str = json.dumps(all_chunks, indent=4)
        destination.write_text(json_str, encoding="utf-8")
        typer.echo(
            f"Successfully wrote {len(all_chunks)} chunks to {destination} as JSON"
        )
        return

    # Write to directory
    destination.mkdir(parents=True, exist_ok=True)
    total_chunks_written = 0
    processed_sources = set()

    for chunk_box in chunks:
        source_name = chunk_box.metadata["source"]
        base_name = Path(source_name).stem

        base_output_filename = f"{base_name}_chunk_{chunk_box.metadata['chunk_num']}"

        # Write content file
        output_txt_path = destination / f"{base_output_filename}.txt"
        with open(output_txt_path, "w", encoding="utf-8") as f:
            f.write(chunk_box.content + "\n")

        total_chunks_written += 1

        # Write metadata file if requested
        if metadata:
            output_json_path = destination / f"{base_output_filename}.json"
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump(chunk_box.metadata.to_dict(), f, indent=4)

        processed_sources.add(source_name)

    message = (
        f"Successfully processed {len(processed_sources)} input(s)"
        f"and wrote {total_chunks_written} chunk file(s) to {destination}"
    )
    message += " (with .json metadata files)." if metadata else "."
    typer.echo(message)


def _print_chunks(chunks, destination: Optional[Path], metadata: bool):
    """Print or write chunks to stdout or a single file."""
    output_content = []

    chunk_counter = 0
    for chunk_box in chunks:
        chunk_counter += 1
        output_content.append(f"## --- Chunk {chunk_counter} ---")
        output_content.append(chunk_box.content)
        output_content.append("")
        if metadata:
            chunk_metadata = chunk_box.metadata.to_dict()
            output_content.append("\n--- Metadata ---")  # Use a sub-header

            for key, value in chunk_metadata.items():
                # Use clean pipe formatting for terminal style tables
                output_content.append(f"| {key}: {value}")

            output_content.append("\n")

    output_str = "\n".join(output_content)

    if destination:
        destination.write_text(output_str, encoding="utf-8")
    else:
        typer.echo(output_str)


@app.command(name="split", help="Splits text or a single file into sentences.")
def split_command(
    text: Optional[str] = typer.Argument(
        None, help="The input text to split. If not provided, --source must be used."
    ),
    source: Optional[Path] = typer.Option(
        None,
        "--source",
        "-s",
        help="Path to a single file to read input from. Cannot be a directory or multiple files.",
    ),
    destination: Optional[Path] = typer.Option(
        None,
        "--destination",
        "-d",
        help="Path to a single file to write the segmented sentences (separated by \\n). Cannot be a directory.",
    ),
    lang: str = typer.Option(
        "auto",
        "--lang",
        help="Language of the text (e.g., 'en', 'fr', 'auto').",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging."
    ),
):
    """Split text or a single file into sentences"""
    # Validation and Input Acquisition
    provided_inputs = [arg for arg in [text, source] if arg is not None]

    if len(provided_inputs) == 0:
        typer.echo(
            "Error: No input provided. Please use a text argument or the --source option.",
            err=True,
        )
        raise typer.Exit(code=1)

    if len(provided_inputs) > 1:
        typer.echo(
            "Error: Provide either a text string, or use the --source option, but not both.",
            err=True,
        )
        raise typer.Exit(code=1)

    if source:
        # --- Source Constraints ---
        if source.is_dir():
            typer.echo(
                f"Error: Source path '{source}' cannot be a directory for the 'split' command.",
                err=True,
            )
            raise typer.Exit(code=1)
        if not source.is_file():
            typer.echo(
                f"Error: Source path '{source}' not found or is not a file.",
                err=True,
            )
            raise typer.Exit(code=1)

        try:
            input_text = source.read_text(encoding="utf-8")
        except Exception as e:
            typer.echo(f"Error reading source file: {e}", err=True)
            raise typer.Exit(code=1)
    else:
        input_text = text

    # --- Destination Constraint ---
    if destination and destination.is_dir():
        typer.echo(
            f"Error: Destination path '{destination}' cannot be a directory for the 'split' command.",
            err=True,
        )
        raise typer.Exit(code=1)

    # Split Logic
    splitter = SentenceSplitter(verbose=verbose)
    lang_detected, confidence = splitter.detected_top_language(input_text)
    sentences = splitter.split(input_text, lang=lang or lang_detected)

    # Output Handling
    if destination:
        output_str = "\n".join(sentences)
        source_display = f"from {source.name}" if source else "(from stdin)"

        try:
            destination.write_text(output_str, encoding="utf-8")
            typer.echo(
                f"Successfully split and wrote {len(sentences)} sentences "
                f"{source_display} to {destination} (Confidence: {confidence})",
                err=True,
            )
        except Exception as e:
            typer.echo(f"Error writing to destination file: {e}", err=True)
            raise typer.Exit(code=1)
    else:
        source_display = f"Source: {source.name}" if source else "Source: stdin"

        typer.echo(
            f"--- Sentences ({len(sentences)}): "
            f" [{source_display} | Lang: {lang.upper()} | Confidence: {confidence}] ---"
        )

        for sentence in sentences:
            typer.echo(sentence)


@app.command(name="chunk", help="Chunk text or files based on specified parameters.")
def chunk_command(
    text: Optional[str] = typer.Argument(
        None, help="The input text to chunk. If not provided, --source must be used."
    ),
    source: Optional[List[Path]] = typer.Option(
        None,
        "--source",
        "-s",
        help="Path(s) to one or more files or directories to read input from. Overrides the 'text' argument.",
    ),
    # flags for chunker type
    code: bool = typer.Option(False, "--code", help="Use CodeChunker for code files."),
    doc: bool = typer.Option(
        False, "--doc", help="Use DocumentChunker for document files."
    ),
    destination: Optional[Path] = typer.Option(
        None,
        "--destination",
        "-d",
        help="Path to a file (for single output) or a directory (for batch output) to write the chunks.",
    ),
    lang: str = typer.Option(
        "auto",
        "--lang",
        help="Language of the text (e.g., 'en', 'fr', 'auto'). (default: auto)",
    ),
    max_tokens: int = typer.Option(
        None,
        "--max-tokens",
        help="Maximum number of tokens per chunk. Applies to all chunking strategies. (must be >= 12)",
    ),
    max_sentences: int = typer.Option(
        None,
        "--max-sentences",
        help="Maximum number of sentences per chunk. Applies to PlainTextChunker and DocumentChunker. (must be >= 1)",
    ),
    max_section_breaks: Optional[int] = typer.Option(
        None,
        "--max-section-breaks",
        help="Maximum number of section breaks per chunk. Applies to PlainTextChunker and DocumentChunker. (must be >= 1)",
    ),
    overlap_percent: float = typer.Option(
        20.0,
        "--overlap-percent",
        help="Percentage of overlap between chunks (0-85). Applies to PlainTextChunker and DocumentChunker. (default: 20)",
    ),
    offset: int = typer.Option(
        0,
        "--offset",
        help="Starting sentence offset for chunking. Applies to PlainTextChunker and DocumentChunker. (default: 0)",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging."
    ),
    tokenizer_command: Optional[str] = typer.Option(
        None,
        "--tokenizer-command",
        help=(
            "A shell command to use for token counting. "
            "The command should take text as stdin and output the token count as a number."
        ),
    ),
    metadata: bool = typer.Option(
        False,
        "--metadata",
        help=(
            "Include metadata in the output. If --destination is a directory, "
            "metadata is saved as separate .json files; otherwise, it's "
            "included inline in the output."
        ),
    ),
    # for Batching
    n_jobs: Optional[int] = typer.Option(
        None,
        "--n-jobs",
        help="Number of parallel jobs for batch chunking. (default: None, uses all available cores)",
    ),
    on_errors: OnError = typer.Option(
        OnError.raise_,
        "--on-errors",
        help="How to handle errors during processing: 'raise', 'skip' or 'break'",
    ),
    # CodeChunker specific arguments
    max_lines: int = typer.Option(
        None,
        "--max-lines",
        help="Maximum number of lines per chunk. Applies to CodeChunker only. (must be >= 5)",
    ),
    max_functions: int = typer.Option(
        None,
        "--max-functions",
        help="Maximum number of functions per chunk. Applies to CodeChunker only. (must be >= 1)",
    ),
    docstring_mode: DocstringMode = typer.Option(
        DocstringMode.all_,
        "--docstring-mode",
        help="Docstring processing strategy for CodeChunker: 'summary', 'all', or 'excluded'. Applies to CodeChunker only.",
    ),
    strict: bool = typer.Option(
        True,
        "--strict",
        help="If True, raise error when structural blocks exceed max_tokens in CodeChunker. If False, split oversized blocks. Applies to CodeChunker only.",
    ),
    include_comments: bool = typer.Option(
        True,
        "--include-comments",
        help="Include comments in output chunks for CodeChunker. Applies to CodeChunker only.",
    ),
):
    """Chunk text or files based on specified parameters."""
    # --- Input validation logic ---
    provided_inputs = [arg for arg in [text, source] if arg]

    if len(provided_inputs) == 0:
        typer.echo(
            "Error: No input provided. Please provide a text, or use the --source option.",
            err=True,
        )
        raise typer.Exit(code=1)

    if len(provided_inputs) > 1:
        typer.echo(
            "Error: Please provide either a text string, or use the --source option, but not both.",
            err=True,
        )
        raise typer.Exit(code=1)

    if doc and code:
        typer.echo(
            "Error: Please specify either '--doc' or '--code', but not both.",
            err=True,
        )
        raise typer.Exit(code=1)

    # --- Tokenizer setup ---
    token_counter = None
    if tokenizer_command:
        token_counter = _create_external_tokenizer(tokenizer_command)

    # Construct chunk_kwargs dynamically
    chunk_kwargs = {
        "max_tokens": max_tokens,
        "token_counter": token_counter,
    }

    if code:
        if CodeChunker is None:
            typer.echo(
                "Error: CodeChunker dependencies not available.\n"
                "Please install with: pip install chunklet-py[code]",
                err=True,
            )
            raise typer.Exit(code=1)

        chunker_instance = CodeChunker(
            verbose=verbose,
            token_counter=token_counter,
        )
        chunk_kwargs.update(
            {
                "max_lines": max_lines,
                "max_functions": max_functions,
                "docstring_mode": docstring_mode,
                "strict": strict,
                "include_comments": include_comments,
            }
        )
    else:
        if text:
            chunker_instance = PlainTextChunker(
                verbose=verbose,
                token_counter=token_counter,
            )
        else:
            if DocumentChunker is None:
                typer.echo(
                    "Error: DocumentChunker dependencies not available.\n"
                    "Please install with: pip install chunklet-py[document]",
                    err=True,
                )
                raise typer.Exit(code=1)

            chunker_instance = DocumentChunker(
                verbose=verbose,
                token_counter=token_counter,
            )
        chunk_kwargs.update(
            {
                "lang": lang,
                "max_sentences": max_sentences,
                "max_section_breaks": max_section_breaks,
                "overlap_percent": overlap_percent,
                "offset": offset,
            }
        )

    # --- Chunking logic ---
    if text:
        chunks = chunker_instance.chunk(
            text=text,
            **chunk_kwargs,
        )
    else:
        file_paths = _extract_files(source)

        if len(file_paths) == 1 and file_paths[0].suffix not in {
            ".docx",
            ".epub",
            ".pdf",
            ".odt",
        }:
            single_file = file_paths[0]
            chunks = chunker_instance.chunk(
                path=single_file,
                **chunk_kwargs,
            )
        else:
            # Batch input logic
            chunks = chunker_instance.batch_chunk(
                paths=file_paths,
                n_jobs=n_jobs,
                show_progress=True,
                on_errors=on_errors,
                **chunk_kwargs,
            )

    if not chunks:
        typer.echo(
            "Warning: No chunks were generated. "
            "This might be because the input was empty or did not contain any processable content.",
            err=True,
        )
        raise typer.Exit(code=0)

    if destination:
        _write_chunks(chunks, destination, metadata)
    else:
        _print_chunks(chunks, destination, metadata)


@app.command(
    name="visualize",
    help="Start the web-based chunk visualizer interface for interactive text and code chunking.",
)
def visualize_command(
    host: str = typer.Option(
        "127.0.0.1",
        "--host",
        help="Host IP to bind the visualizer server. (default: 127.0.0.1)",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port number to run the visualizer server. (default: 8000)",
    ),
    tokenizer_command: Optional[str] = typer.Option(
        None,
        "--tokenizer-command",
        help=(
            "A shell command to use for token counting in the visualizer. "
            "The command should take text as stdin and output the token count as a number."
        ),
    ),
    headless: bool = typer.Option(
        False,
        "--headless",
        help="Run visualizer in headless mode (don't open browser automatically).",
    ),
):
    """
    Start the web-based chunk visualizer interface for interactive text and code chunking.
    """
    if Visualizer is None:
        typer.echo(
            "Error: Visualization dependencies not available.\n"
            "Please install with: pip install chunklet-py[visualization]",
            err=True,
        )
        raise typer.Exit(code=1)

    # Check if port is available
    url = f"http://{host}:{port}"
    if not _check_port_available(host, port):
        typer.echo(f"Error: Port {port} is already in use on {host}", err=True)
        typer.echo("Options:", err=True)
        typer.echo(f"  1. Stop the process currently occupying {url}", err=True)
        typer.echo(
            "  2. Use a different port: chunklet visualize --port <different_port>",
            err=True,
        )
        typer.echo(
            "  3. Find the PID:\n"
            f"     - Linux: 'ss -tunlp | grep :{port}' or 'fuser {port}/tcp'\n"
            f"     - Windows: 'netstat -ano | findstr :{port}'\n"
            f"     - Mac: 'lsof -i :{port}'",
            err=True,
        )
        raise typer.Exit(code=1)

    # Create token counter if tokenizer command provided
    token_counter = None
    if tokenizer_command:
        token_counter = _create_external_tokenizer(tokenizer_command)

    # Start the visualizer
    visualizer = Visualizer(host=host, port=port, token_counter=token_counter)

    typer.echo("Starting Chunklet Visualizer...")
    typer.echo(f"URL: {url}")
    typer.echo("Press Ctrl+C to stop the server")

    if not headless:
        import webbrowser

        try:
            webbrowser.open(url)
            typer.echo("Opened in default browser")
        except Exception as e:
            typer.echo(f"Could not open browser: {e}", err=True)

    try:
        visualizer.serve()
    except KeyboardInterrupt:
        typer.echo("\nVisualizer stopped.")
    except Exception as e:
        typer.echo(f"Error starting visualizer: {e}", err=True)
        raise typer.Exit(code=1)


@app.callback(invoke_without_command=True)
def main_callback(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", help="Show program's version number and exit."
    )
):
    if version:
        typer.echo(f"chunklet v{__version__}")
        raise typer.Exit()


if __name__ == "__main__":
    app()
