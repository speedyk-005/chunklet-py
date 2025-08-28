import argparse
import textwrap
import sys
import subprocess
import os
import glob
import warnings
from importlib.metadata import version, PackageNotFoundError # New import
from .core import Chunklet

try:
    __version__ = version("chunklet")
except PackageNotFoundError:
    __version__ = "unknown"

def create_external_tokenizer(command):
    def external_tokenizer(text):
        try:
            process = subprocess.run(
                command,
                shell=True,
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
    warnings.simplefilter('default', DeprecationWarning) # Add this line
    parser = argparse.ArgumentParser(
        description="Chunklet: Smart Multilingual Text Chunker for LLMs, RAG, and beyond.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # New argument for version
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s v{__version__}",
        help="Show program's version number and exit."
    )

    parser.add_argument(
        "text",
        nargs="?",
        help="The input text to chunk. If not provided, --file or --input-file must be used.",
    )
    parser.add_argument(
        "--file", "--input-file", # Added --input-file as an alias
        help="Path to a text file to read input from. Overrides the 'text' argument.",
    )
    parser.add_argument(
        "--output-file",
        help="Path to a file to write the output chunks to. If not provided, output is printed to stdout.",
    )
    parser.add_argument(
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
        help="Maximum number of tokens per chunk. (default: 512)",
    )
    parser.add_argument(
        "--max-sentences",
        type=int,
        default=100,
        help="Maximum number of sentences per chunk. (default: 100)",
    )
    parser.add_argument(
        "--overlap-percent",
        type=float,
        default=10,
        help="Percentage of overlap between chunks (0-85). (default: 10)",
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
        "--batch",
        action="store_true",
        help="Process input as a list of texts for batch chunking (requires --file with one text per line).",
    )
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

    args = parser.parse_args()

    # Check if any input argument is provided
    if sum([bool(args.text), bool(args.file), bool(args.input_dir)]) == 0:
        print("Error: No input provided. Please specify text, a file, or an input directory.", file=sys.stderr)
        print("See 'chunklet -h' for usage examples.", file=sys.stderr)
        sys.exit(1) # Exit with an error code

    # Existing validation for exactly one input argument
    if sum([bool(args.text), bool(args.file), bool(args.input_dir)]) != 1:
        parser.error("Exactly one of 'text' argument, '--file', or '--input-dir' must be provided.")
    if args.output_file and args.output_dir:
        parser.error("Only one of '--output-file' or '--output-dir' can be specified.")
    if args.batch and not (args.file or args.input_dir):
        parser.error("Batch mode (--batch) requires input from '--file' or '--input-dir'.")

    source_texts = []
    is_batch = args.batch

    if args.input_dir:
        if not os.path.isdir(args.input_dir):
            parser.error(f"Input directory not found: {args.input_dir}")
        is_batch = True
        # Use glob to find all .txt and .md files recursively
        file_paths = glob.glob(os.path.join(args.input_dir, "**/*.txt"), recursive=True)
        file_paths.extend(glob.glob(os.path.join(args.input_dir, "**/*.md"), recursive=True))
        
        for file_path in file_paths:
            with open(file_path, "r", encoding="utf-8") as f:
                source_texts.append((file_path, f.read()))

    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            if args.batch:
                warnings.warn(
                    "Using --batch with --file is deprecated. "
                    "Please use --input-dir for batch processing multiple files, "
                    "or provide a single text directly for single file chunking.",
                    DeprecationWarning
                )
                lines = [line.strip() for line in f if line.strip()]
                for i, line in enumerate(lines):
                    source_texts.append((f"{args.file}_line_{i+1}", line))
            else:
                source_texts.append((args.file, f.read()))
    elif args.text:
        source_texts.append(("stdin", args.text))

    if not source_texts:
        print("No input texts found to process.", file=sys.stderr)
        sys.exit(0)

    token_counter = None
    if args.tokenizer_command:
        token_counter = create_external_tokenizer(args.tokenizer_command)

    chunker = Chunklet(
        verbose=args.verbose,
        use_cache=not args.no_cache,
        token_counter=token_counter,
    )

    input_texts_only = [text for _, text in source_texts]

    results = []
    if is_batch:
        results = chunker.batch_chunk(
            texts=input_texts_only,
            lang=args.lang,
            mode=args.mode,
            max_tokens=args.max_tokens,
            max_sentences=args.max_sentences,
            overlap_percent=args.overlap_percent,
            offset=args.offset,
            n_jobs=args.n_jobs,
        )
    else:
        # For single text, chunk returns a list of strings
        results = [
            chunker.chunk(
                text=input_texts_only[0],
                lang=args.lang,
                mode=args.mode,
                max_tokens=args.max_tokens,
                max_sentences=args.max_sentences,
                overlap_percent=args.overlap_percent,
                offset=args.offset,
            )
        ]  # Wrap in a list to match batch output structure for consistent printing

    if args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)
        total_chunks_written = 0
        for (source_path, _), doc_chunks in zip(source_texts, results):
            base_name, _ = os.path.splitext(os.path.basename(source_path))
            for j, chunk in enumerate(doc_chunks):
                output_filename = f"{base_name}_chunk_{j+1}.txt"
                output_path = os.path.join(args.output_dir, output_filename)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(chunk + "\n")
                total_chunks_written += 1
        print(f"Successfully processed {len(source_texts)} file(s) and wrote {total_chunks_written} chunk file(s) to {args.output_dir}")
    else:
        output_content = []
        for (source_name, _), doc_chunks in zip(source_texts, results):
            if is_batch:
                output_content.append(f"## Source: {source_name}")
                output_content.append("")
            for j, chunk in enumerate(doc_chunks):
                output_content.append(f"--- Chunk {j+1} ---")
                output_content.append(chunk)
                output_content.append("")

        output_str = "\n".join(output_content)

        if args.output_file:
            with open(args.output_file, "w", encoding="utf-8") as f:
                f.write(output_str)
        else:
            print(output_str)