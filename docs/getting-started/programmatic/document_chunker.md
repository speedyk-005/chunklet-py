# Document Chunker

<p align="center">
  <img src="../../../img/document_chunker.jpg" alt="Document Chunker" width="512"/>
</p>

## Quick Install

```bash
pip install chunklet-py
```

No extra dependencies needed - `DocumentChunker` is ready to roll right out of the box for plain text! 🚀

For document processing (PDFs, DOCX, EPUB, ODT, Excel, etc.), install the structured-document extra:

```bash
pip install chunklet-py[structured-document]
```

This installs all the document processing dependencies needed to handle PDFs, DOCX, EPUB, ODT, Excel, and more! 📚

## Taming Your Text and Documents with Precision

Got a wall of text that's overwhelming? The `DocumentChunker` transforms unruly paragraphs into perfectly sized, context-aware chunks. Perfect for RAG systems and document analysis.

It preserves meaning and flow — no confusing puzzle pieces.

### Where `DocumentChunker` Really Shines

The `DocumentChunker` comes packed with smart features that make it your go-to text wrangling sidekick:

-  **Flexible Composable Constraints:** Ultimate control over your chunks! Mix and match limits based on sentences, tokens, or section breaks (headings, horizontal rules, `<details>` tags). Craft exactly the chunk size you need with precision control! 🎯
-  **Intelligent Overlap:** Adds smart overlaps between chunks so your text flows smoothly. No more jarring transitions that leave readers scratching their heads!
-  **Extensive Multilingual Support:** Speaks over 50 languages fluently, thanks to our trusty sentence splitter. Global domination through better text chunking! 🌍
-  **Customizable Token Counting:** Plug in your own token counter for perfect alignment with different LLMs. Because one size definitely doesn't fit all models!
-  **Memory-Conscious Operation:** Handles massive documents efficiently by yielding chunks one at a time. Your RAM will thank you later! 💾
-  **Multi-Format Maestro:** From corporate DOCX boardrooms to academic PDF libraries, this chunker speaks every file language fluently! Handles `.pdf`, `.docx`, `.epub`, `.txt`, `.tex`, `.html`, `.hml`, `.md`, `.rst`, `.rtf`, `.odt`, `.csv`, and `.xlsx` files like a pro. 🌍
-  **Metadata Magician:** Not just text - it automatically enriches your chunks with valuable metadata. Your chunks come with bonus context! 📊
-  **Bulk Processing Powerhouse:** Got a mountain of documents to conquer? No problem! This powerhouse efficiently processes multiple documents in parallel. 📚⚡
-  **Pluggable Processor Power:** Have a mysterious file format that's one-of-a-kind? Plug in your own custom processors - `DocumentChunker` is ready for any challenge you throw at it! 🔌🛠️

!!! note "No Scanned PDF Support"
    Currently, `DocumentChunker` does **not** support scanned PDFs (images). It can only process PDFs with selectable/extractable text. For scanned documents, you'll need to OCR them first before chunking! 📷

### Composable Constraints: Your Text, Your Rules!

`DocumentChunker` lets you call the shots with composable constraints. Mix and match limits to craft the perfect chunk size for your needs. Here's the constraint menu:

| Constraint           | Value Requirement | Description |
| :------------------- | :---------------- | :---------- |
| `max_sentences`      | `int >= 1`        | Sentence power mode! Tell us how many sentences per chunk, and we'll group them thoughtfully so your ideas flow like a well-written story. |
| `max_tokens`         | `int >= 12`       | Token budget watcher! We'll carefully pack sentences into chunks while respecting your token limits. If a sentence gets too chatty, we'll politely split it at clause boundaries. 🤐 |
| `max_section_breaks` | `int >= 1`        | Structure superhero! Limits section breaks per chunk — headings (`##`), horizontal rules (`---`, `***`, `___`), and `<details>` tags. Your document structure stays intact! |

!!! note "Quick Note: Constraints Required!"
    You must specify at least one limit (`max_sentences`, `max_tokens`, or `max_section_breaks`) when using chunking methods. Forget to add one? You'll get an [`InvalidInputError`](../../exceptions-and-warnings.md#invalidinputerror)!

The `DocumentChunker` has four main methods: `chunk_text`, `chunk_file`, `chunk_texts`, and `chunk_files`. `chunk_text` and `chunk_file` return a list of [`Box`](https://pypi.org/project/python-box/) objects, while `chunk_texts` and `chunk_files` are memory-friendly generators that yield chunks one by one. Each `Box` has `content` (the actual text) and `metadata` (all the juicy details). Check the [Metadata guide](../metadata.md#documentchunker-metadata) for the full scoop!


## Single: Chunk One Text! 📝

Chunk a single string of text into manageable pieces using various constraints:
- `chunk_text()` - accepts raw text as a string
- `chunk_file()` - accepts a file path as a string or `pathlib.Path` object
  
### Chunking by Sentences: Sentence Group Guru! 📝

Let's say you have this text:

```text
# Introduction to Chunking

This is the first paragraph of our document. It discusses the importance of text segmentation for various NLP tasks, such as RAG systems and summarization. We aim to break down large documents into manageable, context-rich pieces.

## Why is Chunking Important?

Effective chunking helps in maintaining the semantic coherence of information. It ensures that each piece of text retains enough context to be meaningful on its own, which is crucial for downstream applications.

### Different Strategies

There are several strategies for chunking, including splitting by sentences, by a fixed number of tokens, or by structural elements like headings. Each method has its own advantages depending on the specific use case.

---

## Advanced Chunking Techniques

Ready to go beyond the basics? Let's explore some pro-level techniques!

### Overlap Considerations

Overlap is your secret weapon! It includes a bit of the previous chunk at the start of the next one, ensuring your text doesn't feel choppy or disconnected.

---

# Conclusion

In conclusion, mastering chunking is key to unlocking the full potential of your text data.
```

Now let's see how to chunk it:

```py linenums="1"
from chunklet.document_chunker import DocumentChunker

text = "..."  # The text from above

chunker = DocumentChunker()  # (1)!

chunks = chunker.chunk_text(
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

1.  Initialize `DocumentChunker` - no extra dependencies needed for plain text!
2.  `lang="auto"` lets us detect the language automatically. Super convenient, but specifying a known language like `lang="en"` can boost accuracy and speed.
3.  `overlap_percent=0` means no overlap between chunks. By default, we add 20% overlap to keep your text flowing smoothly across chunks.
4.  `offset=0` starts us from the very beginning of the text. (Zero-based indexing - because programmers love starting from zero!)

??? success "Click to show output"
    ```linenums="0"
    --- Chunk 1 ---
    Metadata: {'chunk_num': 1, 'span': (1, 73)}
    Content: # Introduction to Chunking
    This is the first paragraph of our document.

    --- Chunk 2 ---
    Metadata: {'chunk_num': 2, 'span': (74, 259)}
    Content: It discusses the importance of text segmentation for various NLP tasks, such as RAG systems and summarization.
    We aim to break down large documents into manageable, context-rich pieces.

    ## Why is Chunking Important?
    Effective chunking helps in maintaining the semantic coherence of information.

    --- Chunk 3 ---
    Metadata: {'chunk_num': 3, 'span': (261, 370)}
    Content: It ensures that each piece of text retains enough context to be meaningful on its own, which is crucial for downstream applications.

    ### Different Strategies

    --- Chunk 4 ---
    Metadata: {'chunk_num': 4, 'span': (371, 529)}
    Content: There are several strategies for chunking, including splitting by sentences, by a fixed number of tokens, or by structural elements like headings.
    Each method has its own advantages depending on the specific use case.

    --- Chunk 5 ---
    Metadata: {'chunk_num': 5, 'span': (531, 748)}
    Content: ---

    ## Advanced Chunking Techniques

    --- Chunk 6 ---
    Metadata: {'chunk_num': 6, 'span': (750, 787)}
    Content: Ready to go beyond the basics?
    Let's explore some pro-level techniques!

    --- Chunk 7 ---
    Metadata: {'chunk_num': 7, 'span': (788, 859)}
    Content: ### Overlap Considerations
    Overlap is your secret weapon!

    --- Chunk 8 ---
    Metadata: {'chunk_num': 8, 'span': (861, 919)}
    Content: ### Overlap Considerations
    Overlap is your secret weapon!

    --- Chunk 9 ---
    Metadata: {'chunk_num': 9, 'span': (920, 1050)}
    Content: It includes a bit of the previous chunk at the start of the next one, ensuring your text doesn't feel choppy or disconnected.

    ---

    --- Chunk 10 ---
    Metadata: {'chunk_num': 10, 'span': (1052, 1157)}
    Content: # Conclusion
    In conclusion, mastering chunking is key to unlocking the full potential of your text data.
    ```

### Chunking by Tokens: Token Budget Master! 🪙

!!! note "Token Counter Requirement"
    When using the `max_tokens` constraint, a `token_counter` function is essential. This function, which you provide, should accept a string and return an integer representing its token count. Failing to provide a `token_counter` will result in a [`MissingTokenCounterError`](../../exceptions-and-warnings.md#missingtokencountererror).

```py linenums="1" hl_lines="1 3-4 6 10"
from chunklet.document_chunker import DocumentChunker

def word_counter(text: str) -> int:
    return len(text.split())

chunker = DocumentChunker(token_counter=word_counter)

chunks = chunker.chunk_text(
    text=text,
    max_tokens=50,
)

for i, chunk in enumerate(chunks):
    print(f"--- Chunk {i+1} ---")
    print(f"Metadata: {chunk.metadata}")
    print(f"Content: {chunk.content}")
    print()
```

??? success "Click to show output"
    ```linenums="0"
    --- Chunk 1 ---
    Metadata: {'chunk_num': 1, 'span': (1, 290)}
    Content: # Introduction to Chunking
    This is the first paragraph of our document.
    It discusses the importance of text segmentation for various NLP tasks, such as RAG systems and summarization.
    We aim to break down large documents into manageable, context-rich pieces.

    ## Why is Chunking Important?

    --- Chunk 2 ---
    Metadata: {'chunk_num': 2, 'span': (261, 573)}
    Content: ... 
    ## Why is Chunking Important?

    Effective chunking helps in maintaining the semantic coherence of information.
    It ensures that each piece of text retains enough context to be meaningful on its own, which is crucial for downstream applications.

    ### Different Strategies
    There are several strategies for chunking,

    --- Chunk 3 ---
    Metadata: {'chunk_num': 3, 'span': (531, 859)}
    Content: There are several strategies for chunking,
    including splitting by sentences, by a fixed number of tokens, or by structural elements like headings.
    Each method has its own advantages depending on the specific use case.

    ---

    ## Advanced Chunking Techniques
    Ready to go beyond the basics?
    Let's explore some pro-level techniques!

    --- Chunk 4 ---
    Metadata: {'chunk_num': 4, 'span': (819, 1080)}
    Content: Let's explore some pro-level techniques!



    ### Overlap Considerations
    Overlap is your secret weapon!
    It includes a bit of the previous chunk at the start of the next one, ensuring your text doesn't feel choppy or disconnected.

    ---

    # Conclusion
    In conclusion,

    --- Chunk 5 ---
    Metadata: {'chunk_num': 5, 'span': (1052, 1157)}
    Content: ... 
    # Conclusion
    In conclusion,
    mastering chunking is key to unlocking the full potential of your text data.
    ```

!!! tip "Overrides token_counter"
    You can also provide the `token_counter` directly to any chunking method. If provided in both the constructor and the method, the one in the method will be used.

### Chunking by Section Breaks: Structure Superhero! 🦸‍♀️

This constraint is useful for documents structured with Markdown headings or thematic breaks.

``` py linenums="1" hl_lines="3"
chunks = chunker.chunk_text(
    text=text,
    max_section_breaks=2
)

for i, chunk in enumerate(chunks):
    print(f"--- Chunk {i+1} ---")
    print(f"Metadata: {chunk.metadata}")
    print(f"Content: {chunk.content}")
    print()
```

??? success "Click to show output"
    ```linenums="0"
    --- Chunk 1 ---
    Metadata: {'chunk_num': 1, 'span': (1, 503)}
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
    Metadata: {'chunk_num': 3, 'span': (678, 859)}
    Content: Each method has its own advantages depending on the specific use case.

    ---

    ## Advanced Chunking Techniques
    Ready to go beyond the basics?
    Let's explore some pro-level techniques!

    --- Chunk 4 ---
    Metadata: {'chunk_num': 4, 'span': (819, 1050)}
    Content: Let's explore some pro-level techniques!

    ### Overlap Considerations
    Overlap is your secret weapon!
    It includes a bit of the previous chunk at the start of the next one, ensuring your text doesn't feel choppy or disconnected.

    ---

    --- Chunk 5 ---
    Metadata: {'chunk_num': 5, 'span': (1047, 1157)}
    Content: ... 

    ---

    # Conclusion
    In conclusion, mastering chunking is key to unlocking the full potential of your text data.
    ```

### Combining Multiple Constraints: Mix and Match Magic! 🎭

The real power of `DocumentChunker` comes from combining multiple constraints. The chunking will stop as soon as any of the limits is reached.

``` py linenums="1" hl_lines="3-5"
chunks = chunker.chunk_text(
    text,
    max_sentences=5,
    max_tokens=100,
    max_section_breaks=2
)
```

!!! tip "Customizing the Continuation Marker"
    You can customize the continuation marker, which is prepended to clauses that don't fit in the previous chunk. To do this, pass the `continuation_marker` parameter to the chunker's constructor.

    ```py
    chunker = DocumentChunker(continuation_marker="[...]")
    ```

    If you don't want any continuation marker, you can set it to an empty string:

    ```py
    chunker = DocumentChunker(continuation_marker="")
    ```

!!! tip "Enable Verbose Logging"
    To see detailed logging during the chunking process, you can set the `verbose` parameter to `True` when initializing the `DocumentChunker`:
    ```py
    chunker = DocumentChunker(verbose=True)
    ```

!!! tip "Custom Sentence Splitter"
    You can provide a custom [`SentenceSplitter`](sentence_splitter.md) instance to `DocumentChunker` for specialized sentence splitting behavior. For more details, see the [Sentence Splitter documentation](sentence_splitter.md#custom-sentence-splitter).

!!! tip "Adding Base Metadata"
    You can pass a `base_metadata` dictionary to `chunk_text` and `chunk_texts`. This metadata will be included in each chunk. For example: `chunker.chunk_text(..., base_metadata={"source": "my_document.txt"})`. For more details, see the [Metadata guide](../metadata.md#documentchunker-metadata).


## Single File: Process One Document! 📄

While `chunk_text` is perfect for plain text, `chunk_file` handles document files. It supports the same constraints (max_sentences, max_tokens, max_section_breaks, etc.).

``` py linenums="1"
from chunklet.document_chunker import DocumentChunker

file_path = "sample_text.txt"

chunker = DocumentChunker()

chunks = chunker.chunk_file(
    path=file_path,
    lang="auto",
    max_sentences=4,
    overlap_percent=20,
    offset=0
)

for i, chunk in enumerate(chunks):
    print(f"--- Chunk {i+1} ---")
    print(f"Metadata: {chunk.metadata}")
    print(f"Content: {chunk.content}")
    print()
```

!!! note "Special Handling for Streaming Processors"
    Some processors work differently due to their streaming nature - they yield content page by page or in blocks rather than all at once. This means they require special care:

    **Streaming processors** (PDF, EPUB, DOCX, ODT): These beauties process content as they go, so they're designed for `chunk_files` method. Using them with `chunk_file` will throw a [`FileProcessingError`](../../exceptions-and-warnings.md#fileprocessingerror) since `chunk_file` expects all content upfront.

    **Regular processors** work fine with both `chunk_file` and `chunk_files` methods.


## Batch: Chunk Multiple Items! 📚

While `chunk_text` is perfect for single texts and `chunk_file` for single files, `chunk_texts` and `chunk_files` are your power players for processing multiple texts or files in parallel. They use memory-friendly generators so you can handle massive collections with ease.

- `chunk_texts()` - process multiple raw text strings
- `chunk_files()` - process multiple file paths

### For Texts

```py linenums="1" hl_lines="11-19"
from chunklet.document_chunker import DocumentChunker

def word_counter(text: str) -> int:
    return len(text.split())

EN_TEXT = "This is the first document. It has multiple sentences for chunking. Here is the second document."
ES_TEXT = "Este es el primer documento. Contiene varias frases para la segmentación de texto."

chunker = DocumentChunker(token_counter=word_counter)

chunks = chunker.chunk_texts(
    texts=[EN_TEXT, ES_TEXT],
    max_sentences=5,
    max_tokens=20,
    overlap_percent=30,
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
2.  Define how to handle errors during processing. If set to `"raise"` (default), an exception will be raised immediately. If set to `"break"`, the process will halt and partial result will be returned. If set to `"ignore"`, errors will be silently ignored.
3.  Display a progress bar during batch processing. The default value is `False`.

??? success "Click to show output"
    ```linenums="0"
    --- Chunk 1 ---
    Metadata: {'chunk_num': 1, 'span': (0, 82)}
    Content: Este es el primer documento.
    Contiene varias frases para la segmentación de texto.

    --- Chunk 2 ---
    Metadata: {'chunk_num': 2, 'span': (83, 196)}
    Content: El segundo ejemplo es más extenso para probar el procesamiento por lotes.
    La tercera oración añade más contenido.

    --- Chunk 3 ---
    Metadata: {'chunk_num': 3, 'span': (197, 236)}
    Content: Y la cuarta oración para mayor medida.

    --- Chunk 4 ---
    Metadata: {'chunk_num': 1, 'span': (0, 96)}
    Content: This is the first document.
    It has multiple sentences for chunking.
    Here is the second document.

    --- Chunk 5 ---
    Metadata: {'chunk_num': 2, 'span': (97, 201)}
    Content: It is a bit longer to test batch processing effectively.
    This is the third sentence to add more content.

    --- Chunk 6 ---
    Metadata: {'chunk_num': 3, 'span': (202, 294)}
    Content: And the fourth sentence for good measure.
    The fifth sentence makes it even more interesting.
    ```

### For Files

```py linenums="1"
PATHS = [
    "samples/document.pdf",
    "samples/document.docx",
]

chunks = chunker.chunk_files(PATHS, ...)
```

!!! warning "Generator Cleanup"
    When using `chunk_texts`, it's crucial to ensure the generator is properly closed, especially if you don't iterate through all the chunks. This is necessary to release the underlying multiprocessing resources. The recommended way is to use a `try...finally` block to call `close()` on the generator. For more details, see the [Troubleshooting](../../troubleshooting.md) guide.

### Separator: Keeping Your Batches Organized! 📋

The `separator` parameter works for both `chunk_texts` and `chunk_files`. It lets you add a custom marker that gets yielded after all chunks from a single input are processed. Super handy for batch processing when you want to clearly separate chunks from different source texts.

!!! note "Quick Note"
    `None` won't work as a separator - you'll need something more substantial!

```py linenums="1" hl_lines="2 9 14 18-21"
from chunklet.document_chunker import DocumentChunker
from more_itertools import split_at

chunker = DocumentChunker()
texts = [
    "This is the first document. It has two sentences.",
    "This is the second document. It also has two sentences."
]
custom_separator = "---END_OF_DOCUMENT---"

chunks_with_separators = chunker.chunk_texts(
    texts,
    max_sentences=1,
    separator=custom_separator,
    show_progress=False,
)

chunk_groups = split_at(chunks_with_separators, lambda x: x == custom_separator)
# Process the results using split_at
for i, doc_chunks in enumerate(chunk_groups):
    if doc_chunks:        # (1)!
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

### Custom processors: Build Your Own Document Wizards! 🛠️🔮

Want to handle exotic file formats that `DocumentChunker` doesn't know about? Create your own custom processors! This lets you add specialized processing for any file type and prioritize your custom processors over the built-in ones.

!!! warning "Global Registry Alert!"
    Custom processors get registered globally - once you add one, it's available everywhere in your app. Watch out for side effects if you're registering processors across different parts of your codebase, especially in multi-threaded or long-running applications!

To use a custom processor, you leverage the [`@custom_processor_registry.register`](../../reference/chunklet/document_chunker/registry.md) decorator. This decorator allows you to register your function for one or more file extensions directly. Your custom processor function must accept a single `file_path` parameter (str) and return a `tuple[str | list[str], dict]` containing extracted text (or list of texts for multi-section documents) and a metadata dictionary.

!!! important "Custom Processor Rules"
    - Your function must accept exactly one required parameter (the file path)
    - Optional parameters with defaults are totally fine
    - File extensions must start with a dot (like `.json`, `.custom`)
    - Lambda functions are not supported unless you provide a `name` parameter
    - The metadata dictionary will be merged with common metadata (chunk_num, span, source)
    - For multi-section documents, return a list of strings - each will be processed as a separate section
    - If an error occurs during the document processing (e.g., an issue with the custom processor function), a [`CallbackError`](../../exceptions-and-warnings.md#callbackerror) will be raised

```py linenums="1" hl_lines="5 8-18 52-53"
import os
import re
import json
import tempfile
from chunklet.document_chunker import DocumentChunker, custom_processor_registry


# Define a simple custom processor for .json files
@custom_processor_registry.register(".json", name="MyJSONProcessor")
def my_json_processor(file_path: str) -> tuple[str, dict]:
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Assuming the json has a "text" field with paragraphs
    text_content = "\n".join(data.get("text", []))
    metadata = data.get("metadata", {})
    metadata["source"] = file_path
    return text_content, metadata

# A longer and more complex JSON sample
json_data = {
    "metadata": {
        "document_id": "doc-12345",
        "created_at": "2025-11-05"
    },
    "text": [
        "This is the first paragraph of our longer JSON sample. It contains multiple sentences to test the chunking process.",
        "The second paragraph introduces a new topic. We are exploring the capabilities of custom processors in the chunklet library.",
        "Finally, the third paragraph concludes our sample. We hope this demonstrates the flexibility of the system in handling various data formats."
    ]
}

chunker = DocumentChunker()

# Use a temporary file
with tempfile.NamedTemporaryFile(mode='w+', suffix=".json") as tmp:
    json.dump(json_data, tmp)
    tmp.seek(0)
    tmp_path = tmp.name

    chunks = chunker.chunk_file(
        path=tmp_path,
        max_sentences=5,
    )

    for i, chunk in enumerate(chunks):
        print(f"--- Chunk {i+1} ---")
        print(f"Content:\n{chunk.content}\n")
        print(f"Metadata:\n{chunk.metadata}")
        print()

# Optionally unregister
custom_processor_registry.unregister(".json")
```

??? success "Click to show output"
    ```linenums="0"
    --- Chunk 1 ---
    Content:
    This is the first paragraph of our longer JSON sample.
    It contains multiple sentences to test the chunking process.
    The second paragraph introduces a new topic.
    We are exploring the capabilities of custom processors in the chunklet library.
    Finally, the third paragraph concludes our sample.

    Metadata:
    {'document_id': 'doc-12345', 'created_at': '2025-11-05', 'source': '/tmp/tmpdt6xa5rh.json', 'chunk_num': 1, 'span': (0, 292)}

    --- Chunk 2 ---
    Content:
    ... the third paragraph concludes our sample.

    Metadata:
    {'document_id': 'doc-12345', 'created_at': '2025-11-05', 'source': '/tmp/tmpdt6xa5rh.json', 'chunk_num': 2, 'span': (250, 292)}
    ```

!!! note "Registering Without the Decorator"
    If you prefer not to use decorators, you can directly use the `custom_processor_registry.register()` method. This is particularly useful when registering processors dynamically.

    ```py linenums="1"
    from chunklet.document_chunker import custom_processor_registry

    def my_other_processor(file_path: str) -> tuple[str, dict]:
        # ... your logic ...
        return "some text", {"source": file_path}

    custom_processor_registry.register(my_other_processor, ".custom", name="MyOtherProcessor")
    ```

### [`custom_processor_registry`](../../reference/chunklet/document_chunker/registry.md) Methods Summary

*   `processors`: Returns a shallow copy of the dictionary of registered processors.
*   `is_registered(ext: str)`: Checks if a processor is registered for the given file extension, returning `True` or `False`.
*   `register(callback: Callable[[str], ReturnType] | None = None, *exts: str, name: str | None = None)`: Registers a processor callback for one or more file extensions.
*   `unregister(*exts: str)`: Removes processor(s) from the registry.
*   `clear()`: Clears all registered processors from the registry.
*   `extract_data(file_path: str, ext: str)`: Processes a file using a registered processor, returning the extracted data and the name of the processor used.

??? info "API Reference"
    For complete technical details on the `DocumentChunker` class, check out the [API documentation](../../reference/chunklet/document_chunker/document_chunker.md).
