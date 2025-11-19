# Document Chunker

<p align="center">
  <img src="../../img/document_chunker.jpeg" alt="Document Chunker" width="300"/>
</p>

!!! note "Psst... Read `PlainTextChunker` First!"
    Think of `DocumentChunker` as the cool, sophisticated older sibling of `PlainTextChunker`. While `DocumentChunker` knows how to handle all sorts of fancy file formats, the real brains of the chunking operation—the part that does the heavy lifting of splitting text by sentences, tokens, and section breaks—lives inside `PlainTextChunker`.

    So, before you dive in here, do yourself a favor and get cozy with the [PlainTextChunker documentation](plain_text_chunker.md) first. It’s the key to unlocking the full power of chunking! We’ll cover the awesome document-specific stuff here, but the core concepts are all explained over there.

## Streamlined Document Processing

Are you tired of managing multiple tools for different file types? The `DocumentChunker` offers a unified solution for processing a wide array of document formats. From PDFs and DOCX files to EPUBs and more, it handles diverse documents efficiently and elegantly.

Consider the `DocumentChunker` as the orchestrator of your document processing workflow. It intelligently identifies the file type, employs the appropriate specialist to extract and convert the text (often to Markdown if possible), and then seamlessly passes the processed content to the `PlainTextChunker` for further segmentation. This provides a smooth, end-to-end solution for transforming your documents into clean, chunked data.

Ready to simplify your document processing? Let's explore how!

### What's in the Magic Bag?

The `DocumentChunker` comes with a bag of tricks that makes document processing a breeze:

-  **Multi-Format Mastery:** From the corporate world of DOCX to the academic realm of PDFs, this chunker speaks a multitude of file languages. It can handle `.pdf`, `.docx`, `.epub`, `.txt`, `.tex`, `.html`, `.hml`, `.md`, `.rst`, and even `.rtf` files.
-  **Metadata Enrichment:** It's not just about the text. The `DocumentChunker` automatically enriches your chunks with valuable metadata, like the source file path and page numbers for PDFs.
-  **Bulk Processing Beast:** Got a whole folder of documents to process? No sweat. This chunker is built for bulk, efficiently processing multiple documents in a single go.
-  **Pluggable Processors:** Have a weird, esoteric file format that nobody else has heard of? The `DocumentChunker` is ready for the challenge. You can plug in your own custom processors to handle any file type you can throw at it.

The `DocumentChunker` has two main methods: `chunk` for processing a single file and `batch_chunk` for processing multiple files. Both methods return a generator that yields a [`Box`](https://pypi.org/project/python-box/#:~:text=Overview,strings%20or%20files.) object for each chunk. The `Box` object has two main keys: `content` (str) and `metadata` (dict).

!!! note "Supported Processors and Batch Processing"
    The `DocumentChunker` supports the following file types out-of-the-box:
    - `.docx`: Processed by `DocxProcessor`
    - `.epub`: Processed by `EpubProcessor`
    - `.pdf`: Processed by `PDFProcessor`

    These processors can also provide unique optional metadata, enriching your chunks with valuable context. For more details, check out the [Metadata in Chunklet-py documentation](../../getting-started/metadata.md#documentchunker-metadata).

    Due to the streaming nature of these processors (they yield content page by page or in blocks), it is highly recommended to use them with the `batch_chunk` method. Attempting to use these processors with the `chunk` method (which expects a single string input) will result in a [`FileProcessingError`](../../exceptions-and-warnings.md#fileprocessingerror) as the `chunk` method is not designed to consume the generator output of these processors.

## Single Run

The `chunk` method of `DocumentChunker` shares most of its arguments with `PlainTextChunker.chunk`. The key differences are:

*   The first argument is `path` (a string representing the file path or a `pathlib.Path` object) instead of `text`.
*   The `base_metadata` argument is not available, as metadata is automatically extracted and managed by the document processors.

Remember, just like with `PlainTextChunker`, at least one of `max_sentences`, `max_tokens`, or `max_section_breaks` must be provided to avoid an [`InvalidInputError`](../../exceptions-and-warnings.md#invalidinputerror).

Let's say we have the following text content:

```txt
The quick brown fox jumps over the lazy dog. This is the first sentence, and it's a classic.
Here is the second sentence, which is a bit longer and more descriptive. And this is the third one, short and sweet.
The fourth sentence concludes our initial example, but we need more text to demonstrate the chunking effectively.
Let's add a fifth sentence to make the text a bit more substantial. The sixth sentence will provide even more content for our test.
This is the seventh sentence, and we are still going. The eighth sentence is here to make the text even longer.
Finally, the ninth sentence will be the last one for this example, making sure we have enough content to create multiple chunks.
```

Save this content into a file named `sample_text.txt`. Here's how you would use it with `DocumentChunker`:

```py
from chunklet.document_chunker import DocumentChunker

# Assuming sample_text.txt is in the same directory as your script
file_path = "sample_text.txt"

chunker = DocumentChunker()

chunks = chunker.chunk(
    path=file_path,
    lang="auto",             # (1)!
    max_sentences=4,         # (2)!
    overlap_percent=0,       # (3)!
    offset=0                 # (4)!
)

for i, chunk in enumerate(chunks):
    print(f"--- Chunk {i+1} ---")
    print(f"Metadata: {chunk.metadata}")
    print(f"Content: {chunk.content}")
    print()
```

1.  Instructs the chunker to automatically detect the language of the input text. While convenient, explicitly setting the language (e.g., `lang="en"`) can improve accuracy and performance for known languages.
2.  Sets the maximum number of sentences allowed per chunk. In this example, chunks will contain at most four sentences.
3.  Configures the chunker to have no overlap between consecutive chunks. The default behavior includes a 20% overlap to maintain context across chunks.
4.  Specifies that chunking should start from the very beginning of the text (the first sentence). The default is 0.

??? success "Click to show output"
    ```linenums="0"
    --- Chunk 1 ---
    Metadata: {'source': 'sample_text.txt', 'chunk_num': 1, 'span': (0, 209)}
    Content: The quick brown fox jumps over the lazy dog.
    This is the first sentence, and it's a classic.
    Here is the second sentence, which is a bit longer and more descriptive.
    And this is the third one, short and sweet.

    --- Chunk 2 ---
    Metadata: {'source': 'sample_text.txt', 'chunk_num': 2, 'span': (210, 509)}
    Content: The fourth sentence concludes our initial example, but we need more text to demonstrate the chunking effectively.
    Let's add a fifth sentence to make the text a bit more substantial.
    The sixth sentence will provide even more content for our test.
    This is the seventh sentence, and we are still going.

    --- Chunk 3 ---
    Metadata: {'source': 'sample_text.txt', 'chunk_num': 3, 'span': (510, 696)}
    Content: The eighth sentence is here to make the text even longer.
    Finally, the ninth sentence will be the last one for this example, making sure we have enough content to create multiple chunks.
    ```

!!! tip "Enable Verbose Logging"
    To see detailed logging during the chunking process, you can set the `verbose` parameter to `True` when initializing the `DocumentChunker`:
    ```py
    chunker = DocumentChunker(verbose=True)
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

## Batch Run

While the `chunk` method is perfect for processing a single document, the `batch_chunk` method is designed for efficiently processing multiple documents in parallel. It returns a generator, allowing you to process large volumes of documents without exhausting memory.

The `batch_chunk` method shares most of its core arguments with `PlainTextChunker.batch_chunk` (like `lang`, `max_tokens`, `max_sentences`, `max_section_breaks`, `overlap_percent`, `offset`, `token_counter`, `separator`, `n_jobs`, `show_progress`, and `on_errors`). The key differences are:

*   The first argument is `paths` (a list of strings or `pathlib.Path` objects representing the file paths) instead of `texts`.
*   The `base_metadata` argument is not available, as metadata is automatically extracted and managed by the document processors.

For this example, we'll be using some sample files from our repository's [samples directory](https://github.com/speedyk-005/chunklet-py/tree/main/samples).

```py
from chunklet.document_chunker import DocumentChunker

def word_counter(text: str) -> int:
    return len(text.split())

paths = [
    "samples/Lorem Ipsum.docx",
    "samples/What_is_rst.rst",
    "samples/minimal.epub",
    "samples/sample-pdf-a4-size.pdf",
]                                     # (1)!

chunker = DocumentChunker(token_counter=word_counter) # (2)!

chunks_generator = chunker.batch_chunk(
    paths=paths,
    overlap_percent=30,
    max_sentences=12,
    max_tokens=256,
    max_section_breaks=1,
    n_jobs=2,                    # (3)!
    on_errors="raise",           # (4)!
    show_progress=False,         # (5)!
)

for i, chunk in enumerate(chunks_generator):
    if i == 10:                      # (6)!
        break

    print(f"--- Chunk {i+1} ---")
    print(f"Content:\n{chunk.content}\n")
    print(f"Metadata:")
    for k, v in chunk.metadata.items():
        print(f" | {k}: {v}")

    print()

chunks_generator.close()          # (7)!
print("\nAnd so on...")
```

1.  If your files are saved elsewhere make sure to update that accoordingly.
2.  Initializes the `DocumentChunker` with a `token_counter` function. This is crucial when using `max_tokens` for chunking.
3.  Specifies the number of parallel processes to use for chunking. The default value is `None` (use all available CPU cores).
4.  Define how to handle errors during processing. Determines how errors during chunking are handled. If set to `"raise"` (default), an exception will be raised immediately. If set to `"break"`, the process will be halt and partial result will be returned.
 If set to `"ignore"`, errors will be silently ignored.
5.  Display a progress bar during batch processing. The default value is `False`.
6.  We break the loop early to demonstrate the cleanup mechanism.
7.  Explicitly close the generator to ensure proper cleanup.

??? success "Click to show output"
    ```linenums="0"
    --- Chunk 1 ---
    Content:
    Quantum Aristoxeni ingenium consumptum videmus in musicis?
    Lorem ipsum dolor sit amet, consectetur adipiscing elit.
    Quid nunc honeste dicit?
    Tum Torquatus: Prorsus, inquit, assentior; Duo Reges: constructio interrete.
    Iam in altera philosophiae parte.
    Sed haec omittamus; Haec para/doca illi, nos admirabilia dicamus.
    Nihil sane.
    **Expressa vero in iis aetatibus, quae iam confirmatae sunt.**
    Sit sane ista voluptas.
    Non quam nostram quidem, inquit Pomponius iocans; An tu me de L.
    Sed haec omittamus; Cave putes quicquam esse verius.
    [Image - 1]

    Metadata:
     chunk_num: 1
     span: (-1, -1)
     source: samples/Lorem Ipsum.docx
     author: train11
     last_modified_by: Microsoft Office User
     created: 2012-08-07 08:50:00+00:00
     modified: 2019-12-05 23:29:00+00:00
     section_count: 1
     curr_section: 1

    --- Chunk 2 ---
    Content:
    xml version="1.0" encoding="utf-8"?
    ReStructuredText (rst): plain text markup
    ReStructuredText (rst): plain text markup=====
    [The tiny table of contents](#top)
    * [1   What is reStructuredText?](#what-is-restructuredtext)
    * [2   What is it good for?](#what-is-it-good-for)
    * [3   Show me some formatting examples](#show-me-some-formatting-examples)
    * [4   Where can I learn more?](#where-can-i-learn-more)
    * [5   Show me some more stuff, please](#show-me-some-more-stuff-please)
    [1   What is reStructuredText?](#toc-entry-1)=====
    An easy-to-read, what-you-see-is-what-you-get plaintext markup syntax
    and parser system, abbreviated *rst*.

    Metadata:
     chunk_num: 1
     span: (-1, -1)
     source: samples/What_is_rst.rst
     section_count: 1
     curr_section: 1

    --- Chunk 3 ---
    Content:
    An easy-to-read,
    what-you-see-is-what-you-get plaintext markup syntax
    and parser system,
    abbreviated *rst*.
    In other words, using a simple
    text editor, documents can be created which
    * are easy to read in text editor and
    * can be *automatically* converted to
    + html and
    + latex (and therefore pdf)
    [2   What is it good for?](#toc-entry-2)=====
    reStructuredText can be used, for example, to

    Metadata:
     chunk_num: 2
     span: (-1, -1)
     source: samples/What_is_rst.rst
     section_count: 1
     curr_section: 2

    --- Chunk 4 ---
    Content:
    ... + latex (and therefore pdf)
    [2   What is it good for?](#toc-entry-2)=====
    reStructuredText can be used,
    for example,
    to
    * write technical documentation (so that it can easily be offered as a
    pdf file or a web page)
    * create html webpages without knowing html
    * to document source code
    [3   Show me some formatting examples](#toc-entry-3)=====
    You can highlight text in *italics* or, to provide even more emphasis
    in **bold**.

    Metadata:
     chunk_num: 3
     span: (-1, -1)
     source: samples/What_is_rst.rst
     section_count: 1
     curr_section: 3

    --- Chunk 5 ---
    Content:
    ... [3   Show me some formatting examples](#toc-entry-3)=====
    You can highlight text in *italics* or,
    to provide even more emphasis
    in **bold**.
    Often, when describing computer code, we like to use a
    fixed space font to quote code snippets.
    We can also include footnotes [[1]](#footnote-1).
    We could include source code files
    (by specifying their name) which is useful when documenting code.
    We
    can also copy source code verbatim (i.e. include it in the rst
    document) like this:```

    Metadata:
     chunk_num: 4
     span: (-1, -1)
     source: samples/What_is_rst.rst
     section_count: 1
     curr_section: 4

    --- Chunk 6 ---
    Content:
    ... which is useful when documenting code.
    We
    can also copy source code verbatim (i.e. include it in the rst
    document)
    like this:```
    int main ( int argc, char *argv[] ) {
    printf("Hello World\n");
    return 0;}```
    We have already seen at itemised list in section [What is it good
    for?
    ](#what-is-it-good-for).
    Enumerated list and descriptive lists are supported as

    Metadata:
     chunk_num: 5
     span: (-1, -1)
     source: samples/What_is_rst.rst
     section_count: 1
     curr_section: 5

    --- Chunk 7 ---
    Content:
    We have already seen at itemised list in section [What is it good
    for?
    ](#what-is-it-good-for).
    Enumerated list and descriptive lists are supported as
    well.
    It provides very good support for including html-links in a
    variety of ways.
    Any section and subsections defined can be linked to,
    as well.
    [4   Where can I learn more?](#toc-entry-4)=====
    reStructuredText is described at
    <http://docutils.sourceforge.net/rst.html>.

    Metadata:
     chunk_num: 6
     span: (-1, -1)
     source: samples/What_is_rst.rst
     section_count: 1
     curr_section: 6

    --- Chunk 8 ---
    Content:
    ... as well.
    [4   Where can I learn more?](#toc-entry-4)=====
    reStructuredText is described at
    <http://docutils.sourceforge.net/rst.html>.
    We provide some geeky small
    print in this footnote [[2]](#footnote-2).
    [5   Show me some more stuff, please](#toc-entry-5)=====
    We can also include figures:
    ![image.png](image.png)
    The magnetisation in a small ferromagnetic disk.
    The diametre is of the order of 120 nanometers and the material is Ni20Fe
    80.
    Png is a file format that is both acceptable for html pages as well as fo
    r (pdf)latex.

    Metadata:
     chunk_num: 7
     span: (-1, -1)
     source: samples/What_is_rst.rst
     section_count: 1
     curr_section: 7

    --- Chunk 9 ---
    Content:
    ... ![image.png](image.png)
    The magnetisation in a small ferromagnetic disk.
    The diametre is of the order of 120 nanometers and the material is Ni20Fe
    80.
    Png is a file format that is both acceptable for html pages as well as fo
    r (pdf)latex.

    ---
    |  |  |
    | --- | --- |
    | [[1]](#footnote-reference-1) | although there isn't much point of using
     a footnote here.|
    |  |  |
    | --- | --- |
    | [[2]](#footnote-reference-2) | Random facts:   * Emacs provides an rst
     mode * when converting rst to html, a style sheet can be provided (there
     is a similar feature for latex) * rst can also be converted into XML * th
    e recommended file extension for rst is .txt |

    Metadata:
     chunk_num: 8
     span: (2499, 3150)
     source: samples/What_is_rst.rst
     section_count: 1
     curr_section: 8

    --- Chunk 10 ---
    Content:
    Table of Contents=====
    1. [Chapter 1](chapter_1.xhtml)
    2. [Chapter 2](chapter_2.xhtml)
    3. [Copyright](copyright.xhtml)

    Metadata:
     chunk_num: 1
     span: (-1, -1)
     source: samples/minimal.epub
     title: Sample .epub Book
     creator: Thomas Hansen
     section_count: 4
     curr_section: 1

    And so on...
    ```

!!! warning "Generator Cleanup"
    When using `batch_chunk`, it's crucial to ensure the generator is properly closed, especially if you don't iterate through all the chunks. This is necessary to release the underlying multiprocessing resources. The recommended way is to use a `try...finally` block to call `close()` on the generator. For more details, see the [Troubleshooting](../../troubleshooting.md) guide.

!!! note "Token Counter Requirement"
    When using the `max_tokens` constraint, a `token_counter` function is essential. This function, which you provide, should accept a string and return an integer representing its token count. Failing to provide a `token_counter` will result in a [`MissingTokenCounterError`](../../exceptions-and-warnings.md#missingtokencountererror).

!!! tip "Overrides token_counter"
    You can also provide the `token_counter` directly to the `chunk` method. within the `chunk` method call (e.g., `chunker.chunk(..., token_counter=my_tokenizer_function)`). If a `token_counter` is provided in both the constructor and the `chunk` method, the one in the `chunk` method will be used.
### Separator

The `separator` parameter is also available in `DocumentChunker`. It is used to yield a custom value after all chunks for a given document have been processed, which is useful for distinguishing between documents in a batch run.

Since the functionality is very similar to the `PlainTextChunker`, please refer to the [PlainTextChunker documentation](plain_text_chunker.md#separator) for a detailed explanation and code examples.

## Custom Processors

You can provide your own custom document processors to `DocumentChunker`. This is useful if you have a specialized processor for a particular file type that you want to prioritize over `DocumentChunker`'s built-in processors.

!!! warning "Global Registry: Be Mindful of Side Effects"
    Custom processors are registered globally. This means that once you register a processor, it's available everywhere in your application. Be mindful of potential side effects if you're registering processors in different parts of your codebase, especially in multi-threaded or long-running applications.

To use a custom processor, you leverage the [`@registry.register`](../../reference/chunklet/document_chunker/registry.md) decorator. This decorator allows you to register your function for one or more file extensions directly. Your custom processor function must accept a single `file_path` parameter (str) and return a `tuple[str | list[str], dict]` containing extracted text (or list of texts for multi-section documents) and a metadata dictionary.

!!! important "Important constraints"
    - Your function must accept exactly one required parameter (the file path)
    - Optional parameters with default values are allowed
    - File extensions must start with a dot (e.g., `.json`, `.custom`)
    - Lambda functions are not supported unless you provide a `name` parameter
    - The metadata dictionary will be merged with common metadata (chunk_num, span, source)
    - For multi-section documents, return a list of strings - each will be processed as a separate section
    - If an error occurs during the document processing (e.g., an issue with the custom processor function), a [`CallbackError`](../../exceptions-and-warnings.md#callbackerror) will be raised

```py
import os
import re
import json
import tempfile
from chunklet.document_chunker import DocumentChunker, CustomProcessorRegistry


registry = CustomProcessorRegistry()

# Define a simple custom processor for .json files
@registry.register(".json", name="MyJSONProcessor")
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

    chunks = chunker.chunk(
        path=tmp_path,
        max_sentences=5,
    )

    for i, chunk in enumerate(chunks):
        print(f"--- Chunk {i+1} ---")
        print(f"Content:\n{chunk.content}\n")
        print(f"Metadata:\n{chunk.metadata}")
        print()

# Optionally unregister
registry.unregister(".json")
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
    If you prefer not to use decorators, you can directly use the `registry.register()` method. This is particularly useful when registering processors dynamically.

    ```py
    from chunklet.document_chunker import CustomProcessorRegistry

    registry = CustomProcessorRegistry()

    def my_other_processor(file_path: str) -> tuple[str, dict]:
        # ... your logic ...
        return "some text", {"source": file_path}

    registry.register(my_other_processor, ".custom", name="MyOtherProcessor")
    ```

### [`CustomProcessorRegistry`](../../reference/chunklet/document_chunker/registry.md) Methods Summary

*   `processors`: Returns a shallow copy of the dictionary of registered processors.
*   `is_registered(ext: str)`: Checks if a processor is registered for the given file extension, returning `True` or `False`.
*   `register(callback: Callable[[str], ReturnType] | None = None, *exts: str, name: str | None = None)`: Registers a processor callback for one or more file extensions.
*   `unregister(*exts: str)`: Removes processor(s) from the registry.
*   `clear()`: Clears all registered processors from the registry.
*   `extract_data(file_path: str, ext: str)`: Processes a file using a registered processor, returning the extracted data and the name of the processor used.

??? info "API Reference"
    For a deep dive into the `DocumentChunker` class, its methods, and all the nitty-gritty details, check out the full [API documentation](../../reference/chunklet/document_chunker/document_chunker.md).
