# Chunklet Command Line Interface (CLI): Your Chunking Powerhouse! 🚀

Meet `chunklet`, your versatile CLI companion for all things text processing! From precise sentence splitting and smart chunking of any content to interactive visualization in your browser - we've got the tools to make your LLM workflows flow effortlessly. Whether you're processing documents, code, or plain text, chunklet adapts to your needs with RAG-ready precision.

!!! info "`chunklet` vs `chunklet-py`"
    The CLI command is `chunklet` (kept for backward compatibility), while the Python package is named `chunklet-py` to avoid naming conflicts with other packages.

Before we dive into the fun stuff, you can always check your `chunklet` version or get a quick help guide.:

```bash
chunklet --version
chunklet --help
```

You can also get specific help for each command

```bash
chunklet split --help
chunklet chunk --help
chunklet visualize --help
```

---

## The `split` Command: Precision Sentence Segmentation ✂️

Need to break down text into individual sentences with surgical precision? The `split` command is your go-to! It leverages `chunklet`'s powerful [`SentenceSplitter`](programmatic/sentence_splitter.md) to give you clean, segmented sentences.

### Quick Facts for `split`

*   Operates on a raw text string or a single file (`--source`).
*   Outputs sentences separated by newline characters.
*   Perfect for preprocessing text before more complex chunking.

| Flag | Description | Default |
|---|---|---|
| `<TEXT>` | The input text to split. If not provided, `--source` must be used. | None |
| `--source, -s <PATH>` | Path to a single file to read input from. Cannot be a directory. | None |
| `--destination, -d <PATH>` | Path to a single file to write the segmented sentences. If not provided, output goes to STDOUT. | STDOUT |
| `--lang` | Language of the text (e.g., 'en', 'fr', 'auto'). Use 'auto' for automatic detection. | auto |
| `--verbose, -v` | Enable verbose logging for extra insights. | False |

### Scenarios: Splitting Like a Pro!

#### Scenario 1: Splitting Text Directly (and Multilingually!)

Segment a direct text input containing multiple languages into individual sentences, leveraging automatic language detection.

```bash
chunklet split "This is the first sentence. Here is the second sentence, in French. C'est la vie! ¿Cómo estás?" --lang auto
```

#### Scenario 2: Splitting a File and Saving the Output

Process a document and save its segmented sentences to a new file. Easy peasy!

```bash
chunklet split --source my_novel_chapter.txt --destination sentences.txt --lang en
```

--- 

## The `chunk` Command: Your Intelligent Chunking Workhorse!

The `chunk` command is where the real magic happens! It's your versatile tool for breaking down text, documents, and even code into RAG-ready chunks. The "flavor" of chunking (plain text, document, or code) is determined by the flags you provide.

### Key Flags for `chunk` (The Essentials!)

| Flag | Description | Default |
|---|---|---|
| `<TEXT>` | The input text to chunk. If not provided, `--source` must be used. | None |
| `--source, -s <PATH>` | Path(s) to one or more files or directories to read input from. Repeat for multiple sources (e.g., `-s file1.txt -s dir/`). | None |
| `--destination, -d <PATH>` | Path to a file (writes JSON for `.json` extensions or existing files) or directory (writes separate files) to write the chunks. If a non-JSON file exists, a warning is shown and JSON is written. If not provided, output goes to STDOUT. | STDOUT |
| `--max-tokens` | Maximum number of tokens per chunk. Applies to all chunking strategies. (Must be >= 12) | None |
| `--max-sentences` | Maximum number of sentences per chunk. Applies to DocumentChunker. (Must be >= 1) | None |
| `--max-section-breaks` | Maximum number of section breaks per chunk. Applies to DocumentChunker. (Must be >= 1) | None |
| `--overlap-percent` | Percentage of overlap between chunks (0-85). Applies to DocumentChunker. | 20.0 |
| `--offset` | Starting sentence offset for chunking. Applies to DocumentChunker. | 0 |
| `--lang` | Language of the text (e.g., 'en', 'fr', 'auto'). (default: auto) | auto |
| `--metadata` | Include rich metadata (source, span, chunk num, etc.) in the output. If `--destination` is a directory, metadata is saved as separate `.json` files; otherwise, it's included inline in the output. | False |
| `--verbose, -v` | Enable verbose logging for extra insights. | False |

---

### General Text & Document Chunking (Default or with `--doc`) 📄

This is your bread-and-butter chunking for everyday text and diverse document types.

*   **Default Behavior:** If neither `--doc` nor `--code` is specified, `chunklet` uses the [DocumentChunker](programmatic/document_chunker.md) for direct text input. The `DocumentChunker` is designed to transform unruly text into perfectly sized, context-aware chunks.
*   **Document Power-Up:** Activate the [DocumentChunker](programmatic/document_chunker.md) with the `--doc` flag to process `.pdf`, `.docx`, `.epub`, `.txt`, `.tex`, `.html`, `.hml`, `.md`, `.rst`, and `.rtf` files! It intelligently extracts text and then applies the same robust chunking logic.

#### Key Flags for Document Power-Up

| Flag | Description | Default |
|---|---|---|
| `--doc` | Activate the `DocumentChunker` for multi-format file processing. | False |
| `--n-jobs` | Number of parallel jobs for batch processing. (None uses all available cores) | None |
| `--on-errors` | How to handle errors during batch processing: `raise` (stop), `skip` (ignore file, continue), or `break` (halt, return partial result). | raise |

#### Scenarios: Text & Document Chunking in Action!

##### Scenario 1: Basic Text Chunking with Token Limits and Overlap

Chunk a long text string into segments, ensuring no chunk exceeds 200 tokens, with a healthy 15% overlap for context.

```bash
chunklet chunk "The quick brown fox jumps over the lazy dog. This is the first sentence. The second sentence is a bit longer. And this is the third one. Finally, the fourth sentence concludes our example. The last sentence is here to finish the text."
  --max-tokens 200 \
  --overlap-percent 15
```

##### Scenario 2: Chunking a PDF Document with Sentence and Section Break Limits

Process a PDF document, ensuring chunks are no more than 10 sentences or 2 section breaks, and save the output to a file.

```bash
chunklet chunk --doc --source my_report.pdf \
  --max-sentences 10 \
  --max-section-breaks 2 \
  --destination processed_report_chunks.txt
```

##### Scenario 3: Batch Processing a Directory of Documents (with Error Handling!)

Process all supported documents within a directory, saving the chunks to a new folder. If any file causes an error, `chunklet` will gracefully skip it and continue!

```bash
chunklet chunk --doc \
  --source /path/to/my/project_docs \
  --destination ./processed_chunks \
  --n-jobs 4 \
  --on-errors skip \
  --max-tokens 1024 \
  --metadata # Don't forget your metadata!
```

##### Scenario 4: Chunking a Text File with a Specific Language and Metadata

Chunk a French text file, limiting by tokens, and include all the juicy metadata for later analysis.

```bash
chunklet chunk --source french_article.txt \
  --lang fr \
  --max-tokens 300 \
  --metadata
```

---

### Code Chunking (with `--code`) 🧑‍💻

For the developers, by the developers! The [CodeChunker](programmatic/code_chunker.md) is a language-agnostic wizard that breaks your source code into semantically meaningful blocks (functions, classes, etc.). Activate it with the `--code` flag.

*   **Heads Up!** This mode is primarily token-based. `--max-sentences`, `--max-section-breaks`, and `--overlap-percent` are generally ignored here, as code structure takes precedence.

#### Key Flags for Code Chunking

| Flag | Description | Default |
|---|---|---|
| `--code` | Activate the `CodeChunker` for structurally-aware code segmentation. | False |
| `--max-lines` | Maximum number of lines per chunk. (Must be >= 5) | None |
| `--max-functions` | Maximum number of functions per chunk. (Must be >= 1) | None |
| `--docstring-mode` | Docstring processing strategy: `summary` (first line), `all`, or `excluded`. | all |
| `--strict` | If `True`, raise an error when structural blocks exceed `--max-tokens`. If `False`, split oversized blocks. | True |
| `--include-comments` | Include comments in output chunks. | True |

#### Scenarios: Code Chunking in Action!

##### Scenario 1: Chunking a Single Python File, Excluding Comments

Get a clean, comment-free view of your code's structure. Perfect for quick reviews!

```bash
chunklet chunk --code --source my_script.py \
  --max-tokens 512 \
  --include-comments False
```

##### Scenario 2: Batch Chunking a Codebase, Allowing Oversized Blocks

Process an entire code repository, letting `chunklet` split any functions or classes that are just *too* long, and save everything to a dedicated folder.

```bash
chunklet chunk --code \
  --source ./my_awesome_repo \
  --destination ./code_chunks \
  --max-tokens 1024 \
  --strict False \
  --n-jobs 8 \
```

##### Scenario 3: Extracting Function Summaries (Docstring Mode: Summary)

Focus on the "what" of your functions by only including the first line of their docstrings.

```bash
chunklet chunk --code --source utils.py \
  --docstring-mode summary \
  --max-functions 1 \
```

##### Scenario 4: Chunking by Lines and Functions for Granular Control

For super-fine-grained control, chunk a file by both maximum lines and maximum functions per chunk.

```bash
chunklet chunk --code --source main.go \
  --max-lines 100 \
  --max-functions 2 \
  --max-tokens 700
```

---

## 🛠️ Advanced System Hooks

These flags are your secret weapons for scaling up operations, integrating with external tools, and getting the most out of your chunked data. They apply to the `chunk` command.

### System Hook Flags

| Flag | Description | Default |
|---|---|---|
| `--tokenizer-command` | A shell command string for token counting. It must take text via STDIN and output the integer count via STDOUT. | None |
| `--tokenizer-timeout, -t` | Timeout in seconds for the tokenizer command (default: no timeout). | None |
| `--n-jobs` | Number of parallel processes to use during batch operations. (None uses all available CPU cores) | None |
| `--on-errors` | Defines batch error handling: `raise` (stop), `skip` (ignore file, continue), or `break` (halt, return partial result). | raise |
| `--metadata` | Include rich [metadata](metadata.md) (source, span, chunk num, etc.) in the output. If `--destination` is a directory, metadata is saved as separate `.json` files; otherwise, it's included inline in the output. | False |
| `--verbose, -v` | Enable verbose logging for debugging or process detail. | False |

### Scenarios: Unleashing Advanced Power!

#### Scenario 1: Verbose Debugging for a Single File

When things get tricky, crank up the verbosity to see exactly what `chunklet` is doing under the hood while chunking a specific file.

```bash
chunklet chunk --source problematic_file.txt \
  --max-tokens 100 \
  --verbose
```

#### Scenario 2: Batch Processing with Parallelism and Error Skipping

Process a large collection of diverse documents, leveraging all your CPU cores, and gracefully skip any problematic files without halting the entire operation. Plus, get all the metadata!

```bash
chunklet chunk --doc \
  --source /path/to/massive_document_archive \
  --destination ./final_chunks \
  --n-jobs -1 # Use all available cores!
  --on-errors skip \
  --max-tokens 512 \
  --metadata
```

#### Scenario 3: Processing Multiple Specific Files with Advanced Hooks

Process a selection of individual files, explicitly listing each one, and apply advanced chunking parameters. This demonstrates how to handle a non-directory batch of files, ensuring each is processed with metadata and error handling.

```bash
chunklet chunk --doc \
  --source my_document.pdf \
  --source another_report.docx \
  --source plain_text_notes.txt \
  --destination ./processed_specific_files \
  --max-tokens 700 \
  --metadata \
  --on-errors skip
```

#### Scenario 4: Custom Token Counting with an External Script

Align `chunklet`'s chunk sizes perfectly with your LLM's token limits using *any* external tokenizer you can imagine! Optionally set a timeout:

```bash
chunklet chunk --text "Your text here" \
  --max-tokens 50 \
  --tokenizer-command "python ./my_tokenizer.py" \
  --tokenizer-timeout 30
```

👉 See the [Custom Tokenizers](../how-to/custom-tokenizer.md) guide for how to create a tokenizer script in any language.

##### Scenario 5: Saving Chunks as JSON with Metadata

Save processed chunks directly as a JSON file for easy parsing and integration:

```bash
chunklet chunk --source document.pdf --doc --destination chunks.json --metadata
```

---

## Diving Deeper into Metadata

Want to know *exactly* what kind of rich context `chunklet` attaches to your chunks? From source paths and character spans to document-specific properties and code AST details.

👉 Head over to the [Metadata in Chunklet-py guide](../getting-started/metadata.md) to unlock all its secrets!

---

## The `visualize` Command: Your Interactive Chunk Playground! 🎮

Ready to see your chunking in action with a beautiful web interface? The `visualize` command launches Chunklet's interactive web visualizer - perfect for experimenting with parameters, seeing real-time results, and fine-tuning your chunking strategies!

!!! tip "Want programmatic control?"
    For code-based usage and detailed technical information, check out the [Text Chunk Visualizer documentation](programmatic/visualizer.md).

This command starts a local web server that gives you:

- **Live parameter tuning** - Adjust chunking settings and see results instantly
- **Visual chunk exploration** - See exactly how your text gets divided
- **Multiple chunking modes** - Try plain text, document, and code chunking all in one place
- **Custom tokenizers** - Plug in your own token counting for precise control

### Key Flags for `visualize`

| Flag | Description | Default |
|---|---|---|
| `--host, -h` | Host IP to bind the server (use `0.0.0.0` for network access) | 127.0.0.1 |
| `--port, -p` | Port number for the server | 8000 |
| `--tokenizer-command` | Shell command for custom token counting | None |
| `--tokenizer-timeout, -t` | Timeout in seconds for the tokenizer command (default: no timeout) | None |
| `--headless` | Run without opening browser automatically | False |

### Getting Started with Visualization! 🖥

#### Scenario 1: Basic Visualizer Launch

Fire up the visualizer on the default port and let it open your browser automatically:

```bash
chunklet visualize
```

#### Scenario 2: Custom Port and Host

Run on a specific port and host (great for accessing from other devices):

```bash
chunklet visualize --host 0.0.0.0 --port 8080
```

#### Scenario 3: Headless Mode with Custom Tokenizer {#headless-cli}

Run in the background with your own token counting script:

```bash
chunklet visualize --headless \
  --tokenizer-command "python my_tokenizer.py" \
  --tokenizer-timeout 30
```

See the [Custom Tokenizers](../how-to/custom-tokenizer.md) guide for how to create a tokenizer script in any language.

The visualizer will show you the URL to access it in your browser. Press `Ctrl+C` to stop the server when you're done!

!!! info "REST API for Headless Automation! 🤖"
    When running in headless mode, you can use the visualizer's REST API to programmatically upload files, chunk content, and retrieve results without any web interface! Perfect for automation scripts, CI/CD pipelines, or integrating chunking into your applications.

    See the [Headless/REST API Usage](programmatic/visualizer.md#headlessrest-api-usage) section for complete examples of programmatic file processing.

!!! tip "Pro Visualization Tips"
    - Use `--headless false` (or just omit it) to auto-open your browser
    - Try different ports if 8000 is already in use
    - Experiment with different chunking modes - text, document, and code all in one interface!

---

??? info "API Reference"
    For a deep dive into the `chunklet` CLI, its commands, and all the nitty-gritty details, check out the full [API documentation](../reference/chunklet/cli.md)
