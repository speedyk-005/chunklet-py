# Chunklet-py Docs

<p align="center">
  <img src="img/logo_with_tagline.png" alt="Chunklet-py Logo" width="300"/>
</p>

“One library to split them all: Sentence, Code, Docs.”

Hey! Welcome to the Chunklet-py docs. Let's make some text chunking magic happen.

---

## Why Smart Chunking? (Or: Why Not Just Split on Character Count?)

You could split your text by character count or random line breaks. But that's like trying to cut a wedding cake with a chainsaw. 🎂

Dumb splitting causes problems:

- **Mid-sentence surprises:** Your thoughts get chopped mid-way, losing all meaning
- **Language confusion:** Non-English text and code structures get treated the same
- **Lost context:** Each chunk forgets what came before

Smart chunking solves this by:

- **Smart limits** — Respects both natural boundaries (sentences, paragraphs, sections) AND configurable limits (tokens, lines, functions)
- **Language-aware** — Detects language automatically and applies the right rules (50+ languages supported)
- **Context preservation** — Overlap between chunks, rich metadata (source, span, document structure)

## 🤔 So What's Chunklet-py Anyway? (And Why Should You Care?)

**Chunklet-py** is a developer-friendly text splitting library designed to be the most versatile chunking solution — for devs, researchers, and AI engineers. It goes way beyond basic character counting. I built this because I was tired of terrible chunking options. Chunklet-py intelligently chunks text, documents, and code into meaningful, context-aware pieces — perfect for RAG pipelines and LLM applications.

Key features:

- **Composable constraints** — Mix and match limits (sentences, tokens, sections) to get exactly the chunks you need
- **Pluggable architecture** — Swap in custom tokenizers, sentence splitters, or processors  
- **Rich metadata** — Every chunk comes with source references, spans, and structural info
- **Multi-format support** — PDF, DOCX, EPUB, Markdown, HTML, LaTeX, ODT, CSV, Excel, and plain text

Available tools:

- `SentenceSplitter` — Lightweight sentence tokenization
- `DocumentChunker` — Natural language with semantic boundaries
- `CodeChunker` — Language-aware code chunking
- `ChunkVisualizer` — Interactive web-based exploration

Perfect for prepping data for LLMs, building RAG systems, or powering AI search - Chunklet-py gives you the precision and flexibility you need across tons of formats and languages.

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

    Flexible chunking with configurable limits based on sentences, tokens, sections, lines, and functions.

- :material-hexagon-multiple-outline:{ .lg .middle } __Triple Interface: CLI, Library & Web__

    Use it as a command-line tool, import as a library for deep integration, or launch the interactive web visualizer for real-time chunk exploration and parameter tuning.

</div>


---

## How Does Chunklet-py Stack Up?

Wondering how we compare to other chunking tools? Here's the quick comparison:

| Library | Key Differentiator | Focus |
| :--- | :--- | :--- |
| **chunklet-py** | **All-in-one, lightweight, multilingual, language-agnostic with specialized algorithms.** | **Text, Code, Docs** |
| [LangChain](https://github.com/langchain-ai/langchain) | Full LLM framework with basic splitters (e.g., RecursiveCharacterTextSplitter, Markdown, HTML, code splitters). Good for prototyping but basic for complex docs or multilingual needs. | Full Stack |
| [Chonkie](https://github.com/chonkie-inc/chonkie) | All-in-one pipeline (chunking + embeddings + vector DB). Uses `tree-sitter` for code. Multilingual. | Pipelines |
| [Semchunk](https://github.com/isaacus-dev/semchunk) | Text-only, fast semantic splitting. Built-in tiktoken/HuggingFace support. 85% faster than alternatives. | Text |
| [CintraAI Code Chunker](https://github.com/CintraAI/code-chunker) | Code-specific, uses `tree-sitter`. Initially supports Python, JS, CSS only. | Code |

Chunklet-py is a specialized, drop-in replacement for the chunking step in any RAG pipeline. It handles text, documents, and code without heavy dependencies, while keeping your project lightweight.

## Ready? Let's Go!

Pick your path:

*   [**Installation:**](getting-started/installation.md) Get Chunklet-py running in minutes
*   **CLI Fan?** The command line interface is perfect for quick tasks.
    *   [CLI Usage](getting-started/cli.md)
*   **Code Ninja?** Want to integrate chunking into your Python projects?
    *   [Programmatic Usage](getting-started/programmatic/index.md)

## The Full Tour

Curious about all the features?

*   [**Supported Languages:**](supported-languages.md) See which languages Chunklet speaks fluently.
*   [**Exceptions and Warnings:**](exceptions-and-warnings.md) Because sometimes, things go wrong. Here's what to do when they do.
*   [**Metadata:**](getting-started/metadata.md) Understand the rich context `chunklet` attaches to your chunks.
*   [**Troubleshooting:**](troubleshooting.md) Solutions to common issues you might encounter.

## Stay in the Loop

Want to keep up with Chunklet-py's latest adventures?

  *   [**What's New:**](whats-new.md) Discover all the exciting new features and improvements in Chunklet 2.2.0.
  *   [**Migration Guide:**](migration.md) Learn how to smoothly transition from previous versions to Chunklet 2.x.x.

 *   [**Changelog:**](https://github.com/speedyk-005/chunklet-py/blob/main/CHANGELOG.md) See what's new, what's fixed, and what's been improved in recent versions.


## Project Details & Join the Fun

For the behind-the-scenes info and if you're thinking of contributing:

 *   [**GitHub Repository:**](https://github.com/speedyk-005/chunklet-py) The main hub for all things Chunklet.
 *   [**License Information:**](https://github.com/speedyk-005/chunklet-py/blob/main/LICENSE) All the necessary bits and bobs about Chunklet-py's license.
 *   [**Contributing:**](https://github.com/speedyk-005/chunklet-py/blob/main/CONTRIBUTING.md) Want to help make Chunklet even better? Find out how you can contribute!                                            
