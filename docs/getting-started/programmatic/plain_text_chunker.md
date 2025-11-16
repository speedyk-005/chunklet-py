# Plain Text Chunker

<p align="center">
  <img src="../../img/plain_text_chunker.jpg" alt="Plain Text Chunker" width="300"/>
</p>

## Taming Your Text with Precision

Do you have large blocks of text that need to be organized into smaller, more manageable pieces? The `PlainTextChunker` is designed to help you transform unruly text into perfectly sized, context-aware chunks. Whether you're preparing data for a Large Language Model (LLM) or building a search index, this tool aims to simplify your workflow.

Our approach goes beyond simple text splitting; it's about intelligent segmentation. The `PlainTextChunker` prioritizes context, working diligently to preserve the meaning and natural flow of your text.

Ready to bring order to your text? Let's explore how!

### Where `PlainTextChunker` Excels

The `PlainTextChunker` is engineered with a robust set of features, making it highly adaptable for diverse text-chunking needs:

-  **Flexible Constraint-Based Chunking:** Imagine having ultimate control over your text chunks! `PlainTextChunker` empowers you to define exactly how your text is segmented. You can set limits based on sentence count, token count, or even those handy Markdown section breaks. The best part? You can combine them in any way you like, giving you unparalleled precision over your chunk's size and structure.
-  **Intelligent Overlap for Context Preservation:** Features clause-level overlap to ensure smooth transitions and maintain contextual coherence between consecutive chunks.
-  **Extensive Multilingual Support:** Leveraging the capabilities of our sentence splitter, this chunker supports a broad spectrum of languages, enhancing its global applicability.
-  **Customizable Token Counting:** Facilitates easy integration of custom token counting functions, allowing precise alignment with the specific tokenization requirements of different Large Language Models.
-  **Optimized Parallel Processing:** Designed to efficiently handle large text volumes by utilizing multiple processors, significantly accelerating the chunking workflow.
-  **Memory-Conscious Operation:** Processes even extensive documents with high memory efficiency by yielding chunks iteratively, thereby minimizing overall memory footprint.

### Constraint-Based Chunking Explained

`PlainTextChunker` uses a constraint-based approach to chunking. You can mix and match constraints to get the perfect chunk size. Here's a quick rundown of the available constraints:

| Constraint           | Value Requirement | Description
- `max_sentences`      | `int >= 1`        | This constraint is all about sentence power! You tell Chunklet how many sentences you want per chunk, and it gracefully groups them together, making sure your ideas flow smoothly from one chunk to the next.
- `max_tokens`         | `int >= 12`       | Got a strict token budget? This constraint is your best friend! Chunklet carefully adds sentences to your chunk, keeping a watchful eye on the token limit. If a sentence is a bit too chatty, it'll even politely split it at clause boundaries to keep everything perfectly snug.
- `max_section_breaks` | `int >= 1`        | Perfect for structured documents! This constraint lets you limit the number of Markdown-style section breaks (like headings `##` or horizontal rules `---`) in each chunk. It's a fantastic way to keep your document's structure intact while chunking. |

The `PlainTextChunker` has two main methods: `chunk` for processing a single text and `batch_chunk` for processing multiple texts. Both methods return a generator that yields a [`Box`](https://pypi.org/project/python-box/#:~:text=Overview,strings%20or%20files.) object for each chunk. The `Box` object has two main keys: `content` (str) and `metadata` (dict).

## Single Run

### Chunking by Sentences

Here's how you can use `PlainTextChunker` to chunk text by the number of sentences:

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
    Metadata: {'chunk_num': 1, 'span': (1, 74)}
    Content: The quick brown fox jumps over the lazy dog.
    This is the first sentence.

    --- Chunk 2 ---
    Metadata: {'chunk_num': 2, 'span': (126, 205)}
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

### Combining Constraints
The real power of `PlainTextChunker` comes from combining constraints. You can use `max_tokens` and `max_sentences` together to create chunks that respect both limits.

!!! note "Token Counter Requirement"
    When using the `max_tokens` constraint, a `token_counter` function is essential. This function, which you provide, should accept a string and return an integer representing its token count. Failing to provide a `token_counter` will result in a [`MissingTokenCounterError`](../../exceptions-and-warnings.md#missingtokencountererror).

#### Setup
```python
from chunklet.plain_text_chunker import PlainTextChunker

# Simple counter for demonstration purpose
def word_counter(text: str) -> int:
    return len(text.split())

chunker = PlainTextChunker(token_counter=word_counter)         # (1)!
```

1.  Initializes `PlainTextChunker` with a custom `word_counter` function. This function will be used to count tokens when `max_tokens` is used.

#### Chunking by Tokens
```python
chunks = chunker.chunk(
    text=text,
    lang="auto",
    max_tokens=12,         # (1)!
)
```

1.  Sets the maximum number of tokens per chunk to 12. The default value is 256.

#### Chunking by Sentences and Tokens
```python
chunks = chunker.chunk(
    text=text,
    lang="auto",
    max_sentences=2,
    max_tokens=12,
)
```

#### Chunking by Section Breaks
This constraint is useful for documents structured with Markdown headings or thematic breaks.

```python
from chunklet.plain_text_chunker import PlainTextChunker

text = """
# Chapter 1

This is the first paragraph. It contains some sentences.

## Section 1.1

More text here. This section is part of the first chapter.

---

# Chapter 2

A new chapter begins.
"""

chunker = PlainTextChunker()

chunks = chunker.chunk(
    text=text,
    max_section_breaks=2
)

for i, chunk in enumerate(chunks):
    print(f"--- Chunk {i+1} ---")
    print(f"Content: {chunk.content}")
    print()
```

??? success "Click to show output"
    ```
    --- Chunk 1 ---
    Content: # Chapter 1
    This is the first paragraph.
    It contains some sentences.

    ## Section 1.1
    More text here.
    This section is part of the first chapter.---

    --- Chunk 2 ---
    Content: This section is part of the first chapter.---
    A new chapter begins.
    ```

!!! tip "Overrides token_counter"
    You can also provide the `token_counter` directly to the `chunk` method. within the `chunk` method call (e.g., `chunker.chunk(..., token_counter=my_tokenizer_function)`). If a `token_counter` is provided in both the constructor and the `chunk` method, the one in the `chunk` method will be used.  

## Batch Run

While the `chunk` method is perfect for processing a single text, the `batch_chunk` method is designed for efficiently processing multiple texts in parallel. It returns a generator, allowing you to process large volumes of text without exhausting memory. It shares most of its core arguments with `chunk` (like `max_sentences`, `max_tokens`, `lang`, `overlap_percent`, `offset`, and `token_counter`), but introduces additional parameters to manage batch processing.

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