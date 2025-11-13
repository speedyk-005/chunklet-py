# Chunklet Command Line Interface (CLI)

The chunklet CLI is your single gateway to all chunking and splitting functionalities. It provides two main commands: split for simple sentence segmentation and chunk for sophisticated, configuration-driven chunking across text, documents, and code.

You can always check the installed version or get help using the main callbacks:

```bash
chunklet --version
chunklet --help
```


## The split Command: Sentence Segmentation

The split command is for precision text segmentation, breaking down text into individual sentences. This command exclusively uses the internal SentenceSplitter utility.

### What You Need to Know First

This command operates only on a raw text string or a single file (--source).

Sentences are output separated by newline characters.

| Flag | Description | Default |
|---|---|---|
| `<TEXT>` | The input text to split. | None |
| `--source, -s <PATH>` | Path to a single file to read input from. | None |
| `--destination, -d <PATH>` | Path to a single file to write the segmented sentences. | STDOUT |
| `--lang` | Language of the text (e.g., 'en', 'fr', 'auto'). | auto |

### Scenario 1: Splitting Text Directly on the Command Line

```bash
chunklet split "This is the first sentence. Here is the second sentence, in French. C'est la vie!" --lang auto
```


### Scenario 2: Splitting a File and Saving the Output

```bash
chunklet split --source document.txt --destination sentences.txt --lang en
```


## Plain Text Chunking: General Text Segmentation

This is the default mode for the chunk command. It utilizes the PlainTextChunker to create context-aware chunks based on length limits. This mode is active when neither the --doc nor the --code flags are provided.

### Key Flags for Plain Text

| Flag | Description | Default |
|---|---|---|
| `--mode` | The chunking strategy: sentence (groups by count), token (limits by size), or hybrid (respects both limits). | sentence |
| `--max-sentences` | Maximum number of sentences per chunk. | 12 |
| `--max-tokens` | Maximum number of tokens per chunk. | 256 |
| `--overlap-percent` | Percentage of overlap between chunks (0-85). | 20.0 |

### Scenario 1: Token-Based Chunking with a Custom Tokenizer

Chunk a file into segments of at most 128 tokens using a custom external shell command for token counting, and include the chunk metadata in the output.

```bash
# This example uses a hypothetical external script called 'my-tokenizer'
chunklet chunk \
  --source long_article.txt \
  --mode token \
  --max-tokens 128 \
  --tokenizer-command "my-tokenizer" \
  --metadata
```


### Scenario 2: Hybrid Chunking from a Text String

Chunk a long text string using the hybrid mode, respecting a limit of 3 sentences OR 20 tokens.

```bash
chunklet chunk "The quick brown fox jumps over the lazy dog. This is the first sentence. The second sentence is a bit longer. And this is the third one. Finally, the fourth sentence concludes our example. The last sentence is here to finish the text." \
  --mode hybrid \
  --max-sentences 3 \
  --max-tokens 20
```


## Document Chunking: Multi-Format File Processing

The DocumentChunker is an orchestrator for diverse document types like PDFs, DOCX, and EPUBs. It extracts raw text and then applies the Plain Text Chunker logic. This mode is activated with the --doc flag.

### Key Flags for Document Chunking

Requires: The --doc flag and the --source, -s argument (path to file(s) or directory).

When batch processing multiple files, the --destination must be a directory.

| Flag | Description | Default |
|---|---|---|
| `--doc` | Activate Document Chunker. | False |
| `--destination, -d <PATH>` | Output chunks into a directory (recommended for batch). | STDOUT |
| `--n-jobs` | Number of parallel jobs for concurrent file processing. | None (all cores) |
| `--on-errors` | How to handle errors: raise, skip, or break. | raise |

### Scenario 1: Processing a Documentation Directory in Parallel

Process all supported documents within a directory, segmenting them, and saving the output to a new directory using 4 parallel processes, skipping any files that cause an error.

```bash
chunklet chunk \
  --doc \
  --source /path/to/my/docs \
  --destination ./processed_chunks \
  --n-jobs 4 \
  --on-errors skip \
  --max-tokens 1024
```


### Scenario 2: Process a Single DOCX File with Clause Overlap

Process a single DOCX file, chunking it using the hybrid mode with a 25% overlap.

```bash
chunklet chunk --doc --source corporate_memo.docx \
  --mode hybrid \
  --max-sentences 5 \
  --max-tokens 256 \
  --overlap-percent 25
```


## Code Chunking: Structurally-Aware Code Segmentation

The CodeChunker is a language-agnostic tool for breaking source code into semantically meaningful blocks like functions and classes. This mode is activated with the --code flag.

### Key Flags for Code Chunking

Requires: The --code flag.

Token-Only: This mode is token-based; --max-sentences and --overlap-percent are ignored.

| Flag | Description | Default |
|---|---|---|
| `--code` | Activate Code Chunker. | False |
| `--docstring-mode` | Docstring strategy: summary (first line), all, or excluded. | summary |
| `--strict` | If True, raise an error when structural blocks exceed --max-tokens. If False, split oversized blocks. | True |
| `--include-comments` | Include comments in output chunks. | True |

### Scenario 1: Cracking a Repository of Code (Batching)

Use the CodeChunker on the current directory, allow splitting of oversized code blocks, use 8 cores, and write the output to a new directory.

```bash
chunklet chunk \
  --code \
  --source . \
  --destination ./code_chunks \
  --max-tokens 512 \
  --n-jobs 8 \
  --strict False
```


### Scenario 2: Quick Code Review (Excluding Comments and Docstrings)

Process a single code file, but remove all comments and docstrings from the final chunks for a cleaner representation.

```bash
chunklet chunk --code --source cli.py \
  --docstring-mode excluded \
  --include-comments False
```


## 🛠️ Advanced System Hooks (Batching and Tokenization)

These flags are essential for scaling up your operation or integrating with external tools. They apply to the chunk command.

### System Hook Flags

| Flag | Description | Default |
|---|---|---|
| `--tokenizer-command` | A shell command string to use for token counting. It must take text via STDIN and output the integer count via STDOUT. | None |
| `--n-jobs` | Number of parallel processes to use during batch_chunk operations. | None (uses all available CPU cores) |
| `--on-errors` | Defines batch error handling: raise (stop), skip (ignore file, continue), or break (halt, return partial result). | raise |
| `--metadata` | Include rich metadata (source, span, chunk num, etc.) in the output. | False |
| `--verbose, -v` | Enable verbose logging for debugging or process detail. | False |

### Scenario: Using an External Python Script to Count Tokens

This allows you to align chunklet chunk sizes with your final LLM's token limits using an external tool.

Create your external script (e.g., my_tok_counter.py):

```python
# my_tok_counter.py
import sys
# Read text from stdin
text = sys.stdin.read()
# Replace with your actual token counting logic
token_count = len(text.split()) 
print(token_count) # Must print only the integer count
```

Run chunklet with the command:

```bash
# The argument to --tokenizer-command is the full shell command
chunklet chunk \
  --text "This is the text to chunk." \
  --max-tokens 5 \
  --tokenizer-command "python ./my_tok_counter.py"
```

This is how you perfectly align your `chunklet` chunk sizes with your final LLM's token limits, no matter what tool is counting them!

??? info "API Reference"
    For a deep dive into the `chunklet` CLI, its commands, and all the nitty-gritty details, check out the full [API documentation](../reference/chunklet/cli.md).