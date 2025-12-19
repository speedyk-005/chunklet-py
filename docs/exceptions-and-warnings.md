# Exceptions and Warnings: Navigating Chunklet's Quirks

Every powerful tool has its moments, and Chunklet-py is no different! This guide is here to help you understand the various messages and signals you might encounter. Most of these are straightforward to resolve, and some are simply helpful hints to keep you on track.

## Exceptions: When Things Need a Pause

Sometimes, unexpected situations arise that require Chunklet-py to pause its operations. When you encounter an exception, it means something significant occurred that prevented the process from continuing. But don't worry, we're here to help you understand what happened!

### `ChunkletError`

*   **Description:** This is the foundational exception for all operations within the Chunklet-py library. It serves as the base class for more specific exceptions related to chunking and splitting.
*   **Inherits from:** `Exception`
*   **When Raised:** While you typically won't encounter `ChunkletError` directly, it's the common ancestor for all our custom exceptions. This design makes it convenient to catch any Chunklet-related issues using a single `except ChunkletError` statement.

### `InvalidInputError`

*   **Description:** Oh dear! 😕 This exception appears when Chunklet-py encounters input that's a little... unexpected. It's like trying to bake a cake with salt instead of sugar – the ingredients just aren't quite right! This could mean a parameter is out of place, the data type is a surprise, or the input structure is a bit wonky. Chunklet-py is always eager to help, but it does need valid input to craft those perfect chunks!
*   **Inherits from:** `ChunkletError`
*   **When Raised:**
    *   When an invalid parameter is passed during initialization (e.g., providing a non-boolean value for a boolean flag).
    *   When an incorrect type of object is passed (e.g., a sentence splitter that doesn't inherit from the required base class).
    *   When a file path is missing a required extension.

### `MissingTokenCounterError`

*   **Description:** Imagine trying to bake a cake without a key ingredient like flour – that's pretty much what happens when Chunklet-py needs a `token_counter` but can't find one! This exception gently reminds you that a token counter is essential for token-based chunking.
    > A token_counter is required for token-based chunking.
    > 💡 Hint: Pass a token counting function to the `chunk` method, like `chunker.chunk(..., token_counter=tk)`
    > or configure it in the class initialization: `.*Chunker(token_counter=tk)`
*   **Inherits from:** `InvalidInputError`
*   **When Raised:**
    *   When performing token-based chunking ("token" or "hybrid" modes) without a `token_counter` function having been provided.

### `FileProcessingError`

*   **Description:** This exception signals that Chunklet-py encountered a problem while trying to interact with a file. It could be anything from a file that's playing hide-and-seek (not found!), to permission issues, encoding troubles, or even a file that's a bit under the weather (corrupted). Essentially, something prevented us from properly loading, opening, or accessing the file.
*   **Inherits from:** `ChunkletError`
*   **When Raised:**
    *   When a specified file does not exist at the given path.
    *   When there are issues reading a file's content due to permissions, encoding problems, or if it's a binary file.

### `UnsupportedFileTypeError`

*   **Description:** This exception pops up when Chunklet-py receives a file type it doesn't quite recognize. While we're always working to expand our capabilities, some file formats are simply beyond our current repertoire.
*   **Inherits from:** `FileProcessingError`
*   **When Raised:**
    *   When trying to process a file with an extension that is not supported or registered with a custom processor.

### `TokenLimitError`

*   **Description:** This exception occurs when a chunk exceeds the defined `max_tokens` limit. It's particularly relevant in modes where maintaining the semantic integrity of your content is paramount, even if it means not splitting a block further.
*   **Inherits from:** `ChunkletError`
*   **When Raised:**
    *   When a structural block of code (like a function or class) exceeds the `max_tokens` limit while in `strict_mode`, where splitting the block would compromise its integrity.

### `CallbackError`

*   **Description:** This exception occurs when a user-provided callback function (such as a `token_counter`, or a custom `sentence splitter` or `document processor`) encounters an error during its execution. It's Chunklet-py's way of letting you know that something went awry within the custom logic you've integrated.
*   **Inherits from:** `ChunkletError`
*   **When Raised:**
    *   When a user-provided callback function (like a `token_counter`, or a custom `sentence splitter` or `document processor`) raises an error during its execution in any chunking or batch process.

---

## Warnings: Chunklet-py's Gentle Reminders
    
Warnings from Chunklet-py are like friendly nudges – they let you know about situations that might warrant your attention, even though the process continues. They often highlight opportunities for optimization or important details to be aware of.

### "The language is set to `auto`. Consider setting the `lang` parameter to a specific language to improve reliability."

*   **What it means:** This warning appears when Chunklet-py is set to automatically detect the language of your text. While our language detection is quite capable, providing a specific `lang` parameter (e.g., `lang='en'` or `lang='fr'`) can often lead to faster and more accurate results, particularly with shorter texts. Think of it as giving Chunklet-py a helpful head start!
*   **Where Logged:** `src/chunklet/sentence_splitter/sentence_splitter.py`
*   **What to do:** If you know the language of your text, setting the `lang` parameter explicitly is a great idea. If not, no worries – Chunklet-py will still do its best to figure it out for you.


### "Using a universal rule-based splitter. Reason: Language not supported or detected with low confidence."
        
*   **What it means:** This warning indicates that Chunklet-py couldn't find a specialized sentence splitter for your language (or its confidence in detection was low). In such cases, it gracefully falls back to its universal rule-based regex splitter. This splitter is designed to be robust, offering a general solution for sentence segmentation.
*   **Where Logged:** `src/chunklet/sentence_splitter/sentence_splitter.py`
*   **What to do:** For languages requiring highly accurate and nuanced sentence splitting, exploring a [Custom Splitter](getting-started/programmatic/sentence_splitter.md#custom-sentence-splitter) might be beneficial. Otherwise, our universal splitter is a reliable option for general purposes.

### "Offset {} >= total sentences {}. Returning empty list."

*   **What it means:** This warning indicates that the provided `offset` value is greater than or equal to the total number of sentences in the text. Essentially, you've asked Chunklet-py to start processing beyond the available content.
*   **Where Logged:** `src/chunklet/plain_text_chunker.py`
*   **What to do:** To resolve this, simply adjust your `offset` parameter to a value within the valid range of sentences.

### "Skipping a failed task. \nReason: {error}"

*   **What it means:** During a batch operation, if an individual chunking task encounters an error, Chunklet-py is designed to skip that particular task and continue with the rest of the operation. This prevents the entire process from crashing and is a general warning triggered when `on_errors='skip'`.
*   **Where Logged:** `src/chunklet/utils/batch_runner.py` (This is a general-purpose warning from the batch runner, used by `PlainTextChunker`, `DocumentChunker`, and `CodeChunker` when `on_errors='skip'`).
*   **What to do:** We recommend checking the `Reason` provided in the warning for details about the failure. You might need to inspect the problematic input or adjust your `on_errors` parameter if you'd rather have the operation stop.

### "Skipping document '{}' at paths[{}] due to validation failure.\nReason: {}"

*   **What it means:** This warning appears when a file doesn't pass the initial validation checks before its content can be extracted. The `Reason` will give you more details about what went wrong (perhaps a corrupted file or an unsupported format). Don't worry, the invalid file is simply skipped, and processing continues.
*   **Where Logged:** `src/chunklet/document_chunker/document_chunker.py`
*   **What to do:** Take a look at the file path and the reason provided in the warning. This should help you pinpoint and resolve the validation issue.


### "No valid files found after validation. Returning empty generator."

*   **What it means:** During batch processing, after checking all your input paths, Chunklet-py discovered that none of them made the cut! 🫣 This could happen if the paths were pointing to the wrong place, the files were in formats we don't speak, or they all got politely excused due to validation issues. In any case, we're returning an empty generator since there's nothing to work with.
*   **Where Logged:** `src/chunklet/document_chunker/document_chunker.py` (during `batch_chunk` operations)
*   **What to do:** Double-check those file paths and make sure they're pointing to supported file types - we're ready whenever you are!

### "Splitting oversized block ({} tokens) into sub-chunks"

*   **What it means:** In `CodeChunker`'s more relaxed mode, one of your code blocks turned out to be a bit of a heavyweight - too big for the `max_tokens` limit! 💪 Rather than throwing up its hands in defeat, Chunklet-py decided to be extra helpful and split it into more manageable sub-chunks.
*   **Where Logged:** `src/chunklet/experimental/code_chunker/code_chunker.py` (during `chunk` operations when `strict_mode=False`)
*   **What to do:** This is just a friendly heads-up about what we're doing. If you want us to be more strict about those token limits for code blocks, just set `strict_mode=True` in `CodeChunker`.

### "Warning: '{path}' is path-like but was not found or is not a processable file/directory. Skipping."

*   **What it means:** The path you provided via `--source` looked promising at first glance, but when we went to find it, it was either playing hide-and-seek (doesn't exist!) or turned out to be something special like a socket or pipe that we can't process. No worries - we'll just skip this one and keep going.
*   **Where Logged:** `src/chunklet/cli.py`
*   **What to do:** Give that path another look to make sure it's correct and points to a regular file or directory we can handle.

### "Warning: '{path}' does not resemble a valid file system path (failed heuristic check). Skipping."

*   **What it means:** The string you gave us via `--source` just doesn't look like a proper file system path to our trained eye. We use a clever heuristic to spot path-like strings, but this one didn't pass the test. We'll politely skip it and move along.
*   **Where Logged:** `src/chunklet/cli.py`
*   **What to do:** Make sure your source path is a proper, well-formed file system path - we're all set to handle it once it's right.

### "Warning: No processable files found in the specified source(s). Exiting."

*   **What it means:** We searched high and low through all the `--source` paths you provided, but couldn't find a single file we could process. 🕵️‍♀️ Maybe the directories are feeling a bit empty, or they only contain file types we don't speak yet. In any case, there's nothing for us to do, so we're gracefully bowing out.
*   **Where Logged:** `src/chunklet/cli.py`
*   **What to do:** Double-check those source paths and make sure they contain files in formats we support.

### "Warning: No chunks were generated. This might be because the input was empty or did not contain any processable content."

*   **What it means:** The chunking process ran its course, but unfortunately, no chunks came out the other side. This often happens when your input text was empty, or the files you provided turned out to be text-free zones with nothing we could extract. Since there's nothing to show for our efforts, we're calling it a day.
*   **Where Logged:** `src/chunklet/cli.py`
*   **What to do:** Take a peek at your input to make sure there's some actual text content we can work with.
