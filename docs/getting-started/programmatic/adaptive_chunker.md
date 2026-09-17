# Adaptive Chunker

<p align="center">
  <img src="../../../img/adaptive_chunker.jpg" alt="Adaptive Chunker" width="512"/>
</p>

## Quick Install

```bash
pip install chunklet-py[adaptive]
```

`AdaptiveChunker` rides on top of the `DocumentChunker` and `CodeChunker` with automatic language detection, so the `adaptive` extra bundles its `struct-doc`, `code`, and `auto` dependencies in one shot.

!!! note "Auto language detection requires the `[auto]` extra"
    The default `lang="auto"` needs `py3langid` to detect the language of your text which is why it ships with the `adaptive` extra. If you only chunk a known language (e.g. `lang="en"`), the default install is enough:

    ```bash
    pip install chunklet-py[struct-doc,code] -U
    ```

## Adaptive Chunker: Your Self-Tuning Text Sidekick! 🤖

Got a messy mix of prose and source code, and no patience to hand-tune chunk sizes for each file? The `AdaptiveChunker` watches how your sources are structured and sizes its own chunk boundaries to match. No manual constraint tuning required.

It classifies every source as **document** or **code**, keeps a running memory (an exponential moving average) of structural metrics per profile, and uses that memory to size the chunks for everything you throw at it.

### Why `AdaptiveChunker` is cool. 🆒

Here's what makes it tick:

-  **Profile-Based Dispatch:** Knows documents from code by extension first, then binary sniffing, then content heuristics for anything extensionless. No setup needed!
-  **Learning Memory (EMA Profiles):** Persists per-profile statistics via an exponential moving average so that chunk sizes react to your real corpus, not to guessed defaults.
-  **Adaptive Limits:** Derives constraints from the learned profile each time instead of using fixed values. The more you chunk, the sharper it gets!
-  **Token Budget Ceiling:** A `hard_token_limit` caps the dynamically grown `max_tokens`, so adaptive limits never run away.
-  **Raw Text & File Support:** Feed it file paths or raw strings; both land in the same queue and get chunked the same way.
-  **Enriched Chunk Metadata:** Every chunk carries an `inferred_type` so you know exactly how each piece was classified.
-  **Memory-Conscious Operation:** `process()` yields chunks one at a time via a generator, so RAM stays happy even on big corpora.

### Constructor: Your Control Knobs 🎛️

| Parameter | Default | Description |
| :-------- | :------ | :---------- |
| `lang` | `'auto'` | Language code (`'en'`, `'fr'`, ...) passed down to the document chunker. |
| `token_counter` | `None` | Function counting tokens in text. When provided, `max_tokens` is learned **and** bounded; when `None`, token limits and `max_tokens` learning are disabled. |
| `hard_token_limit` | `1024` | Ceiling for the dynamically grown `max_tokens`. |
| `ema_alpha` | `0.3` | Smoothing factor in `[0, 1]` for the exponential moving average. Higher values react faster to recent sources. |
| `verbose` | `False` | Toggles verbose logging on the underlying chunkers. |

!!! note "Token Counter Requirement"
    To learn token-based limits, pass a `token_counter` function that accepts a string and returns its token count as an integer. Without one, `AdaptiveChunker` still chunks happily, but it just skips `max_tokens` learning and relies on structural limits.

### Learnable Profiles: What Gets Learned ❓

`AdaptiveChunker` keeps two profiles, one per content type, each initialized from sensible defaults:

```python
{
    "document": {
        "max_sentences": 7.0,
        "header_density_ratio": 0.05,
        "max_section_breaks": 1,
        "max_tokens": 512.0,
    },
    "code": {
        "max_lines": 15.0,
        "max_functions": 1,
        "max_tokens": 512.0,
    },
}
```

| Profile | Learned Metric | What It Measures |
| :------ | :------------- | :--------------- |
| `code` | `max_lines` | Mean line gap between consecutive function declarations. |
| `code` | `max_functions` | Functions-per-chunk signal (1 when functions are widely spaced, 2 when they're tightly clustered). |
| `code` | `max_tokens` | Mean token span between function starts (needs `token_counter`). |
| `document` | `max_sentences` | Mean sentences-per-paragraph, clamped to `[2, 25]`. |
| `document` | `header_density_ratio` | Share of paragraphs carrying a section marker (headings, horizontal rules, `<details>` tags). |
| `document` | `max_section_breaks` | 2 when header density is high, otherwise 1. |
| `document` | `max_tokens` | Mean paragraph token count (needs `token_counter`). |

Each measurement is folded into the stored estimate with `ema_alpha`.

### The Pipeline: Queue Then Process ⏳

`AdaptiveChunker` works in two stages:

1.  **Enqueue** sources with `add_file` / `add_files` (file paths) or `add_text` / `add_texts` (raw strings). Cheap, nothing is read yet.
2.  **Drain** with `process()`, a generator that reads, classifies, learns from, and chunks each source on the spot.

## Single Source: Chunks That Learn! 🎚

Let's watch `AdaptiveChunker` size up a mixed queue (a Markdown document, then a small Python module) and tune its profiles as it goes:

```py linenums="1" hl_lines="8 42-43 45"
from chunklet import AdaptiveChunker


def word_counter(text: str) -> int:  # (1)!
    return len(text.split())


chunker = AdaptiveChunker(token_counter=word_counter, ema_alpha=0.5)

prose = """# My Document

This is the first paragraph. It talks about adaptive chunking and retrieval.
We write a few more sentences to make it substantial.

## Second Section

Here is another paragraph with more content. It keeps the demonstration going nicely.

### Deep Dive

And a final paragraph, still going, to make sure the sample is long enough for splitting."""


code = '''"""Small utilities module."""


def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


def multiply(a: int, b: int) -> int:
    """Multiply two numbers together."""
    return a * b


def greet(name: str) -> str:
    """Return a friendly greeting."""
    return f"Hello {name}!"
'''

chunker.add_text(prose)  # (2)!
chunker.add_text(code)

for i, chunk in enumerate(chunker.process(show_progress=False)):  # (3)!
    print(f"--- Chunk {i + 1} ---")
    print(f"Metadata: {chunk.metadata}")
    print(f"Content:\n{chunk.content}")
    print()
```

1.  A pluggable token counter enables `max_tokens` learning for both profiles.
2.  Raw strings are enqueued the same way as file paths; the queue decides code vs. document later, at `process()` time.
3.  `process()` is a generator, so it can be iterated lazily or drained eagerly.

??? success "Click to show output"
    ```linenums="0"
    --- Chunk 1 ---
    Metadata: {'source': '/tmp/chunklet_xxxxxx', 'chunk_num': 1, 'span': (0, 118), 'inferred_type': 'document'}
    Content:
    # My Document
    This is the first paragraph.
    It talks about adaptive chunking and retrieval.
    We write a few more sentences to make it substantial.

    --- Chunk 2 ---
    Metadata: {'source': '/tmp/chunklet_xxxxxx', 'chunk_num': 2, 'span': (92, 222), 'inferred_type': 'document'}
    Content:
    We write a few more sentences to make it substantial.

    ## Second Section
    Here is another paragraph with more content.
    It keeps the demonstration going nicely.

    --- Chunk 3 ---
    Metadata: {'source': '/tmp/chunklet_xxxxxx', 'chunk_num': 3, 'span': (211, 328), 'inferred_type': 'document'}
    Content:
    It keeps the demonstration going nicely.

    ### Deep Dive
    And a final paragraph, still going, to make sure the sample is long enough for splitting.

    --- Chunk 4 ---
    Metadata: {'chunk_num': 1, 'tree': 'global\n└─ def add(\n', 'start_line': 1, 'end_line': 8, 'span': (0, 119), 'source': 'N/A', 'inferred_type': 'code'}
    Content:
    """Small utilities module."""


    def add(a: int, b: int) -> int:
        """Add two numbers together."""
        return a + b

    --- Chunk 5 ---
    Metadata: {'chunk_num': 2, 'tree': 'global\n└─ def multiply(\n', 'start_line': 9, 'end_line': 13, 'span': (119, 216), 'source': 'N/A', 'inferred_type': 'code'}
    Content:
    def multiply(a: int, b: int) -> int:
        """Multiply two numbers together."""
        return a * b

    --- Chunk 6 ---
    Metadata: {'chunk_num': 3, 'tree': 'global\n└─ def greet(\n', 'start_line': 14, 'end_line': 16, 'span': (216, 311), 'source': 'N/A', 'inferred_type': 'code'}
    Content:
    def greet(name: str) -> str:
        """Return a friendly greeting."""
        return f"Hello {name}!"
    ```

!!! tip "Spot the `inferred_type`"
    Each chunk's metadata carries an `inferred_type` of `'document'` or `'code'`, telling you which profile produced it. Because raw strings are written to temporary files, the `source` shown for `add_text` inputs is the generated temp path (unique per run).

!!! tip "Cap Your Token Budget"
    Set `hard_token_limit` to keep the learned `max_tokens` from ballooning on gigantic files. The final `max_tokens` per chunk is `min(hard_token_limit, learned_max_tokens)`.

!!! note "Extensionless & Unusual Files"
    Sources with a recognizable document/code extension are routed instantly. Everything else is sniffed for binary content (bailing out with an [`UnsupportedFileTypeError`](../../exceptions-and-warnings.md#unsupportedfiletypeerror) for unsupported binaries) and otherwise classified by content heuristics, so extensionless text and code still work.

### The Learning, In Action 🌠

After the run above, the profiles have already updated:

```py linenums="1"
print(chunker.learned_state)
```

```py linenums="0"
{'document': {'max_sentences': 4.5, 'header_density_ratio': 0.275, 'max_section_breaks': 1.0, 'max_tokens': 260.4},
 'code': {'max_lines': 10.0, 'max_functions': 1.0, 'max_tokens': 263.5}}
```

`max_sentences` dropped from the default `7.0` toward the prose's real ~4-5 sentences per paragraph, and both `max_tokens` values are now estimated from your actual content instead of the `512.0` default. Chunk the same corpus again and the boundaries will already fit it better! 📈

!!! tip "Tuning `ema_alpha`"
    -  `ema_alpha=1.0` trusts only the most recent source (fast, jumpy).
    -  `ema_alpha=0.0` keeps the defaults forever (no learning).
    -  Values in between blend old memory with new measurements, so smaller is smoother.

## Batch: Chunk Multiple Sources! 📚

Enqueue as many files and strings as you like; `process()` drains them in order.

```py linenums="1" hl_lines="1-2 4-8"
chunker.add_files(["samples/document.pdf", "samples/sample_module.py"])
chunker.add_text("Some extra raw prose that should also be chunked.")

chunks = chunker.process(
    separator="---END---",  # (1)!
    on_errors="raise",  # (2)!
    show_progress=True,  # (3)!
)

for chunk in chunks:
    ...
```

1.  A value yielded after the chunks of each source, handy for grouping (the same trick as `chunk_texts` / `chunk_files`).
2.  How to handle processing errors: `'raise'` (default), `'skip'`, or `'break'`.
3.  Show a progress bar while draining the queue. Defaults to `True`.

!!! note "Mixed Corpora Are The Sweet Spot"
    Feed it documents *and* code side by side cause that's exactly the scenario `AdaptiveChunker` was built for. No need to sort or tag your inputs; the profile dispatch handles it.

??? info "API Reference"
    For complete technical details on the `AdaptiveChunker` class, check out the [API documentation](../../reference/chunklet/adaptive_chunker/adaptive_chunker.md).
