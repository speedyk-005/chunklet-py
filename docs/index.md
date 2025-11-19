# Welcome to the Chunklet-py Documentation!

<p align="center">
  <img src="img/logo_with_tagline.png" alt="Chunklet-py Logo" width="300"/>
</p>

“One library to split them all: Sentence, Code, Docs.”

Hello there! Welcome to the official documentation for Chunklet-py. We're thrilled to have you here and excited to guide you through everything our library has to offer.

---

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

<div class="grid cards" markdown>

- :material-speedometer:{ .lg .middle } __Blazingly Fast__

    Leverages efficient parallel processing to chunk large volumes of content with remarkable speed.

- :fontawesome-solid-feather:{ .lg .middle } __Featherlight Footprint__

    Designed to be lightweight and memory-efficient, ensuring optimal performance without unnecessary overhead.

- :material-database-marker-outline:{ .lg .middle } __Rich Metadata for RAG__

    Enriches chunks with valuable, context-aware metadata (source, span, document properties, code AST details) crucial for advanced RAG and LLM applications.

- :material-tune:{ .lg .middle } __Infinitely Customizable__

    Offers extensive customization options, from pluggable token counters to custom sentence splitters and processors.

- :material-translate:{ .lg .middle } __Multilingual Mastery__

    Supports over 50 natural languages for text and document chunking with intelligent detection and language-specific algorithms.

- :material-code-tags:{ .lg .middle } __Code-Aware Intelligence__

    Language-agnostic code chunking that understands and preserves the structural integrity of your source code.

- :material-ruler-square:{ .lg .middle } __Precision Chunking__

    Flexible constraint-based chunking allows you to combine limits based on sentences, tokens, sections, lines, and functions.

- :material-console-line:{ .lg .middle } __Dual Interface: CLI & Library__

    Use it as a powerful command-line tool for fast, terminal-based chunking or import it as a library for deep integration into your Python applications.

</div>


---

## Ready to Dive In? 🚀 Your Chunklet Adventure Awaits!

Welcome, brave adventurer, to the Chunklet starter pack! You've taken the first step towards taming unruly texts and transforming them into bite-sized, manageable chunks. No more wrestling with massive strings of words – Chunklet is here to make your life (and your LLMs' lives) a whole lot easier.

Here's how to get your hands dirty and unleash the power of Chunklet-py:

*   [**Installation:**](getting-started/installation.md) Our super-easy, step-by-step guide to get Chunklet-py up and running on your system. No pain, all gain!

*   **Choose Your Own Adventure: CLI or Code?**
    Chunklet offers two main paths to text-chunking glory. Pick the one that suits your style:

    *   **Command Line Interface (CLI):** For the terminal aficionados and those who prefer quick, direct action. If you like typing commands and seeing immediate results, this is your jam.
        *   [Dive into CLI Usage](getting-started/cli.md)

    *   **Programmatic Usage:** For the developers, the scripters, and those who want to integrate Chunklet's power directly into their Python applications. If you prefer writing code and building custom workflows, this path is for you.
        *   [Explore Programmatic Usage](getting-started/programmatic/index.md)

No matter which path you choose, Chunklet is designed to make text chunking as painless (and perhaps, as entertaining) as possible. Let's get chunking!

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

## The Grand Tour

Wanna know what's under the hood?

*   [**Supported Languages:**](supported-languages.md) See which languages Chunklet speaks fluently.
*   [**Exceptions and Warnings:**](exceptions-and-warnings.md) Because sometimes, things go wrong. Here's what to do when they do.
*   [**Metadata:**](getting-started/metadata.md) Understand the rich context `chunklet` attaches to your chunks.
*   [**Troubleshooting:**](troubleshooting.md) Solutions to common issues you might encounter.

## Keeping Up-to-Date

 Stay informed about Chunklet's evolution:

 *   [**What's New:**](whats-new.md) Discover all the exciting new features and improvements in Chunklet 2.0.
 *   [**Migration Guide:**](migration.md) Learn how to smoothly transition from previous versions to Chunklet 2.0.

 *   [**Changelog:**](https://github.com/speedyk-005/chunklet-py/blob/main/CHANGELOG.md) See what's new, what's fixed, and what's been improved in recent versions.


## 🧪 Planned Features

- [x] CLI interface
- [x] Documents chunking with metadata.
- [x] Code chunking based on interest point.
- [ ] Visualization for chunks (e.g., highlighting spans in original documents)
- Extend the file supported:
  - [ ] Support for odt and eml files
  - [ ] Support for tabular: csv, excel, ...

---

## Project Information & Contributing For the serious stuff (and if you want to join the fun):

 *   [**GitHub Repository:**](https://github.com/speedyk-005/chunklet-py) The main hub for all things Chunklet.
 *   [**License Information:**](https://github.com/speedyk-005/chunklet-py/blob/main/LICENSE) All the necessary bits and bobs about Chunklet's license.
 *   [**Contributing:**](https://github.com/speedyk-005/chunklet-py/blob/main/CONTRIBUTING.md) Want to help make Chunklet even better? Find out how you can contribute!                                            
