# 🧩 Chunklet-py

<p align="center">
  <img src="https://github.com/speedyk-005/chunklet-py/blob/main/logo_with_tagline.png?raw=true" alt="Chunklet-py Logo" width="200"/>
</p>

“One library to split them all: Sentence, Code, Docs”

> [!WARNING]
> **Heads Up!** Version 2.0.0 introduces **breaking changes**. For a smooth transition and detailed information, please consult our [Migration Guide](https://speedyk-005.github.io/chunklet-py/latest/migration/).

[![Python Version](https://img.shields.io/badge/Python-3.10%20--%203.14-blue)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/chunklet-py)](https://pypi.org/project/chunklet-py)
[![Coverage Status](https://coveralls.io/repos/github/speedyk-005/chunklet-py/badge.svg?branch=main)](https://coveralls.io/github/speedyk-005/chunklet-py?branch=main)
[![Stability](https://img.shields.io/badge/stability-stable-brightgreen)](https://github.com/speedyk-005/chunklet-py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](https://github.com/speedyk-005/chunklet-py/actions)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/speedyk-005/chunklet-py)

<p align="center">
  <a href="https://speedyk-005.github.io/chunklet-py/latest" target="_blank" rel="noopener noreferrer">
    -- documentation site --
  </a>
</p>

## Why Bother with Smart Chunking?

You might be thinking, 'Can't I just split my text or code with a simple character count or by arbitrary lines?' Well, you certainly *could*, but let's be frank – that's a bit like trying to perform delicate surgery with a butter knife! Standard splitting methods often lead to:

-   **Literary Butchery:** Sentences chopped mid-thought or code blocks broken mid-function, leading to a loss of crucial meaning.
-   **Monolingual Approach:** A disregard for the unique rules of non-English languages or the specific structures of programming languages.
-   **A Goldfish's Memory:** Forgetting the context of the previous chunk, resulting in disconnected ideas and a less coherent flow.

## 🤔 Why Chunklet-py? What is it, Anyway? (And Why Should You Care?)

**Chunklet-py** is a versatile and powerful library designed to intelligently segment various forms of content—from raw text to complex documents and source code—into perfectly sized, context-aware chunks. It goes beyond simple splitting, offering specialized tools:

*   `Sentence Splitter`
*   `Plain Text Chunker`
*   `Document Chunker`
*   `Code Chunker`

Each of these is tailored to preserve the original meaning and structure of your data.

Whether you're preparing data for Large Language Models (LLMs), developing Retrieval-Augmented Generation (RAG) pipelines, or enhancing AI-driven document search, Chunklet-py (version 2.0) provides the precision and flexibility needed for efficient indexing, embedding, and inference across multiple formats and languages.

| Feature | Why it’s great ? |
| :--- | :--- |
| 🚀 **Blazingly Fast** | Leverages efficient parallel processing to chunk large volumes of content with remarkable speed. |
| 🪶 **Featherlight Footprint** | Designed to be lightweight and memory-efficient, ensuring optimal performance without unnecessary overhead. |
| 🗂️ **Rich Metadata for RAG** | Enriches chunks with valuable, context-aware metadata (source, span, document properties, code AST details) crucial for advanced RAG and LLM applications. |
| 🔧 **Infinitely Customizable** | Offers extensive customization options, from pluggable token counters to custom sentence splitters and processors. |
| 🌐 **Multilingual Mastery** | Supports over 50 natural languages for text and document chunking with intelligent detection and language-specific algorithms. |
| 🧑‍💻 **Code-Aware Intelligence** | Language-agnostic code chunking that understands and preserves the structural integrity of your source code. |
| 🎯 **Precision Chunking** | Flexible constraint-based chunking allows you to combine limits based on sentences, tokens, sections, lines, and functions. |
| 📄 **Document Format Mastery** | Processes a wide array of document formats including `.pdf`, `.docx`, `.epub`, `.txt`, `.tex`, `.html`, `.hml`, `.md`, `.rst`, and `.rtf`. |
| 💻 **Dual Interface: CLI & Library** | Use it as a powerful command-line tool for fast, terminal-based chunking or import it as a library for deep integration into your Python applications. |


And there's even more to discover!

> [!NOTE]
> For the documentation, visit our [documentation site](https://speedyk-005.github.io/chunklet-py/latest).

---

## 📦 Installation

Ready to get Chunklet-py up and running? Fantastic! This guide will walk you through the installation process, making it as smooth as possible.

### The Easy Way

The most straightforward method to install Chunklet-py is by using `pip`:

```bash
# Install and verify version
pip install chunklet-py
chunklet --version
```

And that's all there is to it! You're now ready to start using Chunklet-py.

### Optional Dependencies

Chunklet-py offers optional dependencies to unlock additional functionalities, such as document processing or code chunking. You can install these extras using the following syntax:

*   **Document Processing:** For handling `.pdf`, `.docx`, `.epub`, and other document formats:
    ```bash
    pip install "chunklet-py[document]"
    ```
*   **Code Chunking:** For advanced code analysis and chunking features:
    ```bash
    pip install "chunklet-py[code]"
    ```
*   **All Extras:** To install all optional dependencies:
    ```bash
    pip install "chunklet-py[all]"
    ```

### The Alternative Way

For those who prefer to build from source, you can clone the repository and install it manually. This method allows for direct modification of the source code and installation of all optional features:

```bash
git clone https://github.com/speedyk-005/chunklet-py.git
cd chunklet-py
pip install .[all]
```

But why would you want to do that? The easy way is so much easier.

### Contributing to Chunklet-py

Interested in helping make Chunklet-py even better? That's fantastic! Before you dive in, please take a moment to review our [**Contributing Guide**](https://github.com/speedyk-005/chunklet-py/blob/main/CONTRIBUTING.md). Here's how you can set up your development environment:

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

These commands install Chunklet-py in "editable" mode, ensuring that any changes you make to the source code are immediately reflected. The `[dev]`, `[docs]`, and `[dev-all]` options include the necessary dependencies for specific development tasks.

Now, go forth and code! And remember, good developers always write tests. (Even in a Python project, we appreciate all forms of excellent code examples!)

---

## 🧪 Planned Features

- [x] CLI interface
- [x] Documents chunking with metadata.
- [x] Code chunking based on interest point.
- [ ] Visualization for chunks (e.g., highlighting spans in original documents)
- Extend the file supported:
  - [ ] Support for odt and eml files
  - [ ] Support for tabular: csv, excel, ...
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

Big thanks to the people who helped shape **Chunklet**:

- [@jmbernabotto](https://github.com/jmbernabotto) — for helping mostly on the CLI part, suggesting fixes, features, and design improvements.

---

📜 License

See the [LICENSE](https://github.com/speedyk-005/chunklet-py/blob/main/LICENSE) file for full details.

> MIT License. Use freely, modify boldly, and credit the legend (me. Just kidding!)
