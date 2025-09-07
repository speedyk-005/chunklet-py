# CLI Usage: Your Command-Line Companion

So, you're ready to get your hands dirty with some command-line action? Excellent! `chunklet-py` isn't just a fancy library; it's also a handy CLI tool. A quick `pip install chunklet-py` and you'll have `chunklet` at your beck and call, ready to slice and dice your text.

Run chunklet --help for full options.

## Basic Chunking: Getting Started with the Essentials

Specifying Chunking Mode and Parameters: Because One Size Rarely Fits All

You're about to discover the various ways `chunklet` can dissect your text. We'll cover the core arguments that let you control how your text gets chopped up, so you can get exactly what you need (or at least, something close).

> **Note:** The following examples showcase individual flags for clarity. However, most flags can be combined to create more complex and specific chunking behaviors.

| Flag | Alias | Description | Default |
|---|---|---|---|
| `text` | | The input text to chunk. | |
| `--file` | `--input-file` | Path to a text file to read input from. | |
| `--output-file` | | Path to a file to write the output chunks to. | |
| `--input-dir` | | Path to a directory to read input files from. | |
| `--output-dir` | | Path to a directory to write the output chunks to. | |
| `--mode` | | Chunking mode: 'sentence', 'token', or 'hybrid'. | `sentence` |
| `--lang` | | Language of the text (e.g., 'en', 'fr', 'auto'). | `auto` |
| `--max-tokens` | | Maximum number of tokens per chunk. | `256` |
| `--max-sentences` | | Maximum number of sentences per chunk. | `12` |
| `--overlap-percent` | | Percentage of overlap between chunks (0-85). | `10` |
| `--offset` | | Starting sentence offset for chunking. | `0` |
| `-v` | `--verbose` | Enable verbose logging. | |
| `--no-cache` | | Disable LRU caching. | |
| `--batch` | | Process input as a list of texts for batch chunking. | |
| `--n-jobs` | | Number of parallel jobs for batch chunking. | `None` |
| `--tokenizer-command` | | A shell command to use for token counting. | |
| `--version` | | Show program's version number and exit. | |

> ⚠️ **Note:** Language will be detected automatically if not set explicitly, but you'll see this warning in output.
> ```
> 2025-08-30 22:09:09.355 | WARNING | chunklet.core:chunk:481 -
> Found 1 unique warning(s) during chunking:
> - The language is set to `auto`. Consider setting the `lang` parameter to a specific language to improve performance.
> ```

### Sentence Mode: Keeping Your Thoughts Intact

This mode is for those who appreciate the elegance of a complete sentence. `chunklet` will diligently break down your text based on sentence boundaries, ensuring each chunk is a coherent thought. It's perfect for when you want to maintain the natural flow of your content, just in smaller, more manageable pieces.

```bash
chunklet "She loves cooking. He studies AI. The weather is great." \
    --max-sentences 2 \
    --lang "en"
```

<details>
<summary>Output</summary>

```
--- Chunk 1 ---
She loves cooking. He studies AI.

--- Chunk 2 ---
The weather is great.
```

</details>

### Token Mode: When Every Character Counts (Almost)

For the detail-oriented among us, Token Mode focuses on the raw building blocks of your text. Whether you're counting words, characters, or something more exotic, this mode lets you define chunk sizes by the number of tokens. You can even hook up your own custom tokenizer if you're feeling adventurous – because who are we to tell you how to count your tokens?

```bash
# Example using 'wc -w' as a simple word counter (approximation of tokens)
chunklet "Hello world! You see that? This is a sample text for token counting." \
    --mode token \
    --max-tokens 10 \
    --tokenizer-command "wc -w"
```

<details>
<summary>Output</summary>

```
2025-08-30 22:09:09.355 | WARNING | chunklet.core:chunk:481 -
Found 1 unique warning(s) during chunking:
- The language is set to `auto`. Consider setting the `lang` parameter to a specific language to improve performance.
--- Chunk 1 ---
Hello world! You see that?

--- Chunk 2 ---
This is a sample text for token counting.
```

</details>

For more accurate tokenization that matches OpenAI's models, you can use the `tiktoken` library.

1. **Install `tiktoken`:**

   ```bash
   pip install tiktoken
   ```

2. **Create a tokenizer script (`my_tokenizer.py`):**

   ```python
   # my_tokenizer.py
   import tiktoken
   import sys

   # Note: tiktoken will download the selected encoding models on first usage.
   def count_tokens(text):
       # Using cl100k_base encoding, suitable for gpt-3.5-turbo and gpt-4
       encoding = tiktoken.get_encoding("cl100k_base")
       return len(encoding.encode(text))

   if __name__ == "__main__":
       input_text = sys.stdin.read()
       token_count = count_tokens(input_text)
       print(token_count)
   ```

3. **Use the script with `chunklet`:**

   ```bash
   chunklet "Your long text here..." \
    --mode token \
    --max-tokens 100 \
    --tokenizer-command "python my_tokenizer.py"
   ```

### Hybrid Mode: The Smart Compromise

Hybrid Mode is `chunklet`'s attempt at being the smartest kid in the chunking class. It starts by trying to split your text into sentences using its advanced, language-aware splitters. If your language isn't explicitly supported, or if your text is a bit... unconventional, it gracefully falls back to a robust, universal regex-based sentence splitter. So, you'll always get something that looks like sentences.

Once it has these sentences, Hybrid Mode then groups them into chunks, but with a keen eye on *both* your `max-sentences` and `max-tokens` limits. It tries its best to keep sentences whole, but if adding a full sentence would push a chunk over the `max-tokens` limit, it gets clever. It'll then try to fit just parts of that sentence (clauses) into the remaining space, ensuring your chunks stay within budget while still being as semantically complete as possible. It's the perfect choice when you want readable chunks but also need to strictly control their size, especially useful for LLM contexts where token limits are king.

```bash
chunklet "Bonjou tout moun! Byenvini anko. Mesye dam, Kitem prezante nou 'hybrid mode'. Li vreman bon." \
     --max-sentences 3 \
     --mode hybrid \
     --max-tokens 10 \
     --tokenizer-command "wc -w" \
     --overlap-percent 30 \
     --lang "ht"
```

<details>
<summary>Output</summary>

```
2025-08-30 22:52:23.951 | WARNING | chunklet.core:chunk:481 -
Found 1 unique warning(s) during chunking:
- Language not supported or detected with low confidence. Universal regex splitter was used.
--- Chunk 1 ---
Bonjou tout moun! Byenvini anko. Mesye dam,

--- Chunk 2 ---
Mesye dam, Kitem prezante nou 'hybrid mode'. Li vreman bon.
```

</details>

---

## Advanced Usage: Beyond the Command Line (Files and Directories)

> For the following examples, let's assume we have a directory named `my_documents` with the following two files:
>
> **my_documents/story.txt**
> ```
> In a quiet village nestled between rolling hills and a whispering forest, lived a clockmaker named Elias. His hands, though old and worn, moved with a grace that defied his age. He didn't just make clocks; he crafted time itself, each tick a heartbeat, each tock a breath. One day, a mysterious traveler arrived, carrying a pocket watch that didn't tell time, but rather, seemed to hold it. The watch, the traveler claimed, could show glimpses of what was, what is, and what could be. Intrigued, Elias traded his finest creation for the enigmatic timepiece, a decision that would unravel the very fabric of his reality.
> ```
>
> **my_documents/poem.md**
> ```
> The wind, a restless poet, writes verses on the leaves,
> Of summer's fleeting sonnet, and autumn's golden eves.
> It sings a mournful ballad, a lament for the fallen snow,
> And whispers tales of springtime, in the gentle seeds that grow.
> ```

### Chunking from a File: When Your Text Lives in a Document

Got a text file you need to chunk? `chunklet` can handle that. Just point it to your file, and it'll process the content. You can even tell it to save the output to another file, keeping your console tidy. Remember, `--file` and `--input-file` are just two ways to say the same thing – we like options!

> ⚠️ **Deprecation Notice:** While you *can* use `--file` (or `--input-file`) with `--batch` for processing multiple lines from a single file, this approach is deprecated and will be removed in future releases.
> Please use `--input-dir` for batch processing multiple files instead. For more details on this and other friendly nudges from Chunklet, check out the [Exceptions and Warnings](../exceptions-and-warnings.md) documentation.

```bash
# Chunk from my_documents/story.txt and print to console
chunklet --file my_documents/story.txt \
    --mode sentence \
    --max-sentences 2
```

<details>
<summary>Output</summary>

```
--- Chunk 1 ---
In a quiet village nestled between rolling hills and a whispering forest, lived a clockmaker named Elias. His hands, though old and worn, moved with a grace that defied his age.

--- Chunk 2 ---
He didn't just make clocks; he crafted time itself, each tick a heartbeat, each tock a breath. One day, a mysterious traveler arrived, carrying a pocket watch that didn't tell time, but rather, seemed to hold it.

--- Chunk 3 ---
... seemed to hold it. The watch, the traveler claimed, could show glimpses of what was, what is, and what could be.

--- Chunk 4 ---
... and what could be. Intrigued, Elias traded his finest creation for the enigmatic timepiece, a decision that would unravel the very fabric of his reality.

2025-08-30 21:39:55.197 | WARNING | chunklet.core:chunk:481 -
Found 1 unique warning(s) during chunking:
- The language is set to `auto`. Consider setting the `lang` parameter to a specific language to improve performance.
```

</details>

```bash
# Chunk from my_documents/story.txt and save to output.txt
chunklet --input-file my_documents/story.txt \
    --output-file output.txt \
    --mode sentence \
    --max-sentences 2
```

This command will create a file named `output.txt` containing the output.

### Chunking from a Directory: For When You Have a Whole Folder of Fun

Why chunk one file when you can chunk them all? If your texts are neatly organized in a directory, `chunklet` can sweep through it, processing all `.txt` and `.md` files (and it's smart enough to find them even in subfolders!). It's batch processing, `chunklet` style.

```bash
# Process all text files in 'my_documents/' and print chunks to console
chunklet --input-dir my_documents/ \
    --mode token \
    --max-tokens 10 \
    --tokenizer-command "wc -w"
```

<details>
<summary>Output</summary>

```
## Source: my_documents/story.txt

--- Chunk 1 ---
In a quiet village nestled between rolling hills and a whispering forest, lived a clockmaker named Elias.

--- Chunk 2 ---
His hands, though old and worn, moved with a grace that defied his age.

--- Chunk 3 ---
He didn't just make clocks; he crafted time itself, each tick a heartbeat, each tock a breath.

--- Chunk 4 ---
One day, a mysterious traveler arrived, carrying a pocket watch that didn't tell time, but rather, seemed to hold it.

--- Chunk 5 ---
The watch, the traveler claimed, could show glimpses of what was, what is, and what could be.

--- Chunk 6 ---
Intrigued, Elias traded his finest creation for the enigmatic timepiece, a decision that would unravel the very fabric of his reality.

## Source: my_documents/poem.md

--- Chunk 1 ---
The wind, a restless poet, writes verses on the leaves,

--- Chunk 2 ---
Of summer's fleeting sonnet, and autumn's golden eves.

--- Chunk 3 ---
It sings a mournful ballad, a lament for the fallen snow,

--- Chunk 4 ---
And whispers tales of springtime, in the gentle seeds that grow.

2025-08-30 21:54:37.662 | WARNING | chunklet.core:batch_chunk:596 -
Found 1 unique warning(s) during batch processing of 2 texts:
- (2/2) The language is set to `auto`. Consider setting the `lang` parameter to a specific language to improve performance.
```

</details>

### Saving Chunks to a Directory: Because Sometimes You Need More Than Just Console Output

Printing chunks to your terminal is cool and all, but what if you need those chunks as actual files? `chunklet` understands. Just tell it an output directory, and it will dutifully save each generated chunk as its own separate file. Perfect for when you're building something bigger and need those individual pieces.

```bash
# Process 'input.txt' and save each chunk as a separate file in 'output_chunks/'
chunklet --file input.txt \
    --output-dir output_chunks/ \
    --mode token \
    --max-tokens 50
# Example output files: output_chunks/input_chunk_1.txt, output_chunks/input_chunk_2.txt
```

You should see a message like this:
```
Successfully processed 1 file(s) and wrote 6 chunk file(s) to output_chunks/
```

This will create the directory with the following files:

```
output_chunks/
├── story_chunk_1.txt
├── story_chunk_2.txt
├── story_chunk_3.txt
├── story_chunk_4.txt
├── story_chunk_5.txt
└── story_chunk_6.txt
```

### Combined Directory Input and Output: The Full Automation Experience

For the true power users (or just the really lazy ones), `chunklet` offers the ultimate convenience: process an entire input directory and save all the resulting chunks into a separate output directory. It's like setting up your own personal chunking factory – just point, click (well, type), and let `chunklet` handle the rest. Your hands will thank you.

```bash
# Process all files in 'my_documents/' and save individual chunks to 'processed_chunks/'
chunklet --input-dir my_documents/ \
    --output-dir processed_chunks/ \
    --mode hybrid \
    --max-sentences 3 \
    --max-tokens 100 \
    --tokenizer-command "wc -w"
```

You should see a message like this:
```
Successfully processed 2 file(s) and wrote 5 chunk file(s) to processed_chunks/
```

This will create the directory with the following files:

```
processed_chunks/
├── poem_chunk_1.txt
├── poem_chunk_2.txt
├── story_chunk_1.txt
├── story_chunk_2.txt
└── story_chunk_3.txt
```

### Speeding Up Batch Processing with `--n-jobs`

When you're processing a large number of files in a directory, you can speed things up by using the `--n-jobs` argument. This allows `chunklet` to process multiple files in parallel, taking advantage of multiple CPU cores.

```bash
# Process all files in 'my_documents/' using 4 parallel jobs
chunklet --input-dir my_documents/ \
    --output-dir processed_chunks/ \
    --n-jobs 4
```

By default, `chunklet` will use all available CPU cores. You can specify a number to limit the number of parallel jobs.

<blockquote>
<p style="color: orange; font-weight: bold;">
⚠️ <strong>Note:</strong> Language will be detected automatically if not set explicitly, but you'll see this warning in output.
</p>
<pre style="background-color: #f9f9f9; border: 1px solid #ccc; padding: 10px;">
2025-08-30 22:09:09.355 | WARNING | chunklet.core:chunk:481 -
Found 1 unique warning(s) during chunking:
- The language is set to `auto`. Consider setting the `lang` parameter to a specific language to improve performance.
</pre>
</blockquote>

## Best Practices for CLI Usage

To get the most out of the `chunklet` CLI, consider these best practices:

*   **Explicit Language Setting:** While `chunklet`'s `--lang auto` detection is robust, explicitly setting the `--lang` parameter when you know the language of your text can significantly improve performance and accuracy, especially for shorter texts or less common languages.

    > **Tip:** For consistent results and to avoid language detection warnings, always specify `--lang` if your text's language is known.

*   **Leverage Batch Processing for Multiple Files:** For processing multiple documents, always prefer `--input-dir` over iterating and calling `chunklet` individually for each file. `--input-dir` is optimized for parallel processing and will significantly speed up your workflow, especially when combined with `--n-jobs`.

    > **Tip:** Use `--n-jobs` with `--input-dir` to utilize multiple CPU cores for even faster batch processing.

*   **Understand Output Options:** Decide whether you need console output, a single output file (`--output-file`), or individual chunk files in an output directory (`--output-dir`). Choose the option that best suits your downstream processing needs.

*   **Monitor Warnings:** Pay attention to the warnings `chunklet` emits. They often provide valuable insights into potential optimizations (e.g., language detection confidence) or inform you about fallback mechanisms being used.

*   **Use a Custom Tokenizer for LLM Alignment:** If you're preparing text for a specific Large Language Model (LLM), integrate its tokenizer using `--tokenizer-command`. This ensures your chunks align perfectly with the LLM's tokenization strategy, preventing truncation issues and optimizing token usage.

