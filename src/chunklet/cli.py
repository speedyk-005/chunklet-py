import argparse
import sys
import subprocess
import os
import glob
import warnings
import shlex
from importlib.metadata import version, PackageNotFoundError
from chunklet.plain_text_chunker import PlainTextChunker
from chunklet.document_chunker import DocumentChunker

try:
    __version__ = version("chunklet")
except PackageNotFoundError:
    __version__ = "unknown"


def create_external_tokenizer(command_str):
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


def main():
    """The main entry point for the Chunklet CLI."""
    warnings.simplefilter("default", DeprecationWarning)
    parser = argparse.ArgumentParser(
        description="Chunklet: Smart Multilingual Text Chunker for LLMs, RAG, and beyond.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s v{__version__}",
        help="Show program's version number and exit.",
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="The input text to chunk. If not provided, --file or --input-file must be used.",
    )
    parser.add_argument(
        "-f",
        "--file",
        "--input-file",
        help="Path to a file to read input from. Overrides the 'text' argument.",
    )
    parser.add_argument(
        "--input-files",
        nargs="+",
        help="A list of paths to input files.",
    )
    parser.add_argument(
        "--output-file",
        help="Path to a file to write the output chunks to. If not provided, output is printed to stdout.",
    )
    parser.add_argument(
        "-d",
        "--input-dir",
        help="Path to a directory to read input files from (e.g., *.txt, *.md).",
    )
    parser.add_argument(
        "--output-dir",
        help="Path to a directory to write the output chunks to. A separate file will be created for each input file.",
    )
    parser.add_argument(
        "--mode",
        choices=["sentence", "token", "hybrid"],
        default="sentence",
        help="Chunking mode: 'sentence', 'token', or 'hybrid'. (default: sentence)",
    )
    parser.add_argument(
        "--lang",
        default="auto",
        help="Language of the text (e.g., 'en', 'fr', 'auto'). (default: auto)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=512,
        help="Maximum number of tokens per chunk. (default: 256)",
    )
    parser.add_argument(
        "--max-sentences",
        type=int,
        default=100,
        help="Maximum number of sentences per chunk. (default: 12)",
    )
    parser.add_argument(
        "--overlap-percent",
        type=float,
        default=10,
        help="Percentage of overlap between chunks (0-85). (default: 20)",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Starting sentence offset for chunking. (default: 0)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging."
    )
    parser.add_argument("--no-cache", action="store_true", help="Disable LRU caching.")
    parser.add_argument(
        "--n-jobs",
        type=int,
        default=None,
        help="Number of parallel jobs for batch chunking. (default: None, uses all available cores)",
    )
    parser.add_argument(
        "--tokenizer-command",
        type=str,
        default=None,
        help="A shell command to use for token counting. The command should take text as stdin and output the token count as a number.",
    )
    parser.add_argument(
        "--metadata", action="store_true", help="Include metadata in the output."
    )

    args = parser.parse_args()

    if (
        sum(
            [
                bool(args.text),
                bool(args.file),
                bool(args.input_dir),
                bool(args.input_files),
            ]
        )
        == 0
    ):
        print(
            "Error: No input provided. Please specify text, a file, or an input directory.",
            file=sys.stderr,
        )
        print("See 'chunklet -h' for usage examples.", file=sys.stderr)
        sys.exit(1)

    if (
        sum(
            [
                bool(args.text),
                bool(args.file),
                bool(args.input_dir),
                bool(args.input_files),
            ]
        )
        != 1
    ):
        parser.error(
            "Exactly one of 'text' argument, '--file', or '--input-dir' must be provided."
        )
    if args.output_file and args.output_dir:
        parser.error("Only one of '--output-file' or '--output-dir' can be specified.")

    token_counter = None
    if args.tokenizer_command:
        token_counter = create_external_tokenizer(args.tokenizer_command)

    plain_text_chunker_instance = PlainTextChunker(
        verbose=args.verbose,
        use_cache=not args.no_cache,
        token_counter=token_counter,
    )
    document_chunker = DocumentChunker(plain_text_chunker_instance)

    all_results = []
    source_info = []

    if args.text:
        chunks = plain_text_chunker_instance.chunk(
            text=args.text,
            lang=args.lang,
            mode=args.mode,
            max_tokens=args.max_tokens,
            max_sentences=args.max_sentences,
            overlap_percent=args.overlap_percent,
            offset=args.offset,
        )
        all_results.append(chunks)
        source_info.append(("stdin", None))

    elif args.input_files:
        for file_path in args.input_files:
            if not os.path.isfile(file_path):
                parser.error(f"File not found: {file_path}")

        all_results = document_chunker.bulk_chunk(
            paths=args.input_files,
            lang=args.lang,
            mode=args.mode,
            max_tokens=args.max_tokens,
            max_sentences=args.max_sentences,
            overlap_percent=args.overlap_percent,
            offset=args.offset,
            n_jobs=args.n_jobs,
        )
        source_info.extend([(os.path.basename(p), p) for p in args.input_files])

    elif args.input_dir:
        if not os.path.isdir(args.input_dir):
            parser.error(f"Input directory not found: {args.input_dir}")

        file_paths = []
        for ext in document_chunker.GENERAL_TEXT_EXTENSIONS:
            file_paths.extend(
                glob.glob(os.path.join(args.input_dir, f"**/*{ext}"), recursive=True)
            )

        file_paths = sorted([p for p in file_paths if os.path.isfile(p)])

        if not file_paths:
            print(
                f"No supported files found in directory: {args.input_dir}",
                file=sys.stderr,
            )
            sys.exit(0)

        all_results = document_chunker.bulk_chunk(
            paths=file_paths,
            lang=args.lang,
            mode=args.mode,
            max_tokens=args.max_tokens,
            max_sentences=args.max_sentences,
            overlap_percent=args.overlap_percent,
            offset=args.offset,
            n_jobs=args.n_jobs,
        )
        source_info.extend([(os.path.basename(p), p) for p in file_paths])

    elif args.input_dir:
        if not os.path.isdir(args.input_dir):
            parser.error(f"Input directory not found: {args.input_dir}")

        file_paths = []
        for ext in document_chunker.GENERAL_TEXT_EXTENSIONS:
            file_paths.extend(
                glob.glob(os.path.join(args.input_dir, f"**/*{ext}"), recursive=True)
            )

        file_paths = sorted([p for p in file_paths if os.path.isfile(p)])

        if not file_paths:
            print(
                f"No supported files found in directory: {args.input_dir}",
                file=sys.stderr,
            )
            sys.exit(0)

        all_results = document_chunker.bulk_chunk(
            paths=file_paths,
            lang=args.lang,
            mode=args.mode,
            max_tokens=args.max_tokens,
            max_sentences=args.max_sentences,
            overlap_percent=args.overlap_percent,
            offset=args.offset,
            n_jobs=args.n_jobs,
        )
        source_info.extend([(os.path.basename(p), p) for p in file_paths])

    elif args.file:
        if not os.path.isfile(args.file):
            parser.error(f"File not found: {args.file}")

        chunks = document_chunker.chunk(
            path=args.file,
            lang=args.lang,
            mode=args.mode,
            max_tokens=args.max_tokens,
            max_sentences=args.max_sentences,
            overlap_percent=args.overlap_percent,
            offset=args.offset,
            n_jobs=args.n_jobs,
        )
        for chunk_box in chunks:
            chunk_box.metadata.source = os.path.basename(args.file)
        all_results.append(chunks)
        source_info.append((os.path.basename(args.file), args.file))

    if not all_results:
        print("No chunks generated.", file=sys.stderr)
        sys.exit(0)

    if args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)
        total_chunks_written = 0
        for (source_name, original_path), doc_chunks in zip(source_info, all_results):
            base_name = (
                os.path.splitext(source_name)[0] if original_path else source_name
            )

            for j, chunk_box in enumerate(doc_chunks):
                output_filename = f"{base_name}_chunk_{j+1}.txt"
                output_path = os.path.join(args.output_dir, output_filename)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(chunk_box.content + "\n")
                total_chunks_written += 1
        print(
            f"Successfully processed {len(source_info)} input(s) and wrote {total_chunks_written} chunk file(s) to {args.output_dir}"
        )
    else:
        output_content = []
        for (source_name, _), doc_chunks in zip(source_info, all_results):
            if len(source_info) > 1 or source_name != "stdin":
                output_content.append(f"## Source: {source_name}")
                output_content.append("")
            for j, chunk_box in enumerate(doc_chunks):
                output_content.append(f"--- Chunk {j+1} ---")
                output_content.append(chunk_box.content)
                if args.metadata and hasattr(chunk_box, 'metadata') and chunk_box.metadata:
                    output_content.append(f"Metadata: {chunk_box.metadata.to_dict()}")
                output_content.append("")

        output_str = "\n".join(output_content)

        if args.output_file:
            with open(args.output_file, "w", encoding="utf-8") as f:
                f.write(output_str)
        else:
            print(output_str)

    elif args.file:
        if not os.path.isfile(args.file):
            parser.error(f"File not found: {args.file}")

        chunks = document_chunker.chunk(
            path=args.file,
            lang=args.lang,
            mode=args.mode,
            max_tokens=args.max_tokens,
            max_sentences=args.max_sentences,
            overlap_percent=args.overlap_percent,
            offset=args.offset,
            n_jobs=args.n_jobs,
        )
        for chunk_box in chunks:
            chunk_box.metadata.source = os.path.basename(args.file)
        all_results.append(chunks)
        source_info.append((os.path.basename(args.file), args.file))

    if not all_results:
        print("No chunks generated.", file=sys.stderr)
        sys.exit(0)

    if args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)
        total_chunks_written = 0
        for (source_name, original_path), doc_chunks in zip(source_info, all_results):
            base_name = (
                os.path.splitext(source_name)[0] if original_path else source_name
            )

            for j, chunk_box in enumerate(doc_chunks):
                output_filename = f"{base_name}_chunk_{j+1}.txt"
                output_path = os.path.join(args.output_dir, output_filename)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(chunk_box.content + "\n")
                total_chunks_written += 1
        print(
            f"Successfully processed {len(source_info)} input(s) and wrote {total_chunks_written} chunk file(s) to {args.output_dir}"
        )
    else:
        output_content = []
        for (source_name, _), doc_chunks in zip(source_info, all_results):
            if len(source_info) > 1 or source_name != "stdin":
                output_content.append(f"## Source: {source_name}")
                output_content.append("")
            for j, chunk_box in enumerate(doc_chunks):
                output_content.append(f"--- Chunk {j+1} ---")
                output_content.append(chunk_box.content)
                if args.metadata and hasattr(chunk_box, 'metadata') and chunk_box.metadata:
                    output_content.append(f"Metadata: {chunk_box.metadata.to_dict()}")
                output_content.append("")

        output_str = "\n".join(output_content)

        if args.output_file:
            with open(args.output_file, "w", encoding="utf-8") as f:
                f.write(output_str)
        else:
            print(output_str)


if __name__ == "__main__":
    main()
