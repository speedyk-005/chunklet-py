import argparse
import textwrap
import sys
import subprocess
from .core import Chunklet


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
    parser = argparse.ArgumentParser(
        description="Chunklet: Smart Multilingual Text Chunker for LLMs, RAG, and beyond.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "text",
        nargs="?",
        help="The input text to chunk. If not provided, --file must be used.",
    )
    parser.add_argument(
        "--file",
        help="Path to a text file to read input from. Overrides the 'text' argument.",
    )
    parser.add_argument(
        "--output-file",
        help="Path to a file to write the output chunks to. If not provided, output is printed to stdout.",
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

    if not args.text and not args.file:
        parser.error("Either 'text' argument or '--file' must be provided.")
    if args.batch and not args.file:
        parser.error("Batch mode (--batch) requires input from a file (--file).")

    input_texts = []
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            if args.batch:
                input_texts = [line.strip() for line in f if line.strip()]
            else:
                input_texts = [f.read()]
    elif args.text:
        input_texts = [args.text]

    token_counter = None
    if args.tokenizer_command:
        token_counter = create_external_tokenizer(args.tokenizer_command)

    chunker = Chunklet(
        verbose=args.verbose,
        use_cache=not args.no_cache,
        token_counter=token_counter,
    )

    results = []
    if args.batch:
        results = chunker.batch_chunk(
            texts=input_texts,
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
                text=input_texts[0],
                lang=args.lang,
                mode=args.mode,
                max_tokens=args.max_tokens,
                max_sentences=args.max_sentences,
                overlap_percent=args.overlap_percent,
                offset=args.offset,
            )
        ]  # Wrap in a list to match batch output structure for consistent printing

    output_content = []
    for i, doc_chunks in enumerate(results):
        if args.batch:
            output_content.append(f"## Document {i+1}")
        for j, chunk in enumerate(doc_chunks):
            output_content.append(f"--- Chunk {j+1} ---")
            output_content.append(chunk)
        output_content.append(
            ""
        )  # Add a newline between documents/single chunk outputs

    output_str = "
".join(output_content)

    if args.output_file:
        with open(args.output_file, "w", encoding="utf-8") as f:
            f.write(output_str)
    else:
        print(output_str)