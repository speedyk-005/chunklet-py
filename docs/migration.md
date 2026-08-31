# Migrating from v1 to v2: Everything Changed (But You'll Be Fine)

!!! warning "Python Version Bump"
    v2.x.x dropped Python 3.8, 3.9, and 3.10. Minimum is now **3.11**. Update your env if you're stuck on ancient Python.

### Automated migration checker

I wrote a script that scans your code for old v1 patterns. It'll point out exactly what needs changing.

```bash
curl -O https://raw.githubusercontent.com/speedyk-005/chunklet-py/main/audit_migration.py
python audit_migration.py /path/to/your/project
```

So you upgraded to v2 and things broke. That's normal. Let me walk you through what changed and how to fix it.

## The Breaking Stuff

Here's what blew up between v1 and v2:

### `Chunklet` is now `DocumentChunker`

I renamed the main class. Why? Because we now have two chunkers (`DocumentChunker` and `CodeChunker`), and calling one of them just "Chunklet" was confusing. Now the names actually make sense.

**Fix:**

=== "Before (v1.4.0)"

    ```py
    from chunklet import Chunklet
    
    chunker = Chunklet()
    ```

=== "After (v2.x.x)"

    ```py
    from chunklet import DocumentChunker
    
    chunker = DocumentChunker()
    ```

### `use_cache` is gone

I removed the `use_cache` flag. It was doing internal stuff that didn't need your attention anyway. Now caching just works without you having to think about it.

**Fix:** Delete `use_cache=False` from your calls.

=== "Before (v1.4.0)"

    ```py
    chunker = Chunklet()
    chunks = chunker.chunk(text, use_cache=False, ...)
    ```

=== "After (v2.x.x)"

    ```py
    chunker = DocumentChunker()
    chunks = chunker.chunk_text(text, ...)
    ```

### The `mode` argument is gone

This was confusing. Instead of saying `mode="sentence"` or `mode="hybrid"`, now you just pass the limits you want. Whatever you pass determines how it chunks. Simple.

**What's different:**
- No more `mode` parameter
- No more default values for `max_tokens` or `max_sentences` - you have to pick
- New toy: `max_section_breaks` lets you chunk by headings, horizontal rules (`---`, `***`, `___`), and `<details>` tags

**Fix:** Stop using `mode`. Just pass your limits.

=== "Before (v1.4.0) - hybrid mode"

    ```py
    chunks = chunker.chunk(text, mode="hybrid", max_sentences=5, max_tokens=512)
    ```

=== "After (v2.x.x)"

    ```py
    chunks = chunker.chunk_text(text, max_sentences=5, max_tokens=512)
    ```

### `chunk()` is now `chunk_text()`

The method was renamed to be clear about what it takes: strings.

**Fix:**

=== "Before (v1.4.0)"

    ```py
    chunks = chunker.chunk(text, mode="sentence", max_sentences=5)
    ```

=== "After (v2.x.x)"

    ```py
    chunks = chunker.chunk_text(text, max_sentences=5)
    ```

### `batch_chunk()` is now `chunk_texts()

For multiple texts use `chunk_texts()`. The name actually describes what it does now.

**Fix:**

=== "Before (v1.4.0)"

    ```py
    texts = ["text1", "text2"]
    chunks = chunker.batch_chunk(texts, mode="sentence", max_sentences=5)
    ```

=== "After (v2.x.x)"

    ```py
    texts = ["text1", "text2"]
    chunks = chunker.chunk_texts(texts, max_sentences=5)
    ```

### Language detection moved

The old `detect_text_language.py` file is gone. Language detection now lives inside `SentenceSplitter` directly. Most people won't notice because it happens automatically, but if you were calling it directly, here's the fix:

=== "Before (v1.4.0)"

    ```py
    from chunklet.utils.detect_text_language import detect_text_language
    
    lang, confidence = detect_text_language(text)
    ```

=== "After (v2.x.x)"

    ```py
    from chunklet.sentence_splitter import SentenceSplitter
    
    splitter = SentenceSplitter()
    lang, confidence = splitter.detected_top_language(text)
    ```

### Custom splitters are gone

!!! warning "Removed in v3.0.0"
    Custom splitters were a v2 feature: the old `custom_splitters` constructor parameter was replaced by a global `custom_splitter_registry` in v2, and **both were removed entirely in v3.0.0**.

    `SentenceSplitter` now always uses its built-in language handlers, falling back to a universal rule-based splitter for unsupported languages. If you were relying on a custom splitter for a specific language, open a feature request or split that language manually.

### Exception name changes

A couple exceptions got renamed to be less confusing:

- `TokenNotProvidedError` -> `MissingTokenCounterError` (clearer about what you forgot)
- Custom callback errors now throw `CallbackError` instead of generic `ChunkletError` (so you know it's your code that broke, not ours)  

### CLI changed

The CLI got a new structure. Instead of just `chunklet "text"`, you now use `chunklet chunk "text"`. 

- Text as argument = DocumentChunker
- File with `--source` = DocumentChunker (handles PDFs, DOCX, etc.)
- Add `--code` flag = CodeChunker

=== "Before (v1.4.0)"

    ```bash
    chunklet "Your text here." --mode sentence --max-sentences 5
    ```

=== "After (v2.x.x)"

    ```bash
    # Chunking a string uses DocumentChunker
    chunklet chunk "Your text here." --max-sentences 5

    # Chunking a file from a path uses DocumentChunker by default
    chunklet chunk --source your_text.txt --max-sentences 5
    ```

That's it. Go forth and migrate.

See [CLI docs](getting-started/cli.md) for the full breakdown.