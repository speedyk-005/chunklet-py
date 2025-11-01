import sys
import typer
from typing import Optional, List
from pathlib import Path
from enum import Enum
import subprocess
import shlex
from importlib.metadata import version, PackageNotFoundError
import json

from chunklet.plain_text_chunker import PlainTextChunker
from chunklet.document_chunker import DocumentChunker
from chunklet.experimental.code_chunker import CodeChunker
from chunklet.experimental.code_chunker.helpers import is_path_like

try:
    __version__ = version("chunklet")
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
    all = "all"
    excluded = "excluded"


app = typer.Typer(
    name="chunklet",
    help="Chunklet: Smart Multilingual Text Chunker for LLMs, RAG, and beyond.",
    rich_help_panel=True,
)


def create_external_tokenizer(command_str: str):
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
    mode: ChunkMode = typer.Option(
        ChunkMode.sentence,
        "--mode",
        help="Chunking mode: 'sentence', 'token', or 'hybrid'. (default: sentence)",
    ),
    lang: str = typer.Option(
        "auto",
        "--lang",
        help="Language of the text (e.g., 'en', 'fr', 'auto'). (default: auto)",
    ),
    max_tokens: int = typer.Option(
        256, "--max-tokens", help="Maximum number of tokens per chunk. (default: 256)"
    ),
    max_sentences: int = typer.Option(
        12,
        "--max-sentences",
        help="Maximum number of sentences per chunk. (default: 12)",
    ),
    overlap_percent: float = typer.Option(
        20.0,
        "--overlap-percent",
        help="Percentage of overlap between chunks (0-85). (default: 20)",
    ),
    offset: int = typer.Option(
        0, "--offset", help="Starting sentence offset for chunking. (default: 0)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging."
    ),
    tokenizer_command: Optional[str] = typer.Option(
        None,
        "--tokenizer-command",
        help="A shell command to use for token counting. The command should take text as stdin and output the token count as a number.",
    ),
    metadata: bool = typer.Option(
        False, "--metadata", help="Include metadata in the output."
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
        help="How to handle errors during processing. (default: raise)",
    ),
    # CodeChunker specific arguments
    docstring_mode: DocstringMode = typer.Option(
        DocstringMode.summary,
        "--docstring-mode",
        help="Docstring processing strategy for CodeChunker: 'summary', 'all', or 'excluded'.",
    ),
    strict_mode: bool = typer.Option(
        True,
        "--strict-mode",
        help="If True, raise error when structural blocks exceed max_tokens in CodeChunker. If False, split oversized blocks.",
    ),
    include_comments: bool = typer.Option(
        True,
        "--include-comments",
        help="Include comments in output chunks for CodeChunker.",
    ),
):
    """
    Chunk text or files based on specified parameters.
    """
    # --- Input validation logic ---
    provided_inputs = [arg for arg in [text, source] if arg]

    if len(provided_inputs) == 0:
        typer.echo(
            "Error: No input provided. Please provide a text, or use the --source option.",
            err=True,
        )
        typer.echo(
            "💡 Hint: Use 'chunklet --help' for more information and usage examples.",
            err=True,
        )
        raise typer.Exit(code=1)

    if len(provided_inputs) > 1:
        typer.echo(
            "Error: Please provide either a text string, or use the --source option, but not both.",
            err=True,
        )
        typer.echo(
            "💡 Hint: Use 'chunklet --help' for more information and usage examples.",
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
        token_counter = create_external_tokenizer(tokenizer_command)

    all_results = []

    # Construct chunk_kwargs dynamically
    chunk_kwargs = {
        "max_tokens": max_tokens,
        "token_counter": token_counter,
    }

    if code:
        chunker_instance = CodeChunker(
            verbose=verbose,
            token_counter=token_counter,
        )
        chunk_kwargs.update(
            {
                "docstring_mode": docstring_mode,
                "strict_mode": strict_mode,
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
            chunker_instance = DocumentChunker(
                verbose=verbose,
                token_counter=token_counter,
            )
        chunk_kwargs.update(
            {
                "lang": lang,
                "mode": mode,
                "max_sentences": max_sentences,
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
        all_results.append(chunks)

    elif source:
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
                    f"Warning: '{s_path}' does not resemble a valid file system path "
                    "(failed heuristic check). Skipping.",
                    err=True,
                )

        if not file_paths:
            typer.echo(
                "Warning: No processable files found in the specified source(s). Exiting.",
                err=True,
            )
            raise typer.Exit(code=0)

        if not len(file_paths) == 1:
            # Single file input logic
            single_file = file_paths[0]
            chunks = chunker_instance.chunk(
                path=single_file,
                **chunk_kwargs,
            )
            all_results.append(chunks)
        else:
            # Batch input logic
            all_results_gen = chunker_instance.batch_chunk(
                paths=file_paths,
                n_jobs=n_jobs,
                show_progress=True,
                on_errors=on_errors,
                **chunk_kwargs,
            )
            all_results.append(all_results_gen)

    if not all_results:
        typer.echo(
            "Warning: No chunks were generated. "
            "This might be because the input was empty or did not contain any processable content.",
            err=True,
        )
        raise typer.Exit(code=0)

    # --- Output handling ---

    # Check for conflict: multi-input requires directory destination
    if destination and is_multi_output_mode and destination.is_file():
        typer.echo(
            "Error: When processing multiple inputs, '--destination' must be a directory, not a file.",
            err=True,
        )
        raise typer.Exit(code=1)

    if destination and is_multi_output_mode:
        # This is the equivalent of the old `if output_dir:` block
        destination.mkdir(parents=True, exist_ok=True)
        total_chunks_written = 0
        processed_sources = set()

        for res in all_results:
            for chunk_box in res:
                source_name = chunk_box.metadata["source"]
                base_name = Path(source_name).stem

                base_output_filename = (
                    f"{base_name}_chunk_{chunk_box.metadata['chunk_num']}"
                )

                # Write content file
                output_txt_path = destination / f"{base_output_filename}.txt"
                with open(output_txt_path, "w", encoding="utf-8") as f:
                    f.write(chunk_box.content + "\n")

                total_chunks_written += 1

                # Write metadata file if requested
                if metadata:
                    output_json_path = destination / f"{base_output_filename}.json"
                    with open(output_json_path, "w", encoding="utf-8") as f:
                        # Ensures metadata is a standard dict before dumping
                        data_to_dump = (
                            chunk_box.metadata.to_dict()
                            if hasattr(chunk_box.metadata, "to_dict")
                            else dict(chunk_box.metadata)
                        )
                        json.dump(data_to_dump, f, indent=4)

                processed_sources.add(source_name)

        message = (
            f"Successfully processed {len(processed_sources)} input(s)"
            f"and wrote {total_chunks_written} chunk file(s) to {destination}"
        )
        if metadata:
            message += " (with .json metadata files)."
        else:
            message += "."
        typer.echo(message)

    else:
        # This is the equivalent of the old `else:` block (stdout or single output_file)
        output_content = []

        chunk_counter = 0
        for res in all_results:
            for chunk_box in res:
                chunk_counter += 1
                output_content.append(f"## Source: {chunk_box.metadata.get('source', 'stdin')}")
                output_content.append(f"--- Chunk {chunk_counter} ---")
                output_content.append(chunk_box.content)
                output_content.append("")
                if metadata:
                    chunk_metadata = chunk_box.metadata.to_dict()
                    chunk_metadata.pop("source", None)   # Prevent printing the source path again
                    output_content.append("\n### Chunk Metadata") # Use a sub-header
                    
                    for key, value in chunk_metadata.items():
                        # Use clean pipe formatting for terminal style tables
                        output_content.append(f"| {key}: {value}")
                        
                    output_content.append("\n")

        output_str = "\n".join(output_content)

        if destination:
            destination.write_text(output_str, encoding="utf-8")
        else:
            typer.echo(output_str)


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False, "--version", "-v", help="Show program's version number and exit."
    )
):
    if version:
        typer.echo(f"chunklet v{__version__}")
        raise typer.Exit()


if __name__ == "__main__":
    app()
