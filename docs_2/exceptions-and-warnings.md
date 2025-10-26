# Exceptions and Warnings: When Chunklet Gets a Bit Grumpy

Even the most robust tools have their moments, and Chunklet is no exception (pun intended!). This page is your guide to understanding the various hiccups and murmurs you might encounter while using Chunklet. Don't worry, most of them are easily fixed, and some are just friendly nudges.

## Exceptions: When Things Go Sideways (and Stop)

These are the big ones. When Chunklet throws an exception, it means something went wrong enough to halt the process. But fear not, we'll tell you why!

### `ChunkletError`

*   **Description:** Meet the grand-daddy of all Chunklet problems! This is the foundational exception for every single chunking and splitting operation in our library. Think of it as the wise old parent from whom all other, more specific, exceptions inherit their dramatic flair.
*   **Inherits from:** `Exception`
*   **When Raised:** You won't typically see `ChunkletError` itself popping up to say hello. It's more of a behind-the-scenes manager. Its main gig is to be the common ancestor for all our other custom exceptions, making it super easy for you to catch any Chunklet-related hiccup with a single `except ChunkletError`. How convenient is that?
*   **Usage:**
    ```python
    try:
        # Some chunklet operation
        pass
    except ChunkletError as e:
        print(f"A Chunklet-specific error occurred: {e}")
    ```

### `InvalidInputError`

*   **Description:** Uh-oh! This one pops up when Chunklet gets a bit confused by what you've given it. It means one or more of your inputs are just not playing by the rules – maybe a parameter is off, the data type is wrong, or the structure is a bit wonky. Chunklet's trying its best, but it needs valid ingredients to cook up those perfect chunks!
*   **Inherits from:** `ChunkletError`
*   **When Raised:**
    *   `DocumentChunker.__init__`: If you try to pass something that isn't a `PlainTextChunker` instance when initializing your `DocumentChunker`. (Hey, we like our chunkers to be specific!)
    *   `DocumentChunker._validate_path_extension`: If a file path you've provided is missing its extension. Chunklet needs to know what kind of file it's dealing with!
    *   `PlainTextChunker.__init__`: Similar to `DocumentChunker`, if you give it a `sentence_splitter` that isn't a `BaseSplitter` instance.
    *   `SentenceSplitter.__init__`: If you try to set `verbose` to something other than `True` or `False`. Boolean, please!
*   **Usage:**
    ```python
    from chunklet.exceptions import InvalidInputError

    try:
        chunker.chunk(text=123) # Example of invalid input
    except InvalidInputError as e:
        print(f"Invalid input provided: {e}")
    ```

### `MissingTokenCounterError`

*   **Description:** Ever tried to bake a cake without flour? That's kind of what happens when Chunklet needs a `token_counter` (especially for "token" or "hybrid" modes) but can't find one! This exception is our polite (but firm) way of saying, "Hey, I need to know *how* to count these tokens to do my job right!"
*   **Inherits from:** `InvalidInputError`
*   **When Raised:**
    *   `PlainTextChunker.chunk`: You'll see this if you're trying to chunk in "token" or "hybrid" mode, and you haven't given `PlainTextChunker` a `token_counter` (either during initialization or in the `chunk` method call).
    *   `CodeChunker.chunk`: Similarly, if `CodeChunker` is trying to do its token-aware magic and its `token_counter` is nowhere to be found.
*   **Usage:**
    ```python
    from chunklet.exceptions import MissingTokenCounterError
    from chunklet.plain_text_chunker import PlainTextChunker

    chunker = PlainTextChunker() # No token_counter provided
    try:
        chunker.chunk(text="Some text", mode="token")
    except MissingTokenCounterError as e:
    ```
    
### `UnsupportedFileTypeError`

*   **Description:** Oh, the dreaded "unsupported file type" message! This exception means you've handed Chunklet a file it just doesn't know how to deal with (yet!). We're always expanding our repertoire, but sometimes a file format is just too exotic for our current capabilities.
*   **Inherits from:** `InvalidInputError`
*   **When Raised:**
    *   `DocumentChunker._validate_path_extension`: If you try to process a file with an extension that isn't in our `SUPPORTED_EXTENSIONS` list, or if it's not registered with a custom processor.
    *   `DocumentChunker.chunk`: If you try to feed a PDF directly to the general `chunk` method. PDFs are special snowflakes and need `chunk_pdfs`!
    *   `DocumentChunker.chunk_pdfs`: If you sneak a non-PDF file into a list meant exclusively for PDFs. (We're looking at you, sneaky `.docx` files!)
*   **Usage:**
    ```python
    from chunklet.exceptions import UnsupportedFileTypeError
    from chunklet.document_chunker import DocumentChunker

    chunker = DocumentChunker()
    try:
        chunker.chunk(path="unsupported.xyz")
    except UnsupportedFileTypeError as e:
        print(f"Unsupported file type: {e}")
    ```

---

### `TokenLimitError`

*   **Description:** This exception is Chunklet's way of saying, "Whoa there, partner! That chunk is a bit too chunky for my `max_tokens` limit!" It's especially strict in certain modes where we prioritize keeping your content's semantic integrity intact, even if it means refusing to split further.
*   **Inherits from:** `ChunkletError`
*   **When Raised:**
    *   `CodeChunker.chunk`: If `strict_mode` is set to `True` and a structural code block (like a function or class) is so massive that it exceeds the `max_tokens` limit without any safe breaking points. We'd rather throw an error than mangle your beautiful code!
*   **Usage:**
    ```python
    from chunklet.exceptions import TokenLimitError
    from chunklet.experimental.code_chunker import CodeChunker

    code_chunker = CodeChunker(strict_mode=True)
    try:
        code_chunker.chunk(source="very_long_function_definition", max_tokens=10)
    except TokenLimitError as e:
        print(f"Token limit exceeded in strict mode: {e}")
    ```

---

### `FileProcessingError`

*   **Description:** This exception is Chunklet's way of throwing its hands up and saying, "I can't deal with this file!" It means something went wrong while trying to load, open, access, or generally mess with a file. Think of it as a digital roadblock due to I/O issues, pesky permissions, or even a corrupted file.
*   **Inherits from:** `ChunkletError`
*   **When Raised:**
    *   `DocumentChunker._validate_path_extension`: If a file simply doesn't exist at the given path. (Poof! Gone!)
    *   `DocumentChunker._extract_text`: If there are issues reading the file's content (e.g., permissions, encoding problems).
    *   `CodeChunker._read_source`: If the code file is nowhere to be found, is a binary file (we're text-only, folks!), or just can't be read for some mysterious reason.
*   **Usage:**
    ```python
    from chunklet.exceptions import FileProcessingError
    from chunklet.document_chunker import DocumentChunker

    chunker = DocumentChunker()
    try:
        chunker.chunk(path="/path/to/non_existent_file.txt")
    except FileProcessingError as e:
        print(f"File processing error: {e}")
    ```

---

### `CallbackExecutionError`

*   **Description:** Ever tried to get a friend to do something, and they just... well, they messed it up? This exception is Chunklet's version of that! It means a custom function you've handed over (like a special token counter or sentence splitter) decided to throw a tantrum during its execution.
*   **Inherits from:** `ChunkletError`
*   **When Raised:**
    *   `PlainTextChunker.chunk`: If your custom `token_counter` or `sentence_splitter` (or any other callback) decides to raise an error while Chunklet is trying to use it.
    *   `PlainTextChunker.batch_chunk`: If any of the callback functions fail during batch processing.
    *   `CodeChunker.batch_chunk`: If any of the callback functions fail during batch processing.
*   **Usage:**
    ```python
    from chunklet.exceptions import CallbackExecutionError
    from chunklet.plain_text_chunker import PlainTextChunker

    def buggy_token_counter(text):
        raise ValueError("Something went wrong!")

    chunker = PlainTextChunker(token_counter=buggy_token_counter)
    try:
        chunker.chunk(text="Hello world", mode="token")
    except CallbackExecutionError as e:
        print(f"Callback execution error: {e}")
    ```


## Warnings: Chunklet's Friendly Nudges (and Occasional Grumbles)
    
Warnings are Chunklet's way of saying, "Hey, I did what you asked, but you might want to know this..." They don't stop the process, but they often indicate something you could optimize or be aware of.

### "The language is set to `auto`. Consider setting the `lang` parameter to a specific language to improve reliability."

*   **What it means:** You've let Chunklet play detective and guess the language of your text. While our language detection skills are pretty sharp, giving us a direct hint (like `lang='en'` or `lang='fr'`) can sometimes make things even faster and more accurate, especially for those bite-sized texts. Think of it as giving us a cheat code!
*   **Where Logged:** `src/chunklet/sentence_splitter/sentence_splitter.py`
*   **What to do:** If you're a language wizard and know your text's tongue, go ahead and set that `lang` parameter! If not, no worries, Chunklet's got your back and will do its best to figure it out.


### "Using a universal rule-based splitter.\nReason: Language not supported or detected with low confidence."
        
*   **What it means:** Chunklet couldn't find a specialized sentence splitter for your language (or it wasn't confident enough in its detection), so it fell back to its trusty universal regex splitter. This splitter is robust but might not be as linguistically nuanced as the specialized ones.
*   **Where Logged:** `src/chunklet/sentence_splitter/sentence_splitter.py`
*   **What to do:** If you need highly accurate sentence splitting for an unsupported language, consider implementing a [Custom Splitter](getting-started/programmatic.md#custom-sentence-splitter). Otherwise, the universal splitter will still get the job done!

### "Offset {} >= total sentences {}. Returning empty list."

*   **What it means:** You've asked Chunklet to start chunking from an offset that's beyond the total number of sentences available in the text. It's like asking to start reading a book from page 100 when the book only has 50 pages!
*   **Where Logged:** `src/chunklet/plain_text_chunker.py`
*   **What to do:** Adjust your `offset` parameter to be within the valid range of sentences.

### "Skipping a failed task. \nReason: {error}"

*   **What it means:** During batch processing, one of the individual chunking tasks encountered an error. Instead of crashing the whole operation (because we're nice like that!), Chunklet skipped that particular task and continued with the rest.
*   **Where Logged:**
    *   `src/chunklet/plain_text_chunker.py` (during `batch_chunk` operations)
    *   `src/chunklet/experimental/code_chunker/code_chunker.py` (during `batch_chunk` operations)
*   **What to do:** Check the `Reason` provided in the warning for details about the failure. You might need to inspect the problematic input or adjust your `on_errors` parameter.

### "Skipping file {} at index {}. Reason: {}"

*   **What it means:** While processing a batch of files, Chunklet encountered an issue with a specific file (e.g., it's not a valid PDF, or it's corrupted). It's skipping this file to keep the batch processing going.
*   **Where Logged:** `src/chunklet/document_chunker/document_chunker.py` (during `chunk_pdfs` and `batch_chunk` operations)
*   **What to do:** Review the file mentioned in the warning and the `Reason` for the skip. Ensure the file is valid and accessible.

### "No valid PDF files found after validation. Returning empty generator."

*   **What it means:** You asked Chunklet to chunk a batch of PDFs, but after validation, it found zero valid PDF files in your list. It's like showing up to a party and no one's there!
*   **Where Logged:** `src/chunklet/document_chunker/document_chunker.py` (during `chunk_pdfs` operations)
*   **What to do:** Double-check your list of PDF paths. Make sure they exist and are indeed valid PDF files.

### "No valid files found after validation. Returning empty generator."

*   **What it means:** Similar to the PDF warning, but for general batch processing. Chunklet couldn't find any valid files to process after checking your input.
*   **Where Logged:** `src/chunklet/document_chunker/document_chunker.py` (during `batch_chunk` operations)
*   **What to do:** Verify your input file paths and ensure they are supported file types.

### "Skipping file {}. Reason: batch_chunk does not support .pdf files. Use chunk_pdfs instead."

*   **What it means:** You tried to include a PDF file in a general `batch_chunk` operation. Chunklet is reminding you that PDFs have their own special method (`chunk_pdfs`) because they need a bit more love and parallel processing.
*   **Where Logged:** `src/chunklet/document_chunker/document_chunker.py` (during `batch_chunk` operations)
*   **What to do:** If you have PDFs, use `chunker.chunk_pdfs()` for them. For other file types, `batch_chunk()` is your friend!

### "Splitting oversized block ({} tokens) into sub-chunks"

*   **What it means:** In `CodeChunker`'s lenient mode, a code block was too big for the `max_tokens` limit. Instead of throwing an error, Chunklet decided to be helpful and split it into smaller sub-chunks.
*   **Where Logged:** `src/chunklet/experimental/code_chunker/code_chunker.py` (during `chunk` operations when `strict_mode=False`)
*   **What to do:** This is usually just an informational warning. If you prefer stricter adherence to token limits for code blocks, consider setting `strict_mode=True` in `CodeChunker`.
