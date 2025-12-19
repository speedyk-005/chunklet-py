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

You might be wondering: "Can't I just split my text by character count or random line breaks?" Well, sure you could... but that's like trying to cut a wedding cake with a chainsaw! 🎂 Standard methods often give you:

-   **Mid-sentence surprises:** Your carefully crafted thoughts get chopped right in the middle, losing all meaning
-   **Language confusion:** Non-English text and code structures get treated like they're all the same
-   **Lost context:** Each chunk forgets what came before, like a conversation where everyone has amnesia

Smart chunking keeps your content's meaning and structure intact!

## 🤔 So What's Chunklet-py Anyway? (And Why Should You Care?)

**Chunklet-py** is your friendly neighborhood text splitter that takes all kinds of content - from plain text to PDFs to source code - and breaks them into smart, context-aware chunks. Instead of dumb splitting, we give you specialized tools:

*   `Sentence Splitter`
*   `Plain Text Chunker`
*   `Document Chunker`
*   `Code Chunker`
*   `Chunk Visualizer` (Interactive web interface)

Each tool keeps your content's meaning and structure intact.

Perfect for prepping data for LLMs, building RAG systems, or powering AI search - Chunklet-py gives you the precision and flexibility you need across tons of formats and languages.

| Feature | Why it's awesome |
| :--- | :--- |
| 🚀 **Blazingly Fast** | Leverages efficient parallel processing to chunk large volumes of content with remarkable speed. |
| 🪶 **Featherlight Footprint** | Designed to be lightweight and memory-efficient, ensuring optimal performance without unnecessary overhead. |
| 🗂️ **Rich Metadata for RAG** | Enriches chunks with valuable, context-aware metadata (source, span, document properties, code AST details) crucial for advanced RAG and LLM applications. |
| 🔧 **Infinitely Customizable** | Offers extensive customization options, from pluggable token counters to custom sentence splitters and processors. |
| 🌐 **Multilingual Mastery** | Supports over 50 natural languages for text and document chunking with intelligent detection and language-specific algorithms. |
| 🧑‍💻 **Code-Aware Intelligence** | Language-agnostic code chunking that understands and preserves the structural integrity of your source code. |
| 🎯 **Precision Chunking** | Flexible constraint-based chunking allows you to combine limits based on sentences, tokens, sections, lines, and functions. |
| 📄 **Document Format Mastery** | Processes a wide array of document formats including `.pdf`, `.docx`, `.epub`, `.txt`, `.tex`, `.html`, `.hml`, `.md`, `.rst`, `.rtf`, `.odt`, `.csv`, and `.xlsx`. |
| 💻 **Triple Interface: CLI, Library & Web** | Use it as a command-line tool, import as a library for deep integration, or launch the interactive web visualizer for real-time chunk exploration and parameter tuning. |


And that's just the start - there's plenty more to explore!

> [!NOTE]
> For the full documentation experience, check out our [documentation site](https://speedyk-005.github.io/chunklet-py/latest).

---

## 📦 Installation

Ready to get Chunklet-py running? Awesome! Let's get you set up quickly and painlessly.

!!! note "Package Name Change"
    Chunklet-py was previously named `chunklet`. The old `chunklet` package is no longer maintained. When installing, make sure to use `chunklet-py` (with the hyphen) to get the latest version.
    
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
    pip install "chunklet-py[document]"
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

## 🗺 Features & Roadmap

- [x] CLI interface
- [x] Documents chunking with metadata
- [x] Code chunking based on interest point
- [x] Interactive chunk visualizer (web interface)
- [x] Extended file format support:
  - [x] ODT files
  - [x] CSV and Excel files
- Future enhancements:
  - [ ] Additional document formats

---

## How Chunklet-py Compares

While there are other chunking libraries available, Chunklet-py stands out for its unique combination of versatility, performance, and ease of use. Here's a quick look at how it compares to some of the alternatives:

| Library | Key Differentiator | Focus |
| :--- | :--- | :--- |
| **chunklet-py** | **All-in-one, lightweight, and language-agnostic with specialized algorithms.** | **Text, Code, Docs** |
| [CintraAI Code Chunker](https://github.com/CintraAI/code-chunker) | Relies on `tree-sitter`, which can add setup complexity. | Code |
| [Chonkie](https://github.com/chonkie-inc/chonkie) | A feature-rich pipeline tool with cloud/vector integrations, but uses a more basic sentence splitter and `tree-sitter` for code. | Pipelines, Integrations |
| [code_chunker (JimAiMoment)](https://github.com/JimAiMoment/code-chunker) | Uses basic regex and rules with limited language support. | Code |
| [Semchunk](https://github.com/isaacus-dev/semchunk) | Primarily for text, using a general-purpose sentence splitter. | Text |

Chunklet-py's rule-based, language-agnostic approach to code chunking avoids the need for heavy dependencies like `tree-sitter`, which can sometimes introduce compatibility issues. For sentence splitting, it uses specialized libraries and algorithms for higher accuracy, rather than a one-size-fits-all approach. This makes Chunklet-py a great choice for projects that require a balance of power, flexibility, and a small footprint.

---

## 🙌 Contributors & Thanks

A huge thank you to the awesome people who helped shape Chunklet-py:

- [@jmbernabotto](https://github.com/jmbernabotto) — for helping mostly on the CLI part, suggesting fixes, features, and design improvements.
- [@arnoldfranz](https://github.com/arnoldfranz) — for reporting the CLI Path Validation Bug (#6) that helped improve error handling.

---

📜 License

Check out the [LICENSE](https://github.com/speedyk-005/chunklet-py/blob/main/LICENSE) file for all the details.

> MIT License. Use freely, modify boldly, and credit appropriately! (We're not that legendary... yet 😉)
