import typer
from typing import Optional, List
import tempfile
from pathlib import Path
from enum import Enum
import sys
import subprocess
import shlex
from importlib.metadata import version, PackageNotFoundError
import json

from chunklet.plain_text_chunker import PlainTextChunker
from chunklet.document_chunker import DocumentChunker
from chunklet.experimental.code_chunker import CodeChunker

try:
    __version__ = version("chunklet")
except PackageNotFoundError:
    __version__ = "unknown"


# Define Enums for choices
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
    """
    Creates a tokenizer function from an external command string.

    Args:
        command_str (str): The command string to execute.

    Returns:
        A function that takes text as input and returns the token count.
    """
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
    # flags for chunker type
    doc: bool = typer.Option(
        False, "--doc", help="Use DocumentChunker for document files."
    ),
    directory: Optional[List[Path]] = typer.Option(
        None, "--dir", "-d", help="Path to one or more directories to read input files from."
    ),
    code: bool = typer.Option(
        False, "--code", "-c", help="Use CodeChunker for code files."
    ),
    
    text: Optional[str] = typer.Argument(
        None, help="The input text to chunk. If not provided, --file must be used."
    ),
    file: Optional[List[Path]] = typer.Option(
        None, "--file", "-f", "--input-file", help="Path to one or more files to read input from. Overrides the 'text' argument."
    ),

    output_file: Optional[Path] = typer.Option(
        None, "--output-file", help="Path to a file to write the output chunks to. If not provided, output is printed to stdout."
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "--output-dir", help="Path to a directory to write the output chunks to. A separate file will be created for each input file."
    ),
    mode: ChunkMode = typer.Option(
        ChunkMode.sentence, "--mode", help="Chunking mode: 'sentence', 'token', or 'hybrid'. (default: sentence)"
    ),
    lang: str = typer.Option(
        "auto", "--lang", help="Language of the text (e.g., 'en', 'fr', 'auto'). (default: auto)"
    ),
    max_tokens: int = typer.Option(
        256, "--max-tokens", help="Maximum number of tokens per chunk. (default: 256)"
    ),
    max_sentences: int = typer.Option(
        12, "--max-sentences", help="Maximum number of sentences per chunk. (default: 12)"
    ),
    overlap_percent: float = typer.Option(
        20.0, "--overlap-percent", help="Percentage of overlap between chunks (0-85). (default: 20)"
    ),
    offset: int = typer.Option(
        0, "--offset", help="Starting sentence offset for chunking. (default: 0)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging."
    ),
    n_jobs: Optional[int] = typer.Option(
        None, "--n-jobs", help="Number of parallel jobs for batch chunking. (default: None, uses all available cores)"
    ),
    tokenizer_command: Optional[str] = typer.Option(
        None, "--tokenizer-command", help="A shell command to use for token counting. The command should take text as stdin and output the token count as a number."
    ),
    on_errors: OnError = typer.Option(
        OnError.raise_, "--on-errors", help="How to handle errors during processing. (default: raise)"
    ),
    metadata: bool = typer.Option(
        False, "--metadata", help="Include metadata in the output."
    ),
    
    # CodeChunker specific arguments
    docstring_mode: DocstringMode = typer.Option(
        DocstringMode.summary, "--docstring-mode", help="Docstring processing strategy for CodeChunker: 'summary', 'all', or 'excluded'."
    ),
    strict_mode: bool = typer.Option(
        True, "--strict-mode", help="If True, raise error when structural blocks exceed max_tokens in CodeChunker. If False, split oversized blocks."
    ),
    include_comments: bool = typer.Option(
        True, "--include-comments", help="Include comments in output chunks for CodeChunker."
    ),
):
    """
    Chunk text or files based on specified parameters.
    """
    # --- Input validation logic ---
    input_sources = [
        text,
        file,
        directory,
    ]
    provided_inputs = [arg for arg in input_sources if arg]

    if len(provided_inputs) == 0:
        typer.echo(
            "Error: No input provided. Please provide a text, or use the --file or --dir option.",
            err=True,
        )
        typer.echo(
            "💡 Hint: Use 'chunklet --help' for more information and usage examples.",
            err=True,
        )
        raise typer.Exit(code=1)

    if len(provided_inputs) > 1:
        typer.echo(
            "Error: Please provide either a text string, or use the --file or --dir option, but not more than one.",
            err=True,
        )
        typer.echo(
            "💡 Hint: Use 'chunklet --help' for more information and usage examples.",
            err=True,
        )
        raise typer.Exit(code=1)

    if output_file and output_dir:
        typer.echo(
            "Error: Please specify either '--output-file' or '--output-dir', but not both.",
            err=True,
        )
        typer.echo(
            "💡 Hint: Use '--output-file' for a single input and '--output-dir' for multiple inputs.",
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
        chunk_kwargs.update({
            "docstring_mode": docstring_mode,
            "strict_mode": strict_mode,
            "include_comments": include_comments,
        })
    else:
        chunker_instance = DocumentChunker(
            verbose=verbose,
            token_counter=token_counter,
        )
        chunk_kwargs.update({
            "lang": lang,
            "mode": mode,
            "max_sentences": max_sentences,
            "overlap_percent": overlap_percent,
            "offset": offset,
        })

    # --- Chunking logic ---
    if text:
        with tempfile.NamedTemporaryFile(mode="w", delete=True, suffix=".txt", encoding="utf-8") as temp_file:
            temp_file.write(text)
            temp_file.flush()
            temp_path = Path(temp_file.name)
            chunks = chunker_instance.chunk(
                path=temp_path,
                **chunk_kwargs,
            )
        all_results.append(chunks)

    elif file:
        processed_files = list(file)

        if len(processed_files) == 1:
            single_file = processed_files[0]
            if single_file.suffix.lower() == ".pdf":
                all_results_gen = chunker_instance.chunk_pdfs(
                    paths=[single_file],
                    show_progress=False, # No progress bar for single file
                    on_errors=on_errors,
                    **chunk_kwargs,
                )
                all_results.append(all_results_gen)
            else:
                chunks = chunker_instance.chunk(
                    path=single_file,
                    **chunk_kwargs,
                )
                all_results.append(chunks)
        else:
            all_results_gen = chunker_instance.batch_chunk(
                paths=processed_files,
                n_jobs=n_jobs,
                show_progress=True, # Typer can handle progress bars
                on_errors=on_errors,
                **chunk_kwargs, # Pass chunk_kwargs
            )
            all_results.append(all_results_gen) # Consume generator

    elif directory:
        file_paths = []
        for d_path in directory:
            if d_path.is_dir():
                file_paths.extend(
                    [p for p in d_path.glob("**/*") if p.is_file()]
                )
            else:
                typer.echo(f"Warning: '{d_path}' is not a directory. Skipping.", err=True)

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
            "Warning: No chunks were generated. This might be because the input was empty or did not contain any processable content.",
            err=True,
        )
        raise typer.Exit(code=0)

    # --- Output handling ---
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        total_chunks_written = 0
        processed_sources = set()
        for res in all_results: # res can be list[Box] or Generator[Box, None, None]
            for chunk_box in res:
                source_name = chunk_box.metadata["source"]
                base_name = Path(source_name).stem # Use Path.stem directly
            
                base_output_filename = f"{base_name}_chunk_{chunk_box.metadata['chunk_num']}" # Use chunk_num from metadata
            
                # Write content file
                output_txt_path = output_dir / f"{base_output_filename}.txt"
                output_json_path = output_dir / f"{base_output_filename}.json"
                with open(output_txt_path, "w", encoding="utf-8") as f:
                    f.write(chunk_box.content + "\n")
            total_chunks_written += 1

            # Write metadata file if requested
            if metadata: # Only write metadata if requested
                output_json_path = output_dir / f"{base_output_filename}.json"
                with open(output_json_path, "w", encoding="utf-8") as f:
                    json.dump(chunk_box.metadata.to_dict(), f, indent=4)
            processed_sources.add(source_name)
        message = f"Successfully processed {len(processed_sources)} input(s) and wrote {total_chunks_written} chunk file(s) to {output_dir}"
        if metadata:
            message += " (with .json metadata files)."
        else:
            message += "."
        typer.echo(message)
    else:
        output_content = []
        
        # Iterate through all chunks directly
        chunk_counter = 0
        for res in all_results: # res can be list[Box] or Generator[Box, None, None]
            for chunk_box in res:
                chunk_counter += 1
                output_content.append(f"## Source: {chunk_box.metadata['source']}")
                output_content.append(f"--- Chunk {chunk_counter} ---")
                output_content.append(chunk_box.content)
                if (
                    metadata
                    and hasattr(chunk_box, "metadata")
                    and chunk_box.metadata
                ):
                    output_content.append(f"Metadata: {chunk_box.metadata.to_dict()}")
                output_content.append("")

        output_str = "\n".join(output_content)

        if output_file:
            output_file.write_text(output_str, encoding="utf-8")
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
