# Plain Text Chunker

<p align="center">
  <img src="../../img/plain_text_chunker.jpg" alt="Plain Text Chunker" width="300"/>
</p>

## Taming Your Text with Precision

Do you have large blocks of text that need to be organized into smaller, more manageable pieces? The `PlainTextChunker` is designed to help you transform unruly text into perfectly sized, context-aware chunks. Whether you're preparing data for a Large Language Model (LLM) or building a search index, this tool aims to simplify your workflow.

Our approach goes beyond simple text splitting; it's about intelligent segmentation. The `PlainTextChunker` prioritizes context, working diligently to preserve the meaning and natural flow of your text.

Ready to bring order to your text? Let's explore how!

### Where it shines?

The `PlainTextChunker` is equipped with a comprehensive set of features designed to address various text-chunking requirements:

-  **Multiple Chunking Modes:** Choose from splitting by sentence count, token count, or a hybrid approach, providing flexibility for diverse use cases.
-  **Clause-Level Overlap:** This feature ensures seamless transitions between chunks by intelligently overlapping content at natural clause boundaries, maintaining contextual flow.
-  **Multilingual Support:** Similar to our sentence splitter, this chunker supports a wide array of languages, offering broad applicability.
-  **Pluggable Token Counters:** Easily integrate your custom token counting functions to align with the specific tokenization needs of your Large Language Models.
-  **Efficient Parallel Processing:** For large volumes of text, the `PlainTextChunker` can leverage multiple processors to expedite the chunking process.
-  **Memory-Efficient Processing:** Even when handling extensive documents, this chunker operates efficiently by yielding chunks one at a time, thereby minimizing memory usage.

### Chunking Modes Explained  

`PlainTextChunker` offers three chunking modes. Here’s a quick rundown:

| Mode       | `max_sentences` | `max_tokens` | Description                                                                                                                                                           |
|------------|-----------------|--------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `sentence` | Should be >= 1 | Ignored      | This mode is all about sentence power! You tell Chunklet how many sentences you want per chunk (`max_sentences`), and it gracefully groups them together, making sure your ideas flow smoothly from one chunk to the next. |
| `token`    | Ignored         | Should be >= 12         | Got a strict token budget? This mode is your best friend! Chunklet carefully adds sentences to your chunk, keeping a watchful eye on the `max_tokens` limit. If a sentence is a bit too chatty, it'll even politely split it at clause boundaries to keep everything perfectly snug. |
| `hybrid`   | Should be >= 1            | Should be >= 12         | Why choose when you can have both? Hybrid mode gives you the best of both worlds! Chunklet respects *both* your `max_sentences` and `max_tokens` limits, ensuring your chunks are beautifully balanced and stop when either limit is reached. It’s like having a personal chunking assistant who knows exactly what you need! |

The `PlainTextChunker` has two main methods: `chunk` for processing a single text and `batch_chunk` for processing multiple texts. Both methods return a generator that yields a [`Box`](https://pypi.org/project/python-box/#:~:text=Overview,strings%20or%20files.) object for each chunk. The `Box` object has two main keys: `content` (str) and `metadata` (dict).


## Single Run

### Sentence Mode

Here's how you can use `PlainTextChunker` in "sentence" mode to chunk text:

```python
from chunklet.plain_text_chunker import PlainTextChunker

text = """
The quick brown fox jumps over the lazy dog. This is the first sentence.
Here is the second sentence, which is a bit longer. And this is the third one.
Finally, the fourth sentence concludes our example.
"""

chunker = PlainTextChunker()  # (1)!

chunks = chunker.chunk(
    text=text,
    mode="sentence",
    lang="auto",             # (2)!
    max_sentences=2,         # (3)!
    overlap_percent=0,       # (4)!
    offset=0                 # (5)!
)

for i, chunk in enumerate(chunks):
    print(f"--- Chunk {i+1} ---")
    print(f"Metadata: {chunk.metadata}")
    print(f"Content: {chunk.content}")
    print()
```

1.  Setting `verbose=True` enables detailed logging, which is `False` by default, showing internal processes like language detection.
2.  Instructs the chunker to automatically detect the language of the input text. While convenient, explicitly setting the language (e.g., `lang="en"`) can improve accuracy and performance for known languages.
3.  Sets the maximum number of sentences allowed per chunk. In this example, chunks will contain at most two sentences. The default value is 12.
4.  Configures the chunker to have no overlap between consecutive chunks. The default behavior includes a 20% overlap to maintain context across chunks.
5.  Specifies that chunking should start from the very beginning of the text (the first sentence). The default is 0.

??? success "Click to show output"
    ```
    --- Chunk 1 ---
    Metadata: {'chunk_num': 1, 'span': (-1, -1)}
    Content: The quick brown fox jumps over the lazy dog.
    This is the first sentence.

    --- Chunk 2 ---
    Metadata: {'chunk_num': 2, 'span': (126, 203)}
    Content: And this is the third one.
    Finally, the fourth sentence concludes our example.
    ```

!!! tip "Enable Verbose Logging"
    To see detailed logging during the chunking process, you can set the `verbose` parameter to `True` when initializing the `DocumentChunker`:
    ```python
    chunker = PlainTextChunker(verbose=True)
    ```
    
!!! tip "Adding Base Metadata"
    You can pass a `base_metadata` dictionary to the `chunk` method. This metadata will be included in the `metadata` of each chunk. For example: `chunker.chunk(..., base_metadata={"source": "my_document.txt"})`.

!!! tip "Customizing the Continuation Marker"
    You can customize the continuation marker, which is prepended to clauses that don't fit in the previous chunk. To do this, pass the `continuation_marker` parameter to the chunker's constructor.

    ```python
    chunker = PlainTextChunker(continuation_marker="[...]")
    ```

    If you don't want any continuation marker, you can set it to an empty string:

    ```python
    chunker = PlainTextChunker(continuation_marker="")
    ```


### Other Modes
To use the `token` or `hybrid` modes, simply set the `mode` parameter accordingly and provide the relevant limit (`max_tokens` or both `max_sentences` and `max_tokens`).

!!! note "Token Counter Requirement"
    When using `token` or `hybrid` mode, a `token_counter` function is essential. This function, which you provide, should accept a string and return an integer representing its token count. Failing to provide a `token_counter` in these modes will result in a [`MissingTokenCounterError`](../../exceptions-and-warnings.md#missingtokencountererror).

#### Setup
```python
from chunklet.plain_text_chunker import PlainTextChunker

# Simple counter for demonstration purpose
def word_counter(text: str) -> int:
    return len(text.split())

chunker = PlainTextChunker(token_counter=word_counter)         # (1)!
```

1.  Initializes `PlainTextChunker` with a custom `word_counter` function. This function will be used to count tokens in `token` and `hybrid` modes.

#### Token Mode Usage
```python
chunks = chunker.chunk(
    text=text,
    mode="token",
    lang="auto",
    max_tokens=12,         # (1)!
)
```

1.  Sets the maximum number of tokens per chunk to 12. The default value is 256.

#### Hybrid Mode Usage
```python
chunks = chunker.chunk(
    text=text,
    mode="hybrid",
    lang="auto",
    max_sentences=2,
    max_tokens=12,
)
```

!!! tip "Overrides token_counter"
    You can also provide the `token_counter` directly to the `chunk` method. within the `chunk` method call (e.g., `chunker.chunk(..., token_counter=my_tokenizer_function)`). If a `token_counter` is provided in both the constructor and the `chunk` method, the one in the `chunk` method will be used.  

## Batch Run

While the `chunk` method is perfect for processing a single text, the `batch_chunk` method is designed for efficiently processing multiple texts in parallel. It returns a generator, allowing you to process large volumes of text without exhausting memory. It shares most of its core arguments with `chunk` (like `mode`, `max_sentences`, `max_tokens`, `lang`, `overlap_percent`, `offset`, and `token_counter`), but introduces additional parameters to manage batch processing.

Here's an example of how to use `batch_chunk`:

```python
from chunklet.plain_text_chunker import PlainTextChunker

def word_counter(text: str) -> int:
    return len(text.split())

EN_TEXT = "This is the first document. It has multiple sentences for chunking. Here is the second document. It is a bit longer to test batch processing effectively. And this is the third document. Short and sweet, but still part of the batch. The fourth document. Another one to add to the collection for testing purposes."
ES_TEXT = "Este es el primer documento. Contiene varias frases para la segmentación de texto. El segundo ejemplo es más extenso. Queremos probar el procesamiento en diferentes idiomas."
FR_TEXT = "Ceci est le premier document. Il est essentiel pour l'évaluation multilingue. Le deuxième document est court mais important. La variation est la clé."

# Initialize PlainTextChunker
chunker = PlainTextChunker(token_counter=word_counter) 

chunks = chunker.batch_chunk(
    texts=[EN_TEXT, ES_TEXT, FR_TEXT],
    mode="hybrid",
    max_sentences=5,
    max_tokens=20,
    n_jobs=2,                    # (1)!
    on_errors="raise",           # (2)!
    show_progress=True,          # (3)!
)

for i, chunk in enumerate(chunks):
    print(f"--- Chunk {i+1} ---")
    print(f"Metadata: {chunk.metadata}")
    print(f"Content: {chunk.content}")
    print()
```

1.  Specifies the number of parallel processes to use for chunking. The default value is `None` (use all available CPU cores).
2.  Define how to handle errors during processing. Determines how errors during chunking are handled. If set to `"raise"` (default), an exception will be raised immediately. If set to `"break"`, the process will be halt and partial result will be returned.
 If set to `"ignore"`, errors will be silently ignored.
3.  Display a progress bar during batch processing. The default value is `False`.

??? success "Click to show output"
    ```
      0%|                                                        | 0/3 [00:00<?, ?it/s]--- Chunk 1 ---
    Metadata: {'chunk_num': 1, 'span': (0, 97)}
    Content: This is the first document.
    It has multiple sentences for chunking.
    Here is the second document.


    --- Chunk 2 ---
    Metadata: {'chunk_num': 2, 'span': (97, 203)}
    Content: It is a bit longer to test batch processing effectively.
    And this is the third document.
    Short and sweet,

    --- Chunk 3 ---
    Metadata: {'chunk_num': 3, 'span': (186, 253)}
    Content: Short and sweet,
    but still part of the batch.
    The fourth document.


    --- Chunk 4 ---
    Metadata: {'chunk_num': 4, 'span': (253, 311)}
    Content: Another one to add to the collection for testing purposes.

    --- Chunk 5 ---
    Metadata: {'chunk_num': 1, 'span': (0, 125)}
    Content: Ceci est le premier document.
    Il est essentiel pour l'évaluation multilingue.
    Le deuxième document est court mais important.


    --- Chunk 6 ---
    Metadata: {'chunk_num': 2, 'span': (125, 149)}
    Content: La variation est la clé.

    --- Chunk 7 ---
    Metadata: {'chunk_num': 1, 'span': (0, 118)}
    Content: Este es el primer documento.
    Contiene varias frases para la segmentación de texto.
    El segundo ejemplo es más extenso.


    --- Chunk 8 ---
    Metadata: {'chunk_num': 2, 'span': (118, 173)}
    Content: Queremos probar el procesamiento en diferentes idiomas.

    100%|████████████████████████████████████████████████| 3/3 [00:00<00:00, 17.12it/s]
    ```

!!! warning "Generator Cleanup"
    When using `batch_chunk`, it's crucial to ensure the generator is properly closed, especially if you don't iterate through all the chunks. This is necessary to release the underlying multiprocessing resources. The recommended way is to use a `try...finally` block to call `close()` on the generator. For more details, see the [Troubleshooting](../../troubleshooting.md) guide.

!!! tip "Adding Base Metadata to Batches"
    Just like with the `chunk` method, you can pass a `base_metadata` dictionary to `batch_chunk`. This is useful for adding common information, like a source filename, to all chunks processed in the batch.

### Separator

The `separator` parameter allows you to specify a custom value to be yielded after all chunks for a given text have been processed. This is particularly useful when processing multiple texts in a batch, as it helps to clearly distinguish between the chunks originating from different input texts in the output stream.

**Note:** `None` cannot be used as a separator.

```python
from more_itertools import split_at
from chunklet.plain_text_chunker import PlainTextChunker

chunker = PlainTextChunker()
texts = [
    "This is the first document. It has two sentences.",
    "This is the second document. It also has two sentences."
]
custom_separator = "---END_OF_DOCUMENT---"

chunks_with_separators = chunker.batch_chunk(
    texts,
    mode="sentence",
    max_sentences=1,
    separator=custom_separator,
    show_progress=False,
)

chunk_groups = split_at(chunks_with_separators, lambda x: x == custom_separator)
# Process the results using split_at
for i, doc_chunks in enumerate(chunk_groups):
    if doc_chunks: # (1)!
        print(f"--- Chunks for Document {i+1} ---")
        for chunk in doc_chunks:
            print(f"Content: {chunk.content}")
            print(f"Metadata: {chunk.metadata}")
        print()
```

1.  Avoid processing the empty list at the end if stream ends with separator

??? success "Click to show output"
    ```
    --- Chunks for Document 1 ---
    Content: This is the first document.
    Metadata: {'chunk_num': 1, 'span': (0, 28)}

    --- Chunks for Document 2 ---
    Content: This is the second document.
    Metadata: {'chunk_num': 1, 'span': (0, 29)}
    ```

??? info "API Reference"
    For a deep dive into the `PlainTextChunker` class, its methods, and all the nitty-gritty details, check out the full [API documentation](../../reference/chunklet/plain_text_chunker.md).
