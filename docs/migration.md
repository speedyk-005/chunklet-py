# Migrating to Chunklet 3.x.x

Whether you're coming from v2 or (bravely) from v1, this guide gets you onto the v3 API.

### Automated migration checker

I wrote a script that scans your code for old patterns. It'll point out exactly what needs changing.

```bash
curl -O https://raw.githubusercontent.com/speedyk-005/chunklet-py/main/audit_migration.py
python audit_migration.py /path/to/your/project
```

---

## Coming from v2

The v2-v3 jump is small: no API renames, just a couple of removals. If you're already on the unified `chunk_text`/`chunk_texts`/`split_text` API, you're unaffected by the deprecation removals.

### Custom sentence splitters are gone

!!! warning "Removed in v3.0.0"
    Custom splitters were a v2 feature: the old `custom_splitters` constructor parameter was replaced by a global `custom_splitter_registry` in v2, and **both were removed entirely in v3.0.0**.

    `SentenceSplitter` now always uses its built-in language handlers, falling back to a universal rule-based splitter for unsupported languages. If you were relying on a custom splitter for a specific language, open a feature request or split that language manually.

### Custom processor registry is now instance-based

In v2, custom processors lived on a **global** `custom_processor_registry` singleton shared across your whole app. In v3 that global is gone — you now create a `CustomProcessorRegistry()` yourself and pass it to a `DocumentChunker` via `processor_registry`. Each registry is independent, so registrations are scoped to the chunker you attach it to.

**Fix:**

=== "Before (v2.x.x)"

    ```py
    from chunklet.document_chunker import DocumentChunker, custom_processor_registry


    @custom_processor_registry.register(".json", name="MyJSONProcessor")
    def my_json_processor(file_path: str) -> tuple[str, dict]: ...


    chunker = DocumentChunker()
    ```

=== "After (v3.x.x)"

    ```py
    from chunklet.document_chunker import CustomProcessorRegistry, DocumentChunker

    registry = CustomProcessorRegistry()


    @registry.register(".json", name="MyJSONProcessor")
    def my_json_processor(file_path: str) -> tuple[str, dict]: ...


    chunker = DocumentChunker(lang="en", processor_registry=registry)
    ```

!!! tip "Scope your registries"
    Each `DocumentChunker` without a `processor_registry` arg gets its own fresh registry. Share a single `CustomProcessorRegistry()` instance across chunkers only when you actually want them to share the same custom processors.

### Removed v2.2.0 aliases

The names deprecated in v2.2.0 are gone in v3. If you were still using them, here's the mapping:

- `SentenceSplitter.split()` => `split_text()`
- `DocumentChunker.chunk()` => `chunk_text()` / `chunk_file()`
- `DocumentChunker.batch_chunk()` => `chunk_texts()` / `chunk_files()`
- `CodeChunker.chunk()` => `chunk_text()` / `chunk_file()`
- `CodeChunker.batch_chunk()` => `chunk_texts()` / `chunk_files()`
- `PlainTextChunker` public import => `DocumentChunker.chunk_text()`

If you were already calling the `chunk_text`/`chunk_texts`/`split_text` methods, nothing changes for you.

### `lang="auto"` is no longer the default

In v2, `lang` defaulted to `"auto"` and `py3langid` was a hard dependency — it was always installed. In v3, `lang` is required (no default), and `py3langid` is now an optional extra called `[auto]`.

If you were relying on automatic language detection, you need to:

1. Pass `lang="auto"` explicitly (it's no longer implicit).
2. Install the extra: `pip install 'chunklet-py[auto]'`

If you only ever used specific language codes like `lang="en"`, you don't need the extra — the default install is enough.

=== "Before (v2.x.x)"

    ```py
    chunker = DocumentChunker()
    chunks = chunker.chunk_text(text)  # lang defaulted to "auto"
    ```

=== "After (v3.x.x)"

    ```py
    chunker = DocumentChunker(lang="auto")
    chunks = chunker.chunk_text(text)
    ```

    And install the extra:

    ```bash
    pip install 'chunklet-py[auto]'
    ```

### Language detection moved to `common`

Language detection is no longer a method on `SentenceSplitter`. It's now a standalone function at `chunklet.common.lang_detection.detect_top_language()`, so you can call it without constructing a splitter.

This affects two ways you may have used it before:

- The legacy `chunklet.utils.detect_text_language()` from v1/v2.
- `SentenceSplitter.detected_top_language()` from v2.

=== "Before (v2.x.x)"

    ```py
    from chunklet.sentence_splitter import SentenceSplitter

    splitter = SentenceSplitter(lang="auto")
    lang_code, confidence = splitter.detected_top_language(text)
    ```

=== "After (v3.x.x)"

    ```py
    from chunklet.common.lang_detection import detect_top_language

    lang_code, confidence = detect_top_language(text)
    ```

It still needs `py3langid`, so install the extra if you haven't:

```bash
pip install 'chunklet-py[auto]'
```

### Constraints moved to the constructor

Sizing and tuning parameters (`max_tokens`, `max_sentences`, `max_section_breaks`, `overlap_percent`, `offset`, `lang`) used to be passed per call to `chunk_text()`, `chunk_file()`, `chunk_texts()`, `chunk_files()`, `split_text()`, and `split_file()`. They now live on the chunker/splitter instance, set once at construction and mutable as plain attributes. The same applies to `CodeChunker` (`max_tokens`, `max_lines`, `max_functions`) and `SentenceSplitter` (`lang`).

=== "Before"

    ```py
    chunker = DocumentChunker()
    chunks = chunker.chunk_text(
        text,
        lang="auto",
        max_sentences=3,
        max_tokens=500,
        max_section_breaks=2,
        overlap_percent=20,
        offset=0,
    )
    ```

=== "After"

    ```py
    chunker = DocumentChunker(
        lang="auto",
        max_sentences=3,
        max_tokens=500,
        max_section_breaks=2,
        overlap_percent=20,
        offset=0,
    )
    chunks = chunker.chunk_text(text)
    ```

---

## Coming from v1

The v1-v2 rename guide (the old `Chunklet` class, `mode`, `use_cache`, `batch_chunk`, etc.) lives in the [v2.x version of these docs](https://speedyk-005.github.io/chunklet-py/v2.4.0/migration/). The short version: `Chunklet` became `DocumentChunker`, and the unified `chunk_text`/`chunk_texts`/`split_text` API replaced the old methods.

---

That's it. Go forth and migrate.

See [CLI docs](getting-started/cli.md) for the full breakdown.
