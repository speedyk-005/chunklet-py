# Metadata in Chunklet-py: Your Chunk's Story 📖

Ever wondered where your chunks come from and what makes them tick? 🤔 Chunklet-py's metadata system tells the whole story! Each chunk comes with rich contextual information about its origin, location, and characteristics. Think of metadata as your chunk's detailed biography - the who, what, when, and where of your text.

Every chunk is wrapped in a handy [`Box`](https://pypi.org/project/python-box/#:~:text=Overview,strings%_or_files.) object with a `metadata` attribute. This metadata dictionary is your treasure trove of chunk insights. Access it easily with dot notation (`chunk.metadata`) or dictionary-style (`chunk["metadata"]`) - your choice!

## Common Metadata: The Essentials 📋 {#common-metadata}

No matter which chunker you use, every chunk includes these fundamental metadata fields. Think of them as your chunk's basic information - the essentials you need to know.

*   **`chunk_num`** (int): Your chunk's sequential ID number within each source - perfect for keeping things organized
*   **`span`** (tuple[int, int]): Character position coordinates showing exactly where this chunk sits in the original text
*   **`source`** (str): Where did this chunk come from? (The origin story!)
     *   **File processing**: Absolute path to the file (for [DocumentChunker](programmatic/document_chunker.md) or [CodeChunker](programmatic/code_chunker.md))
     *   **CLI text input**: `"stdin"` (because it came from standard input)
     *   **Text input**: Only included if you provide it via `base_metadata` parameter
     *   **CodeChunker edge cases**: Might be `"N/A"` if the source can't be determined

## DocumentChunker Metadata: Rich & Detailed 📚 {#documentchunker-metadata}

The `DocumentChunker` provides comprehensive metadata for both text and file inputs. The metadata varies based on your input type - think of it as your chunk's detailed biography! 👇

### Text Input

Keeps things straightforward and clean. Your chunks include the essential [Common Metadata](#common-metadata) fields (`chunk_num` and `span`). No frills, just the basics - perfect when you want clean, minimal metadata without any extra baggage. Additional metadata can be provided via the `base_metadata` parameter.

### File Input

Need more context? File input's got you covered! Provides comprehensive metadata beyond the basics - revealing detailed insights about each file's properties and history:

**Universal Fields (for multi-section docs):**
*   **`section_count`** (int): Total number of sections in the document (pages, chapters, etc.)
*   **`curr_section`** (int): Which section this chunk belongs to

**File-Type Specific Information:**

*   **PDF Files:** Includes `title`, `author`, `creator`, `producer`, `publisher`, `created`, `modified`, and `page_count` fields (powered by pdfminer.six)
*   **EPUB Files:** Dublin Core metadata including `title`, `creator`, `contributor`, `publisher`, `date`, and `rights`
*   **DOCX Files:** Core properties like `title`, `author`, `publisher`, `last_modified_by`, `created`, `modified`, `rights`, and `version`

!!! tip "Safety First with Optional Fields!"
    These metadata fields are optional - not every document fills them out. Use `chunk.metadata.get("author")` instead of `chunk.metadata["author"]` to avoid `KeyError`s when a field is missing. Better safe than sorry! 😉

## CodeChunker Metadata: Code Intelligence 💻 {#codechunker-metadata}

The `CodeChunker` provides code-specific insights beyond basic metadata. It helps you understand the structural context of each chunk - perfect for tracking where your code elements originated! 🔍

**Code-Specific Information:**
*   **`tree`** (str): Abstract syntax tree representation showing structural relationships within the chunk
*   **`start_line`** (int): Line number where this chunk begins in the original file
*   **`end_line`** (int): Line number where this chunk ends in the original file

Automatically included in every `Box` object when chunking code, helping you understand which functions, classes, or code blocks are in each chunk.

## CLI Metadata Output: Command Line Insights 🖥️

The `chunklet` [CLI](../getting-started/cli.md) adapts metadata output based on your input type and flags. Think of it as your CLI's helpful companion that provides just the right context!

**Metadata Control:** The `--metadata` flag gives you control over what gets included.
*   **With `--metadata`**: Your chunks come with their full context - metadata appears alongside content, either printed to stdout or saved in `.json` files with `--destination`
*   **Without `--metadata`**: Just the chunk content - clean and simple when you want to focus purely on the text

**Metadata by Input Type:**

*   **Direct Text Input** (`chunklet chunk "Your text..."`): Uses `DocumentChunker` with essential [Common Metadata](#common-metadata) fields (`chunk_num`, `span`) and `source` set to `"stdin"`
*   **Document Processing** (`chunklet chunk --doc --source document.pdf`): `DocumentChunker` provides rich document metadata including [Common Metadata](#common-metadata) plus file-specific details (PDF titles, EPUB creators, DOCX authors) as detailed in [DocumentChunker Metadata](#documentchunker-metadata)
*   **Code Processing** (`chunklet chunk --code --source code.py`): `CodeChunker` includes structural information with [Common Metadata](#common-metadata) and code-specific fields like `tree`, `start_line`, `end_line` as described in [CodeChunker Metadata](#codechunker-metadata)

The CLI automatically provides the most relevant metadata for your use case - making chunk analysis both powerful and intuitive. Smart and simple! 🎯