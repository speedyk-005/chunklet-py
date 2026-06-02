!!! info "What's on This Page"
    The big stuff. The shiny new things. The stuff we got tired of fixing. For everything else, there's the [changelog](https://github.com/speedyk-005/chunklet-py/blob/main/CHANGELOG.md).

---

## Chunklet v2.3.2

### 🏎️ DotDict Gets Box-Compatible Serialization

We ditched the external `dotdict3` dependency and vendored the code in-tree. Now our `DotDict` has all the serialization methods you expect from the old python-box days:

- **`to_dict()`** — recursive conversion back to plain dicts/lists
- **`to_json()`** — serialize to JSON string or file
- **`to_yaml()`** — YAML, obviously (needs `pyyaml`)
- **`to_toml()`** — TOML support (needs `toml`)
- **`to_msgpack()`** — MessagePack binary format (needs `msgpack`)

The CLI `--metadata` flag no longer crashes — `.to_dict()` actually exists now. 2.3x faster than python-box's `to_dict()` too, since we're not dragging in all of Box's feature creep.

### 🔧 The Boring Stuff

- Removed `dotdict3` from dependencies (vendored in `chunklet.common.dotdict`)
- Docs updated: stale "Box" references replaced with "DotDict" + mkdocstrings cross-links

---

## Chunklet v2.3.1

### 🤖 Android Detection, Fixed (Kinda)

v2.3.0 shipped with `platform_system` markers to detect Android. The problem? Android reports as `'Linux'`, not `'Android'` — so literally nobody was getting the right `sentencex` version. Fixed now with `sys_platform` + `platform_machine` markers. Downside: ARM Linux (Raspberry Pi, etc.) also gets the legacy `sentencex<=0.6.1` without Rust bindings. Temporary, we swear.

### 🐛 DotDict TypeError Fixed

Using `DotDict()` without arguments threw `TypeError` on `dotdict3 < 1.4.2`. Now using `DotDict({})` for backward compatibility.

---

## Chunklet v2.3.0

### 🧩 Smarter Sentence Splitting

The universal fallback splitter finally learned some new tricks:

- **Non-Latin scripts** — Arabic, Chinese, and friends now get treated right
- **Quoted text and parens** — "this (and this)" stay together as one sentence
- **Numbered lists** — 1. 2. 3. now behave instead of getting split apart

### 📄 Document Chunker Improvements

- Better markdown heading detection — we finally read your headers right

### 🎨 Visualizer Gets Sleeker

Now serving both JSON and MessagePack — because one format was never enough:

- Browser visualizer requests MessagePack automatically for performance (~30-50%)
- Programmatic clients can choose: JSON (default) or MessagePack (opt-in via `Accept: application/msgpack` header)
- MessagePack encoding — because we care about your bandwidth

### 🐛 The Fixes

- **pkg_resources** — finally fixed that annoying ModuleNotFoundError (long story)
- **Registration** — no more TypeError with `functools.partial` when registering custom splitters
- **Auto-lang** — stopped spamming you with repeated warnings when `lang='auto'`
- **Code output** — methods now appear under their class, not "global" (we know, it was annoying)

### 🔧 The Boring Stuff

- Lazy imports for splitter libraries (faster startup)
- Added `viz` as shorthand for `visualization` extra
- Dropped Python 3.10 support (anyway Python 3.10 is approaching end-of-life)

---

## Chunklet v2.2.0

### ✨ Simpler Chunking API

We renamed some methods. Yes, we're those people who rename things. But honestly, the old names were confusing — even to us:

- `chunk_text()` — chunk a string
- `chunk_file()` — chunk a file directly  
- `chunk_texts()` — batch strings
- `chunk_files()` — batch files

The old `chunk` and `batch_chunk` still work. They'll whine at you with a deprecation warning. Deal with it or migrate — your choice.

### 🔗 PlainTextChunker Got Absorbed

`PlainTextChunker` is now part of `DocumentChunker`. We know — having two chunkers was weird. Just use `chunk_text()` or `chunk_texts()` like a normal person. The old import still works, technically, with a deprecation warning.

### ✂️ SentenceSplitter Now Does `split_text()`

`split()` is out. `split_text()` is in. We renamed it because apparently "split" was too short. There's also now `split_file()` if you're the type who likes skipping steps.

### 🎨 Visualizer Makeover

The chunk visualizer finally got some love:

- **Fullscreen mode** — for when you want to pretend you're doing something important
- **3-row layout** — less cluttered, more clickable
- **Smoother hovers** — no more seizure-inducing animations
- **Smarter buttons** — they stay enabled because, honestly, disabling them was stupid

### ⌨️ Shorter CLI Flags

Finally, stuff you can actually type without wrist strain:

- `-l` for `--lang`
- `-h` for `--host`  
- `-m` for `--metadata`

You're welcome.

### 🧑‍💻 Code Chunking, Less Broken

Code chunking got slightly less terrible:

- **Cleaner output** — fixed weird artifacts in chunks from comment handling (we know, it was annoying)
- **More languages** — Forth, PHP 8 attributes, VB.NET, ColdFusion, and Pascal. Yes, really.
- **String protection** — multi-line strings and triple-quotes won't get mangled anymore

### 🔧 The Boring But Necessary Stuff

- **Tokenizer timeout** — new `--tokenizer-timeout` / `-t` flag so custom tokenizers don't hang forever
- **Direct imports** — `from chunklet import DocumentChunker` now works without making things slow
- **Fewer crashes** — fixed dependency issues with `setuptools<81` in CI (sentsplit and pkg_resources, long story)
- **Global registries** — `custom_splitter_registry` and `custom_processor_registry` exist now
- **Error messages** — slightly less cryptic when things explode

---

## Chunklet v2.1.1

### 🐛 Visualizer Was Broken

The visualizer didn't work after installing from PyPI. Static files were MIA. Fixed now, obviously.

---

## Chunklet v2.1.0

### 🌐 Visualizer 1.0

We built an actual UI. Because sometimes you want to click buttons instead of writing code:

- Interactive web interface for parameter tuning
- Launch with `chunklet visualize`
- Works with all chunker types

### 📁 More File Formats

ODT, CSV, and Excel (.xlsx) — added in this release. Because apparently plain text wasn't enough for some people.

---

## Chunklet v2.0.0

### 🚀 The Big Rewrite (aka "We Broke Everything")

We rewrote the whole thing. You're welcome? Here's what changed:

- **🗃 New classes** — PlainTextChunker, DocumentChunker, CodeChunker
- **🌍 50+ languages** — because the world has more than English
- **📄 Document formats** — PDF, DOCX, EPUB, HTML, etc.
- **💻 Code understanding** — actual code chunking, not just "split by lines like a savage"
- **🎯 New constraints** — `max_section_breaks` and `max_lines` for finer control
- **⚡ Memory efficient batch** — generators in batch methods so your RAM doesn't cry

---

## 🗺️ Want More Details?

The [changelog](https://github.com/speedyk-005/chunklet-py/blob/main/CHANGELOG.md) has everything. We're not gonna repeat it here.
