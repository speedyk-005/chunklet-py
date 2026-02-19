# 🧩 Chunklet-py

<p align="center">
  <img src="https://github.com/speedyk-005/chunklet-py/blob/main/logo_with_tagline.png?raw=true" alt="Chunklet-py Logo" width="300"/>
</p>

“One library to split them all: Sentence, Code, Docs”

> [!WARNING]
> **Quick heads up!** Version 2 has some breaking changes. No worries though - check our [Migration Guide](https://speedyk-005.github.io/chunklet-py/latest/migration/) for a smooth upgrade!

[![Python Version](https://img.shields.io/badge/Python-3.10%20--%203.14-blue)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/chunklet-py)](https://pypi.org/project/chunklet-py)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/chunklet-py?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=BLUE&left_text=downloads)](https://pepy.tech/projects/chunklet-py)
[![Coverage Status](https://coveralls.io/repos/github/speedyk-005/chunklet-py/badge.svg?branch=main)](https://coveralls.io/github/speedyk-005/chunklet-py?branch=main)
[![Stability](https://img.shields.io/badge/stability-stable-brightgreen)](https://github.com/speedyk-005/chunklet-py)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](https://github.com/speedyk-005/chunklet-py/actions)
[![CodeFactor](https://www.codefactor.io/repository/github/speedyk-005/chunklet-py/badge)](https://www.codefactor.io/repository/github/speedyk-005/chunklet-py)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/speedyk-005/chunklet-py)

<p align="center">
  <a href="https://speedyk-005.github.io/chunklet-py/latest" target="_blank" rel="noopener noreferrer">
    -- documentation site --
  </a>
</p>

## Why Smart Chunking? (Or: Why Not Just Split on Character Count?)

You might be wondering: "Can't I just split my text by character count or random line breaks?" Well, sure you could... but that's like trying to cut a wedding cake with a chainsaw! 🎂

Standard methods slice at arbitrary points, which causes:

- **Mid-sentence surprises:** Your thoughts get chopped mid-way, losing all meaning
- **Language confusion:** Non-English text and code structures get treated the same
- **Lost context:** Each chunk forgets what came before

Smart chunking solves this by:

- **Smart limits** — Respects both natural boundaries (sentences, paragraphs, sections) AND configurable limits (tokens, lines, functions)
- **Language-aware** — Detects language automatically and applies the right rules (50+ languages supported)
- **Context preservation** — Overlap between chunks, rich metadata (source, span, document structure)

## 🤔 So What's Chunklet-py Anyway? (And Why Should You Care?)

**Chunklet-py** is a developer-friendly text splitting library designed to be the most versatile chunking solution — for devs, researchers, and AI engineers. It goes way beyond basic character counting. It intelligently chunks text, documents, and code into meaningful, context-aware pieces — perfect for RAG pipelines and LLM applications.

Key features:

- **Composable constraints** — Mix and match limits (sentences, tokens, sections) to get exactly the chunks you need
- **Pluggable architecture** — Swap in custom tokenizers, sentence splitters, or processors
- **Rich metadata** — Every chunk comes with source references, spans, and structural info
- **Multi-format support** — Text, PDFs, DOCX, EPUB, HTML, and source code

Available tools:

- `SentenceSplitter` — Lightweight sentence tokenization
- `DocumentChunker` — Natural language with semantic boundaries
- `CodeChunker` — Language-aware code chunking
- `ChunkVisualizer` — Interactive web-based exploration

Perfect for prepping data for LLMs, building RAG systems, or powering AI search - Chunklet-py gives you the precision and flexibility you need across tons of formats and languages.

| Feature | Why it's awesome |
| :--- | :--- |
| 🚀 **Blazingly Fast** | Leverages efficient parallel processing to chunk large volumes of content with remarkable speed. |
| 🪶 **Featherlight Footprint** | Designed to be lightweight and memory-efficient, ensuring optimal performance without unnecessary overhead. |
| 🗂️ **Rich Metadata for RAG** | Enriches chunks with valuable, context-aware metadata (source, span, document properties, code AST details) crucial for advanced RAG and LLM applications. |
| 🔧 **Infinitely Customizable** | Offers extensive customization options, from pluggable token counters to custom sentence splitters and processors. |
| 🌐 **Multilingual Mastery** | Supports over 50 natural languages for text and document chunking with intelligent detection and language-specific algorithms. |
| 🧑‍💻 **Code-Aware Intelligence** | Language-agnostic code chunking that understands and preserves the structural integrity of your source code. |
| 🎯 **Precision Chunking** | Flexible chunking with configurable limits based on sentences, tokens, sections, lines, and functions. |
| 📄 **Document Format Mastery** | Processes a wide array of document formats including `.pdf`, `.docx`, `.epub`, `.txt`, `.tex`, `.html`, `.hml`, `.md`, `.rst`, `.rtf`, `.odt`, `.csv`, and `.xlsx`. |
| 💻 **Triple Interface: CLI, Library & Web** | Use it as a command-line tool, import as a library for deep integration, or launch the interactive web visualizer for real-time chunk exploration and parameter tuning. |


And that's just the start - there's plenty more to explore!

> [!NOTE]
> For the full documentation experience, check out our [documentation site](https://speedyk-005.github.io/chunklet-py/latest).

---

## 📦 Installation

Ready to get Chunklet-py running? Awesome! Let's get you set up quickly and painlessly.

> [!NOTE]
> **chunklet-py (aka chunklet)** — The old `chunklet` package is no longer maintained. Use `chunklet-py` to get the latest version.
    
### The Quick & Easy Way

The simplest way to get started is with pip:

```bash
# Install and check it's working
pip install chunklet-py
chunklet --version
```

That's it! You're all set to start chunking.

### Extra Features (Optional)

Want to unlock more Chunklet-py superpowers? Add these optional dependencies based on what you need:

*   **Document Processing:** For handling `.pdf`, `.docx`, `.epub`, and other document formats:
    ```bash
    pip install "chunklet-py[structured-document]"
    ```
*   **Code Chunking:** For advanced code analysis and chunking features:
    ```bash
    pip install "chunklet-py[code]"
    ```
*   **Visualization:** For the interactive web-based chunk visualizer:
    ```bash
    pip install "chunklet-py[visualization]"
    ```
*   **All Extras:** To install all optional dependencies:
    ```bash
    pip install "chunklet-py[all]"
    ```

### The From-Source Way

Prefer building from source? You can clone and install manually for full control:

```bash
git clone https://github.com/speedyk-005/chunklet-py.git
cd chunklet-py
pip install .[all]
```

(But honestly, the pip way is usually way easier!)

### Want to Help Make Chunklet-py Even Better?

That's awesome! We'd love to have you contribute. Check out our [**Contributing Guide**](https://github.com/speedyk-005/chunklet-py/blob/main/CONTRIBUTING.md) first, then set up your development environment:

```bash
git clone https://github.com/speedyk-005/chunklet-py.git
cd chunklet-py
# For basic development (testing, linting)
pip install -e ".[dev]"
# For documentation development
pip install -e ".[docs]"
# For comprehensive development (including all optional features like document and code chunking + docs dependencies)
pip install -e ".[dev-all]"
```

These install Chunklet-py in "editable" mode so your code changes take effect immediately. The different options give you just the dependencies you need.

Go forth and code! (And remember, good developers write tests. We appreciate excellent code examples!)

---

## Quick Reference 🛠️

For the exhaustive details that I know you're probably avoiding, check the [official docs](https://speedyk-005.github.io/chunklet-py/latest/).

### The Constraint-Based Logic

Chunklet-py is basically a "choose your own adventure" for data. It's constraint-based, meaning you can swap, combine, or ignore the limits below as you see fit.

**The Golden Rule:** You must provide at least one constraint, or the chunker has no idea when to stop.

> [!NOTE]
> A quick overview — for the complete picture, check the [detailed docs](https://speedyk-005.github.io/chunklet-py/latest/).

### Core Imports

Pick your weapon based on whatever data mess you're currently cleaning up.

```python
from chunklet import DocumentChunker   # For PDFs, DOCX, and general text chaos
from chunklet import CodeChunker       # For source code (it actually respects brackets)
from chunklet import SentenceSplitter  # For when you just need to split sentences
from chunklet import visualizer        # Web-based chunk visualizer
```

### Configuration & Limits

These tools don't share arguments, so don't try to use `max_functions` on a PDF unless you want to see a very confused Python interpreter.

**DocumentChunker (Text & Docs)**

Perfect for natural language where you don't want to cut someone off mid-sentence.

```python
chunker = DocumentChunker()

# Feel free to mix and match these
chunks = chunker.chunk_text(
    text,
    max_sentences=3,       # Stop after X sentences
    max_tokens=500,        # Don't blow up the LLM context
    max_section_breaks=2,  # Respect the Markdown headers
    overlap_percent=20,    # Give it some "memory" of the last chunk
    offset=0               # Skip the first N sentences if you're feeling adventurous
)
```

**CodeChunker (Source Code)**

Logic-aware. It doesn't do "overlap" because duplicate code is a hallucination waiting to happen.

```python
chunker = CodeChunker()

# Again, use whichever constraints make sense for your file
chunks = chunker.chunk_text(
    text,
    max_lines=50,          # Height limit
    max_tokens=512,        # Width limit
    max_functions=1,       # One function per chunk (keeps things tidy)
    strict=True            # True: Crash on big blocks; False: Slice 'em up anyway
)
```

### The Output Object

The chunkers return a list (or generator) of Chunk objects. These are Box instances, so you can use dot notation like a civilized developer.

```python
for chunk in chunks:
    print(chunk.content)   # The actual text/code
    print(chunk.metadata)  # Chunk metadata
    print()                # Because whitespace is free
```

### Input Methods (Chunkers Only)

These helper methods are for the DocumentChunker and CodeChunker. The SentenceSplitter is a simple soul and only takes strings.

| Method | Input | Return Type |
|--------|-------|-------------|
| `chunk_text(text)` | str | List[Chunk] |
| `chunk_file(path)` | Path or str | List[Chunk] |
| `chunk_texts(list)` | List[str] | Generator[Chunk] |
| `chunk_files(list)` | List[Path] | Generator[Chunk] |

### Specialized Tools

**SentenceSplitter**

The "lite" version for when you just need sentences and no fancy metadata.

```python
splitter = SentenceSplitter()

# 'auto' usually guesses right, but you can specify 'en', 'es', etc.
sentences = splitter.split_text(text, lang="auto")
```

**CLI (Command Line Interface)**

If you prefer the terminal to an IDE, the CLI is packed with features. Just ask for help.

```bash
chunklet --help
chunklet split --help
chunklet chunk --help
chunklet visualize --help
chunklet [COMMAND] [OPTIONS*]
```

---

## 🗺 Features & Roadmap

- [x] CLI interface
- [x] Documents chunking with metadata
- [x] Code chunking based on interest point
- [x] Interactive chunk visualizer (web interface)
- [x] Extended file format support:
  - [x] ODT files
  - [x] CSV and Excel files

---

## How Chunklet-py Compares

While there are other chunking libraries available, Chunklet-py stands out for its unique combination of versatility, performance, and ease of use. Here's a quick look at how it compares to some of the alternatives:

| Library | Key Differentiator | Focus |
| :--- | :--- | :--- |
| **chunklet-py** | **All-in-one, lightweight, multilingual, language-agnostic with specialized algorithms.** | **Text, Code, Docs** |
| [LangChain](https://github.com/langchain-ai/langchain) | Full LLM framework with basic splitters (e.g., RecursiveCharacterTextSplitter, Markdown, HTML, code splitters). Good for prototyping but basic for complex docs or multilingual needs. | Full Stack |
| [Chonkie](https://github.com/chonkie-inc/chonkie) | All-in-one pipeline (chunking + embeddings + vector DB). Uses `tree-sitter` for code. Multilingual. | Pipelines |
| [Semchunk](https://github.com/isaacus-dev/semchunk) | Text-only, fast semantic splitting. Built-in tiktoken/HuggingFace support. 85% faster than alternatives. | Text |
| [CintraAI Code Chunker](https://github.com/CintraAI/code-chunker) | Code-specific, uses `tree-sitter`. Initially supports Python, JS, CSS only. | Code |

Chunklet-py is a specialized, drop-in replacement for the chunking step in any RAG pipeline. It handles text, documents, and code without heavy dependencies, while keeping your project lightweight.

---

## 🙌 Contributors & Thanks

A huge thank you to the awesome people who helped shape Chunklet-py:

- [@jmbernabotto](https://github.com/jmbernabotto) — for helping mostly on the CLI part, suggesting fixes, features, and design improvements.
- [@arnoldfranz](https://github.com/arnoldfranz) — for reporting the CLI Path Validation Bug (#6) that helped improve error handling.

---

📜 License

Check out the [LICENSE](https://github.com/speedyk-005/chunklet-py/blob/main/LICENSE) file for all the details.

> MIT License. Use freely, modify boldly, and credit appropriately! (We're not that legendary... yet 😉)
