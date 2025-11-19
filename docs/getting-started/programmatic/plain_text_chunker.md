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

| Constraint           | Value Requirement | Description |
| :------------------- | :---------------- | :---------- |
| `max_sentences`      | `int >= 1`        | This constraint is all about sentence power! You tell Chunklet how many sentences you want per chunk, and it gracefully groups them together, making sure your ideas flow smoothly from one chunk to the next. |
| `max_tokens`         | `int >= 12`       | Got a strict token budget? This constraint is your best friend! Chunklet carefully adds sentences to your chunk, keeping a watchful eye on the token limit. If a sentence is a bit too chatty, it'll even politely split it at clause boundaries to keep everything perfectly snug. |
| `max_section_breaks` | `int >= 1`        | Perfect for structured documents! This constraint lets you limit the number of Markdown-style section breaks (like headings `##` or horizontal rules `---`) in each chunk. It's a fantastic way to keep your document's structure intact while chunking. |

The `PlainTextChunker` has two main methods: `chunk` for processing a single text and `batch_chunk` for processing multiple texts. Both methods return a generator that yields a [`Box`](https://pypi.org/project/python-box/#:~:text=Overview,strings%20or%20files.) object for each chunk. The `Box` object has two main keys: `content` (str) and `metadata` (dict). For detailed information about metadata structure and usage, see the [Metadata guide](../metadata.md#plaintextchunker-metadata).

!!! note "Constraint Requirement"
    At least one limit mode (e.g., `max_sentences`, `max_tokens`, or `max_section_breaks`) must be provided when calling `chunk` or `batch_chunk`. Failing to specify any limit mode will result in an [`InvalidInputError`](../../exceptions-and-warnings.md#invalidinputerror).

## Single Run

Given the following text for our examples:

```py
text = """
# Introduction to Chunking

This is the first paragraph of our document. It discusses the importance of text segmentation for various NLP tasks, such as RAG systems and summarization. We aim to break down large documents into manageable, context-rich pieces.

## Why is Chunking Important?

Effective chunking helps in maintaining the semantic coherence of information. It ensures that each piece of text retains enough context to be meaningful on its own, which is crucial for downstream applications.

### Different Strategies

There are several strategies for chunking, including splitting by sentences, by a fixed number of tokens, or by structural elements like headings. Each method has its own advantages depending on the specific use case.

---

## Advanced Chunking Techniques

Beyond basic splitting, advanced techniques involve understanding the document's structure. For instance, preserving section breaks can significantly improve the quality of chunks for hierarchical documents. This section will delve into such methods.

### Overlap Considerations

To ensure smooth transitions between chunks, an overlap mechanism is often employed. This means that a portion of the previous chunk is included in the beginning of the next, providing continuity.

---

# Conclusion

In conclusion, mastering chunking is key to unlocking the full potential of your text data. Experiment with different constraints to find the optimal strategy for your needs.
"""
```

### Chunking by Sentences

Here's how you can use `PlainTextChunker` to chunk text by the number of sentences:

```py
from chunklet.plain_text_chunker import PlainTextChunker

chunker = PlainTextChunker()  # (1)!

chunks = chunker.chunk(
    text=text,
    lang="auto",             # (2)!
    max_sentences=2,
    overlap_percent=0,       # (3)!
    offset=0                 # (4)!
)

for i, chunk in enumerate(chunks):
    print(f"--- Chunk {i+1} ---")
    print(f"Metadata: {chunk.metadata}")
    print(f"Content: {chunk.content}")
    print()
```

1.  Setting `verbose=True` enables detailed logging, which is `False` by default, showing internal processes like language detection.
2.  Instructs the chunker to automatically detect the language of the input text. While convenient, explicitly setting the language (e.g., `lang="en"`) can improve accuracy and performance for known languages.
3.  Configures the chunker to have no overlap between consecutive chunks. The default behavior includes a 20% overlap to maintain context across chunks.
4.  Specifies that chunking should start from the very beginning of the text (the first sentence). The default is 0.

??? success "Click to show output"
    ```linenums="0"
    --- Chunk 1 ---
    Metadata: {'chunk_num': 1, 'span': (0, 73)}
    Content: # Introduction to Chunking
    This is the first paragraph of our document.

    --- Chunk 2 ---
    Metadata: {'chunk_num': 2, 'span': (74, 259)}
    Content: It discusses the importance of text segmentation for various NLP tasks, such as RAG systems and summarization.
    We aim to break down large documents into manageable, context-rich pieces.

    --- Chunk 3 ---
    Metadata: {'chunk_num': 3, 'span': (260, 370)}
    Content: ## Why is Chunking Important?
    Effective chunking helps in maintaining the semantic coherence of information.

    --- Chunk 4 ---
    Metadata: {'chunk_num': 4, 'span': (371, 529)}
    Content: It ensures that each piece of text retains enough context to be meaningful on its own, which is crucial for downstream applications.

    ### Different Strategies

    --- Chunk 5 ---
    Metadata: {'chunk_num': 5, 'span': (531, 748)}
    Content: There are several strategies for chunking, including splitting by sentences, by a fixed number of tokens, or by structural elements like headings.
    Each method has its own advantages depending on the specific use case.

    --- Chunk 6 ---
    Metadata: {'chunk_num': 6, 'span': (749, 786)}
    Content: ---

    ## Advanced Chunking Techniques

    --- Chunk 7 ---
    Metadata: {'chunk_num': 7, 'span': (788, 995)}
    Content: Beyond basic splitting, advanced techniques involve understanding the document's structure.
    For instance, preserving section breaks can significantly improve the quality of chunks for hierarchical documents.

    --- Chunk 8 ---
    Metadata: {'chunk_num': 8, 'span': (996, 1066)}
    Content: This section will delve into such methods.

    ### Overlap Considerations

    --- Chunk 9 ---
    Metadata: {'chunk_num': 9, 'span': (1068, 1264)}
    Content: To ensure smooth transitions between chunks, an overlap mechanism is often employed.
    This means that a portion of the previous chunk is included in the beginning of the next, providing continuity.

    --- Chunk 10 ---
    Metadata: {'chunk_num': 10, 'span': (749, 763)}
    Content: ---

    # Conclusion

    --- Chunk 11 ---
    Metadata: {'chunk_num': 11, 'span': (1285, 1459)}
    Content: In conclusion, mastering chunking is key to unlocking the full potential of your text data.
    Experiment with different constraints to find the optimal strategy for your needs.
    ```

!!! tip "Enable Verbose Logging"
    To see detailed logging during the chunking process, you can set the `verbose` parameter to `True` when initializing the `DocumentChunker`:
    ```py
    chunker = PlainTextChunker(verbose=True)
    ```

### Chunking by Tokens

!!! note "Token Counter Requirement"
    When using the `max_tokens` constraint, a `token_counter` function is essential. This function, which you provide, should accept a string and return an integer representing its token count. Failing to provide a `token_counter` will result in a [`MissingTokenCounterError`](../../exceptions-and-warnings.md#missingtokencountererror).

#### Setup
```py
from chunklet.plain_text_chunker import PlainTextChunker

# Simple counter for demonstration purpose
def word_counter(text: str) -> int:
    return len(text.split())

chunker = PlainTextChunker(token_counter=word_counter)         # (1)!
```

1.  Initializes `PlainTextChunker` with a custom `word_counter` function. This function will be used to count tokens when `max_tokens` is used.

```py
chunks = chunker.chunk(
    text=text,
    lang="auto",
    max_tokens=12,
)

for i, chunk in enumerate(chunks):
    print(f"--- Chunk {i+1} ---")
    print(f"Content: {chunk.content}")
    print()
```

??? success "Click to show output"
    ```linenums="0"
    --- Chunk 1 ---
    Metadata: {'chunk_num': 1, 'span': (0, 291)}
    Content: # Introduction to Chunking
    This is the first paragraph of our document.
    It discusses the importance of text segmentation for various NLP tasks, such as RAG systems and summarization.
    We aim to break down large documents into manageable, context-rich pieces.

    ## Why is Chunking Important?

    --- Chunk 2 ---
    Metadata: {'chunk_num': 2, 'span': (256, 573)}
    Content: ...
    ## Why is Chunking Important?

    Effective chunking helps in maintaining the semantic coherence of information.
    It ensures that each piece of text retains enough context to be meaningful on its own, which is crucial for downstream applications.

    ### Different Strategies
    There are several strategies for chunking,

    --- Chunk 3 ---
    Metadata: {'chunk_num': 3, 'span': (531, 880)}
    Content: There are several strategies for chunking,
    including splitting by sentences, by a fixed number of tokens, or by structural elements like headings.
    Each method has its own advantages depending on the specific use case.

    ---

    ## Advanced Chunking Techniques
    Beyond basic splitting, advanced techniques involve understanding the document's structure.

    --- Chunk 4 ---
    Metadata: {'chunk_num': 4, 'span': (808, 1153)}
    Content: ... advanced techniques involve understanding the document's structure.

    For instance, preserving section breaks can significantly improve the quality of chunks for hierarchical documents.
    This section will delve into such methods.

    ### Overlap Considerations
    To ensure smooth transitions between chunks, an overlap mechanism is often employed.

    --- Chunk 5 ---
    Metadata: {'chunk_num': 5, 'span': (1109, 1377)}
    Content: ... an overlap mechanism is often employed.

    This means that a portion of the previous chunk is included in the beginning of the next, providing continuity.

    ---

    # Conclusion
    In conclusion, mastering chunking is key to unlocking the full potential of your text data.

    --- Chunk 6 ---
    Metadata: {'chunk_num': 6, 'span': (1296, 1459)}
    Content: ... mastering chunking is key to unlocking the full potential of your text data.

    Experiment with different constraints to find the optimal strategy for your needs.
    ```

!!! tip "Overrides token_counter"
    You can also provide the `token_counter` directly to the `chunk` method. within the `chunk` method call (e.g., `chunker.chunk(..., token_counter=my_tokenizer_function)`). If a `token_counter` is provided in both the constructor and the `chunk` method, the one in the `chunk` method will be used.

### Chunking by Section Breaks
This constraint is useful for documents structured with Markdown headings or thematic breaks.

```py
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
    ```linenums="0"
    --- Chunk 1 ---
    Metadata: {'chunk_num': 1, 'span': (0, 503)}
    Content: # Introduction to Chunking
    This is the first paragraph of our document.
    It discusses the importance of text segmentation for various NLP tasks, such as RAG systems and summarization.
    We aim to break down large documents into manageable, context-rich pieces.

    ## Why is Chunking Important?
    Effective chunking helps in maintaining the semantic coherence of information.
    It ensures that each piece of text retains enough context to be meaningful on its own, which is crucial for downstream applications.

    --- Chunk 2 ---
    Metadata: {'chunk_num': 2, 'span': (371, 753)}
    Content: It ensures that each piece of text retains enough context to be meaningful on its own,
    which is crucial for downstream applications.

    ### Different Strategies
    There are several strategies for chunking, including splitting by sentences, by a fixed number of tokens, or by structural elements like headings.
    Each method has its own advantages depending on the specific use case.

    ---

    --- Chunk 3 ---
    Metadata: {'chunk_num': 3, 'span': (678, 1038)}
    Content: Each method has its own advantages depending on the specific use case.

    ---

    ## Advanced Chunking Techniques
    Beyond basic splitting, advanced techniques involve understanding the document's structure.
    For instance, preserving section breaks can significantly improve the quality of chunks for hierarchical documents.
    This section will delve into such methods.

    --- Chunk 4 ---
    Metadata: {'chunk_num': 4, 'span': (890, 1269)}
    Content: ... preserving section breaks can significantly improve the quality of chunks for hierarchical documents.
    This section will delve into such methods.

    ### Overlap Considerations
    To ensure smooth transitions between chunks, an overlap mechanism is often employed.
    This means that a portion of the previous chunk is included in the beginning of the next, providing continuity.

    ---

    --- Chunk 5 ---
    Metadata: {'chunk_num': 5, 'span': (1239, 1459)}
    Content: ... providing continuity.

    ---

    # Conclusion
    In conclusion, mastering chunking is key to unlocking the full potential of your text data.
    Experiment with different constraints to find the optimal strategy for your needs.
    ```

!!! tip "Adding Base Metadata"
    You can pass a `base_metadata` dictionary to the `chunk` method. This metadata will be included in the `metadata` of each chunk. For example: `chunker.chunk(..., base_metadata={"source": "my_document.txt"})`. For more details on metadata structure and available fields, see the [Metadata guide](../metadata.md#plaintextchunker-metadata).

### Combining Multiple Constraints
The real power of `PlainTextChunker` comes from combining multiple constraints. This allows for highly specific and granular control over how your text is chunked. Here are a few examples of how you can combine different constraints.

!!! note "Token Counter Requirement"
    Remember, whenever you use the `max_tokens` constraint, you must provide a `token_counter` function.

#### By Sentences and Tokens
This is useful when you want to limit by both the number of sentences and the overall token count, whichever is reached first.

```py
chunks = chunker.chunk(
    text=text,
    max_sentences=5,
    max_tokens=100
)
```

#### By Sentences and Section Breaks
This combination is great for ensuring that chunks don't span across too many sections while also keeping the sentence count in check.

```py
chunks = chunker.chunk(
    text=text,
    max_sentences=10,
    max_section_breaks=2
)
```

#### By Tokens and Section Breaks
A powerful combination for structured documents where you want to respect section boundaries while adhering to a strict token budget.

```py
chunks = chunker.chunk(
    text=text,
    max_tokens=256,
    max_section_breaks=1
)
```

#### By Sentences, Tokens, and Section Breaks
For the ultimate level of control, you can combine all three constraints. The chunking will stop as soon as any of the three limits is reached.

```py
chunks = chunker.chunk(
    text=text,
    max_sentences=8,
    max_tokens=200,
    max_section_breaks=2
)
```
!!! tip "Customizing the Continuation Marker"
    You can customize the continuation marker, which is prepended to clauses that don't fit in the previous chunk. To do this, pass the `continuation_marker` parameter to the chunker's constructor.

    ```py
    chunker = PlainTextChunker(continuation_marker="[...]")
    ```

    If you don't want any continuation marker, you can set it to an empty string:

    ```py
    chunker = PlainTextChunker(continuation_marker="")
    ```

## Batch Run

While the `chunk` method is perfect for processing a single text, the `batch_chunk` method is designed for efficiently processing multiple texts in parallel. It returns a generator, allowing you to process large volumes of text without exhausting memory. It shares most of its core arguments with `chunk` (like `max_sentences`, `max_tokens`, `lang`, `overlap_percent`, `offset`, and `token_counter`), but introduces additional parameters to manage batch processing.

Here's an example of how to use `batch_chunk`:

```py
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
    ```linenums="0"
      0%|                                              | 0/3 [00:00<?, ?it/s]
    --- Chunk 1 ---
    Metadata: {'chunk_num': 1, 'span': (0, 97)}
    Content: This is the first document.
    It has multiple sentences for chunking.
    Here is the second document.

    --- Chunk 2 ---
    Metadata: {'chunk_num': 2, 'span': (96, 202)}
    Content: It is a bit longer to test batch processing effectively.
    And this is the third document.
    Short and sweet,

    --- Chunk 3 ---
    Metadata: {'chunk_num': 3, 'span': (186, 253)}
    Content: Short and sweet,
    but still part of the batch.
    The fourth document.

    --- Chunk 4 ---
    Metadata: {'chunk_num': 4, 'span': (252, 311)}
    Content: Another one to add to the collection for testing purposes.

    --- Chunk 5 ---
    Metadata: {'chunk_num': 1, 'span': (0, 118)}
    Content: Este es el primer documento.
    Contiene varias frases para la segmentación de texto.
    El segundo ejemplo es más extenso.

    --- Chunk 6 ---
    Metadata: {'chunk_num': 2, 'span': (117, 173)}
    Content: Queremos probar el procesamiento en diferentes idiomas.

    Chunking ...: 67%|█████████████████████████▎            | 2/3 [00:00, 10.09it/s]
    --- Chunk 7 ---
    Metadata: {'chunk_num': 1, 'span': (0, 125)}
    Content: Ceci est le premier document.
    Il est essentiel pour l'évaluation multilingue.
    Le deuxième document est court mais important.

    --- Chunk 8 ---
    Metadata: {'chunk_num': 2, 'span': (125, 149)}
    Content: La variation est la clé.

    Chunking ...: 100%|████████████████████████████████████████| 2/2 [00:00, 19.88it/s]
    ```

!!! warning "Generator Cleanup"
    When using `batch_chunk`, it's crucial to ensure the generator is properly closed, especially if you don't iterate through all the chunks. This is necessary to release the underlying multiprocessing resources. The recommended way is to use a `try...finally` block to call `close()` on the generator. For more details, see the [Troubleshooting](../../troubleshooting.md) guide.

!!! tip "Adding Base Metadata to Batches"
    Just like with the `chunk` method, you can pass a `base_metadata` dictionary to `batch_chunk`. This is useful for adding common information, like a source filename, to all chunks processed in the batch. For more details on metadata structure and available fields, see the [Metadata guide](../metadata.md#plaintextchunker-metadata).

### Separator

The `separator` parameter allows you to specify a custom value to be yielded after all chunks for a given text have been processed. This is particularly useful when processing multiple texts in a batch, as it helps to clearly distinguish between the chunks originating from different input texts in the output stream.

!!! note "note"
    `None` cannot be used as a separator.

```py
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
    ```linenums="0"
    --- Chunks for Document 1 ---
    Content: This is the first document.
    Metadata: {'chunk_num': 1, 'span': (0, 27)}
    Content: It has two sentences.
    Metadata: {'chunk_num': 2, 'span': (28, 49)}

    --- Chunks for Document 2 ---
    Content: This is the second document.
    Metadata: {'chunk_num': 1, 'span': (0, 28)}
    Content: It also has two sentences.
    Metadata: {'chunk_num': 2, 'span': (29, 55)}
    ```

??? info "API Reference"
    For a deep dive into the `PlainTextChunker` class, its methods, and all the nitty-gritty details, check out the full [API documentation](../../reference/chunklet/plain_text_chunker.md).````
