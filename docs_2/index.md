# Welcome to the Chunklet-py Documentation!

[![](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/speedyk-005/chunklet-py)

<p align="center">
  <img src="https://github.com/speedyk-005/chunklet-py/blob/main/logo.png?raw=true" alt="Chunklet-py Logo" width="300"/>
</p>

**Chunklet-py** – The Ultimate Text & Code Chunker

“One library to split them all: Sentence, Code, Docs— RAG-ready, token-aware,
and multi-format.”

---

## Why Bother with Fancy Chunking?

Look, you *could* just split your text or code by character count or arbitrary lines. But let's be honest, that's like performing surgery with a butter knife. Standard splitting methods often:

-   **Commit literary butchery:** They'll chop sentences mid-thought or code blocks mid-function, losing crucial meaning.
-   **Get lost in translation:** They don't care about the rules of non-English languages or the specific structures of programming languages.
-   **Have the memory of a goldfish:** They forget the context of the previous chunk, leaving you with a mess of disconnected ideas in natural language.

## 🤔 Why Chunklet-py? What is it, Anyway? (And Why Should You Care?)

**Chunklet-py** is your ultimate solution for transforming vast amounts of text and code into perfectly sized, context-aware chunks. It understands the structure of your text and code, using fancy tricks like clause-level overlapping for text and structural awareness for code, to keep the meaning intact. It's like a linguistic artist, carefully preserving the masterpiece that is your data.

Whether you're preparing data for Large Language Models (LLMs), building Retrieval-Augmented Generation (RAG) pipelines, or powering AI-driven document search, Chunklet 2.0 handles the complex task of text segmentation with unparalleled precision. It ensures your data is RAG-ready, token-aware, and multi-format compatible, making it the #1 choice for efficient indexing, embedding, and inference.

Feature                  | Why it’s elite  
------------------------|----------------
🌐 **Multilingual text chunking** | Officiall support 40+ languages with the help of third-party libs and a fallback splitter. Leverages language-specific algorithms and detection for broad coverage.
🧑‍💻 **agnostic Code Chunking** | Works across Python, C/C++, Java, C#, and others (30+) without requiring language-specific grammars.
⛓️ **Hybrid Mode Text chunking**          | Support token + sentence limits contrainst at the same time with guaranteed Clause-Level Overlap for text chunking — rare even in commercial stacks.  
⚡ **Parallel Batch Processing** | Efficient parallel processing with `Mpire`, optimized for fast batch chunking.
 🔧 **Very Customizable**  | Pluggable Token Counters, custom sentence splitters and custom processors for documents registration.

---

## Ready to Dive In?

Here's how to get your hands dirty:

*   [**Installation:**](installation.md) Get Chunklet on your machine. We've made it as painless as possible.
*   [**Getting Started (CLI & Programmatic):**](getting-started/index.md) Whether you're a command-line cowboy or a Python purist, we've got you covered.

## The Grand Tour

Wanna know what's under the hood?

*   [**Supported Languages:**](supported-languages.md) See which languages Chunklet speaks fluently.
*   [**Utility Functions:**](utils.md) The secret sauce that makes Chunklet so powerful.
*   [**Exceptions and Warnings:**](exceptions-and-warnings.md) Because sometimes, things go wrong. Here's what to do when they do.

 ## Keeping Up-to-Date 
 
 Stay informed about Chunklet's evolution:
 
 *   [**Migration Guide:**](migration.md) Learn how to smoothly transition from previous versions to Chunklet 2.0.
 *   [**Changelog:**](https://github.com/speedyk-005/chunklet-py/blob/main/CHANGELOG.md) See what's new, what's fixed, and what's been improved in recent versions.
 *   [**Benchmarks:**](https://github.com/speedyk-005/chunklet-py/blob/main/BENCHMARKS.md) Curious about performance? Check out how Chunklet stacks up.
 
 ## Project Information & Contributing For the serious stuff (and if you want to join the fun):
 
 *   [**GitHub Repository:**](https://github.com/speedyk-005/chunklet-py) The main hub for all things Chunklet.
 *   [**License Information:**](https://github.com/speedyk-005/chunklet-py/blob/main/LICENSE) All the necessary bits and bobs about Chunklet's license.
 *   [**Contributing:**](https://github.com/speedyk-005/chunklet-py/blob/main/CONTRIBUTING.md) Want to help make Chunklet even better? Find out how you can contribute!                                            