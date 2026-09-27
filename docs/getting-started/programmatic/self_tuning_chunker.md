# Self-Tuning Chunker

<p align="center">
  <img src="../../../img/self_tuning_chunker.jpg" alt="Self-Tuning Chunker" width="512"/>
</p>

## Quick Install

```bash
pip install chunklet-py[self-tuning]
```

`SelfTuningChunker` rides on top of the `DocumentChunker` and `CodeChunker`, so the `self-tuning` extra bundles its `struct-doc`, `code` dependencies in one shot.

!!! note "Auto language detection requires the `[lang-detect]` extra"
    When you use `lang="auto"`, the chunker needs `py3langid` to detect the language of your text. This is not installed by default.

## SelfTuningChunker: Your Self-Tuning Text Sidekick! 🤖

Got a messy mix of prose and source code, and no patience to hand-tune chunk sizes for each file? The `SelfTuningChunker` watches how your sources are structured and sizes its own chunk boundaries to match. No manual constraint tuning required.

It classifies every source as **document** or **code**, keeps a running memory
(a [Kaufman Adaptive Moving Average (KAMA)](https://www.tradingview.com/support/solutions/43000773012-kaufman-s-adaptive-moving-average-kama/))
of structural metrics per profile, and uses that memory to size the chunks for everything you throw at it.

### Why `SelfTuningChunker` is cool. 🆒

Here's why:

-  **Profile-Based Dispatch:** Knows documents from code by extension first, then binary sniffing, then content heuristics for anything extensionless. No setup needed!
-  **Learning Memory (KAMA Profiles):** Persists per-profile statistics via a Kaufman Adaptive Moving Average so that chunk sizes react to your real corpus, not to guessed defaults.
-  **Self-Tuning Limits:** Derives constraints from the learned profile each time instead of using fixed values. The more you chunk, the sharper it gets!
-  **Token Budget Ceiling:** A `hard_token_limit` caps the dynamically grown `max_tokens`, so self-tuning limits never run away.
-  **Raw Text & File Support:** Feed it file paths or raw strings; both are classified, profiled, and chunked the same way, so you never have to sort or tag your inputs.
-  **Enriched Chunk Metadata:** Every chunk carries an `inferred_type` so you know exactly how each piece was classified.
-  **Memory-Conscious Operation:** The batch methods are generators that yield chunks one at a time, so RAM stays happy even on big corpora.

The `SelfTuningChunker` has four main methods: `chunk_text`, `chunk_file`, `chunk_texts`, and `chunk_files`. `chunk_text` and `chunk_file` return a list of [`DotDict`][chunklet.common.dotdict.DotDict] objects, while `chunk_texts` and `chunk_files` are memory-friendly generators that yield chunks one by one. Each `DotDict` has `content` (the actual text) and `metadata` (all the juicy details). Check the [Metadata guide](../metadata.md) for the full scoop!

### Learnable Profiles: What Gets Learned ❓

`SelfTuningChunker` keeps two profiles, one per content type, each initialized from sensible defaults:

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

The `code` profile learns three metrics:

| Learned Metric | What It Measures |
| :-------------- | :--------------- |
| `max_lines` | Mean line gap between consecutive function declarations. |
| `max_functions` | Functions-per-chunk signal (1 when functions are widely spaced, 2 when they're tightly clustered). |
| `max_tokens` | Mean token span between function starts (needs `token_counter`). |

The `document` profile learns four:

| Learned Metric | What It Measures |
| :-------------- | :--------------- |
| `max_sentences` | Mean sentences-per-paragraph, clamped to `[2, 25]`. |
| `header_density_ratio` | Share of paragraphs carrying a section marker (headings, horizontal rules, `<details>` tags). |
| `max_section_breaks` | 2 when header density is high, otherwise 1. |
| `max_tokens` | Mean paragraph token count (needs `token_counter`). |

!!! tip "Seed From a Previous Run"
    Already tuned a profile on a representative corpus? Pass the saved `learned_state` back in as `initial_state` so the next run starts warm instead of relearning from the defaults:

    ```python
    chunker = SelfTuningChunker(lang="auto", token_counter=word_counter)
    # ... chunk a representative corpus ...
    baseline = chunker.learned_state

    warm = SelfTuningChunker(token_counter=word_counter, initial_state=baseline)
    ```

    Missing profiles or metrics fall back to the defaults, so a partial baseline is fine. Each instance deep-copies what you pass, so mutating one chunker's state never leaks into another.

## Mixed Sources: Chunks That Learn! 🎚

Let's watch `SelfTuningChunker` size up a mixed pair (a Markdown document and a small Python module) and tune its profiles as it goes:

```py linenums="1" hl_lines="8-11 45"
from chunklet import SelfTuningChunker


def word_counter(text: str) -> int:  # (1)!
    return len(text.split())


chunker = SelfTuningChunker(
    lang="en",
    token_counter=word_counter  # (2)!
)

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

for i, chunk in enumerate(chunker.chunk_texts([prose, code])):  # (3)!
    print(f"--- Chunk {i + 1} ---")
    print(f"Content:\n{chunk.content}")
    print("Metadata:")
    for k, v in chunk.metadata.items():
        print(f"{k}: {v}")
    print()
```

1.  A pluggable token counter enables `max_tokens` learning for both profiles.
2.  `token_counter` is optional if you don't want `max_tokens` limit.
3.  Each source is classified and learned from *before* it gets chunked, so the second
    source already benefits from the first one's measurements. Raw strings are routed
    exactly like file paths.

??? success "Click to show output"
    ```linenums="0"
    --- Chunk 1 ---
    Content:
    """Small utilities module."""


    def add(a: int, b: int) -> int:
        """Add two numbers together."""
        return a + b


    Metadata:
    chunk_num: 1
    tree: global
    └─ def add(

    start_line: 1
    end_line: 8
    span: (0, 119)
    inferred_type: code

    --- Chunk 2 ---
    Content:
    def multiply(a: int, b: int) -> int:
        """Multiply two numbers together."""
        return a * b


    Metadata:
    chunk_num: 2
    tree: global
    └─ def multiply(

    start_line: 9
    end_line: 13
    span: (119, 216)
    inferred_type: code

    --- Chunk 3 ---
    Content:
    def greet(name: str) -> str:
        """Return a friendly greeting."""
        return f"Hello {name}!"
    Metadata:
    chunk_num: 3
    tree: global
    └─ def greet(

    start_line: 14
    end_line: 16
    span: (216, 311)
    inferred_type: code

    --- Chunk 4 ---
    Content:
    # My Document
    This is the first paragraph.
    It talks about adaptive chunking and retrieval.
    We write a few more sentences to make it substantial.
    Metadata:
    chunk_num: 1
    span: (0, 118)
    inferred_type: document

    --- Chunk 5 ---
    Content:
    We write a few more sentences to make it substantial.

    ## Second Section
    Here is another paragraph with more content.
    It keeps the demonstration going nicely.
    Metadata:
    chunk_num: 2
    span: (92, 222)
    inferred_type: document

    --- Chunk 6 ---
    Content:
    It keeps the demonstration going nicely.

    ### Deep Dive
    And a final paragraph, still going, to make sure the sample is long enough for splitting.
    Metadata:
    chunk_num: 3
    span: (211, 328)
    inferred_type: document
    ```

!!! tip "Spot the `inferred_type`"
    Each chunk's metadata carries an `inferred_type` of `'document'` or `'code'`, telling you which profile produced it. Already know which one a source is? Skip the guesswork with `file_type="code"` or `file_type="document"`, which overrides detection entirely.

!!! tip "Cap Your Token Budget"
    Set `hard_token_limit` to keep the learned `max_tokens` from ballooning on gigantic files. Just pass it during construction `SelfTuningChunker(..., hard_token_limit=1024)`

### The Learning, In Action 🌠

After the run above, the profiles have already updated:

```py linenums="1"
print(chunker.learned_state)
```

```py linenums="0"
{'document': {'max_sentences': 6.67741935483871, 'header_density_ratio': 0.07903225806451614, 'max_section_breaks': 1.0, 'max_tokens': 479.53548387096777},
 'code': {'max_lines': 14.35483870967742, 'max_functions': 1.064516129032258, 'max_tokens': 479.93548387096774}}
```

`max_sentences` dropped from the default `7.0` toward the prose's real ~6-7 sentences per paragraph, and both `max_tokens` values are now estimated from your actual content instead of the `512.0` default. `max_functions` started to climb because the sample packs its functions about 8 lines apart, so two per chunk is the better bet. Chunk the same corpus again and the boundaries will already fit it better! 📈

!!! tip "How the Memory Works (KAMA)"
    Each profile metric is updated with a [Kaufman Adaptive Moving Average (KAMA)](https://www.tradingview.com/support/solutions/43000773012-kaufman-s-adaptive-moving-average-kama/): the smoothing constant adapts to how efficiently the measurement is moving. When a metric is stable, the average moves slowly (keeps its estimate); when it swings, the average catches up faster. The first ten measurements per metric use the slowest constant, so the estimate warms up gently and doesn't get thrown off by a single noisy source.

    The memory is per-instance and per-profile, so code and document metrics learn independently. Reset it by creating a fresh `SelfTuningChunker`, or seed it from a previous run with `initial_state`.

## Batch: Chunk Multiple Sources! 📚

Hand `chunk_files` as many paths as you like, and it learns from every one of them
before chunking it. Reach for `chunk_texts` when the sources are raw strings instead
of files, and the profile dispatch works exactly the same.

```py linenums="1"
chunks = chunker.chunk_files(
    ["samples/document.pdf", "samples/sample_module.py"],  # (1)!
    separator="---END---",  # (2)!
    on_errors="raise",  # (3)!
    show_progress=True,  # (4)!
    n_jobs=4,  # (5)!
)

for chunk in chunks:
    ...
```

1.  Paths may be `str` or `pathlib.Path`. Each one is classified and profiled on its
    own, so a mixed corpus trains both profiles in a single pass.
2.  A value yielded after the chunks of each source, handy for grouping (the same trick
    as `chunk_texts` / `chunk_files`).
3.  How to handle processing errors: `'raise'` (default), `'skip'`, or `'break'`.
4.  Show a progress bar while working through the sources. Defaults to `False`.
5.  How many sources to process in parallel. Defaults to `None` (all available cores).

!!! note "Non-Deterministic Batch Ordering"
    With `n_jobs > 1`, sources are handled by several worker processes at once, so the
    order chunks are yielded in depends on which worker finishes first. The ordering is
    not guaranteed to be stable between runs. `chunk_num` still marks each chunk's
    position within its own source, and `separator` grouping stays deterministic.

!!! note "Mixed Corpora Are The Sweet Spot"
    Feed it documents *and* code side by side cause that's exactly the scenario `SelfTuningChunker` was built for. No need to sort or tag your inputs; the profile dispatch handles it.

## Self-Tuning vs Adaptive: Same Family, Different Level 🎚

Self-tuning *is* adaptive chunking, same family, not competitors. The difference is the level at which the adaptation happens.

**Adaptive chunking** usually means adapting *within* a document: pick the splitter or boundaries that best fit *this* text (multiple strategies, embedding distances, a scoring pass). Call it micro-level adaptation.

**Self-tuning** means adapting the *configuration* that every document is then chunked with: learn what a normal chunk looks like for your corpus as a whole, and feed those numbers to one splitter. Call it macro-level adaptation.

That single distinction cascades into everything below.

**They pick a splitter, we tune one.** Tools like [`adaptive-chunking`](https://github.com/ekimetrics/adaptive-chunking) (from the LREC 2026 paper "Optimizing Chunking-Method Selection for RAG") and `adaptive-oci-chunking` run recursive, page, and LLM-regex splitters in parallel, score each candidate with intrinsic metrics (size compliance, intra-chunk cohesion, contextual coherence, ...), and keep the highest scorer. `SelfTuningChunker` never changes the chunking method: it always drives the same `CodeChunker` and `DocumentChunker`, but the *limits* those chunkers use (`max_lines`, `max_functions`, `max_sentences`, `max_section_breaks`, `max_tokens`) are recalculated from a running, KAMA-smoothed profile of everything you've already processed.

**Online macro learning beats post-hoc micro scoring.** Because scoring-based tools decide per document, their choice for one file tells you nothing about the next. `SelfTuningChunker` learns *while it works through your sources*: each source updates the profile before it's chunked, so file #100 is automatically chunked with sharper boundaries than file #1 at no extra cost.

**No LLM, no embeddings, no inference bills.** `semantic-chunkers` leans on embedding distances and [`chunking-strategy`](https://pypi.org/project/chunking-strategy/) on an AI-powered profiler. Our signals are purely structural: sentences per paragraph, header density, section-break density, function-declaration spans, and token counts. That means it's offline, free, deterministic (the same corpus always learns the same profile), and fast; just one linear measurement pass on top of the chunking itself.

**Built for mixed code/document corpora.** Most adaptive chunkers assume prose. `SelfTuningChunker` keeps a dedicated `code` and `document` profile and routes each source by extension, then binary sniffing, then content heuristics, so folders mixing `*.py` + `.md` + extensionless text just work.

**Native, not a framework hub.** `adaptive-oci-chunking` ships wrappers for LangChain/LlamaIndex and `chunking-strategy` dispatches to 40 external splitters. `SelfTuningChunker` is a first-class chunklet class: it reuses the library's own chunkers and `DotDict` chunk vocabulary, adds no framework glue, and the `[self-tuning]` extra only bundles dependencies chunklet already needs.

### Macro vs Micro at a Glance 🥊

| | Per-document adaptive (micro) | `SelfTuningChunker` (macro) |
| :------ | :----------------------------- | :-------------------------- |
| What adapts | Splitter/boundaries for each document | Constraints shared across the corpus |
| Decision unit | One document at a time | The running corpus profile |
| Passes over text | Several (strategies plus scoring) | One measurement pass plus chunking |
| Inference needed | Often LLM and/or embeddings | None |
| Cross-document learning | None | KAMA-smoothed across all sources |
| Deterministic | Varies | Yes |

Reach for per-document adaptive tools when an individual document is wild enough that a *method* change is needed. Reach for `SelfTuningChunker` when you have a stream of mixed text/code sources and want boundaries that sharpen as they go, without an LLM call or embedding pass per document.

??? info "API Reference"
    For complete technical details on the `SelfTuningChunker` class, check out the [API documentation](../../reference/chunklet/self_tuning_chunker/self_tuning_chunker.md).
