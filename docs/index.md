# Welcome to the Chunklet-py Documentation!

<p align="center">
  <img src="img/logo_with_tagline.png" alt="Chunklet-py Logo" width="300"/>
</p>

“One library to split them all: Sentence, Code, Docs.”

Hey there! Welcome to the Chunklet-py docs. We're stoked you're here - let's make some text chunking magic happen together! ✨

---

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

Each tool is designed to keep your content's meaning and structure intact, plus we've got an interactive visualizer so you can see your chunks in real-time.

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

    Flexible constraint-based chunking allows you to combine limits based on sentences, tokens, sections, lines, and functions.

- :material-hexagon-multiple-outline:{ .lg .middle } __Triple Interface: CLI, Library & Web__

    Use it as a command-line tool, import as a library for deep integration, or launch the interactive web visualizer for real-time chunk exploration and parameter tuning.

</div>


---

## Ready to Get Started? Let's Make Some Chunks! 🚀

Welcome aboard! You're about to turn unruly walls of text into neat, manageable chunks. No more text-wrangling nightmares - Chunklet-py has your back!

Here's your quick start guide:

*   [**Installation:**](getting-started/installation.md) Get Chunklet-py running in minutes - seriously, it's that easy!

*   **Pick Your Path:**
    Got a preferred way of working? We've got you covered:

    *   **CLI Fan?** Love the terminal and instant results? The command line interface is perfect for quick tasks and scripting.
        *   [Check out CLI Usage](getting-started/cli.md)

    *   **Code Ninja?** Want to integrate chunking into your Python projects? The library approach gives you full control.
        *   [Explore Programmatic Usage](getting-started/programmatic/index.md)

Whatever you choose, we're here to make chunking as smooth and maybe even a little fun. Let's do this!

## How Does Chunklet-py Stack Up?

Wondering how we compare to other chunking tools? Chunklet-py brings a unique mix of versatility, speed, and simplicity. Here's the quick comparison:

| Library | Key Differentiator | Focus |
| :--- | :--- | :--- |
| **chunklet-py** | **All-in-one, lightweight, and language-agnostic with specialized algorithms.** | **Text, Code, Docs** |
| [CintraAI Code Chunker](https://github.com/CintraAI/code-chunker) | Relies on `tree-sitter`, which can add setup complexity. | Code |
| [Chonkie](https://github.com/chonkie-inc/chonkie) | A feature-rich pipeline tool with cloud/vector integrations, but uses a more basic sentence splitter and `tree-sitter` for code. | Pipelines, Integrations |
| [code_chunker (JimAiMoment)](https://github.com/JimAiMoment/code-chunker) | Uses basic regex and rules with limited language support. | Code |
| [Semchunk](https://github.com/isaacus-dev/semchunk) | Primarily for text, using a general-purpose sentence splitter. | Text |

Chunklet-py uses smart rule-based approaches that skip heavy dependencies (looking at you, tree-sitter!) and potential compatibility headaches. Our sentence splitting uses specialized algorithms for better accuracy, and the interactive visualizer lets you tweak settings in real-time. Perfect for projects that want power, flexibility, and a lightweight footprint.

## The Full Tour

Curious about all the features?

*   [**Supported Languages:**](supported-languages.md) See which languages Chunklet speaks fluently.
*   [**Exceptions and Warnings:**](exceptions-and-warnings.md) Because sometimes, things go wrong. Here's what to do when they do.
*   [**Metadata:**](getting-started/metadata.md) Understand the rich context `chunklet` attaches to your chunks.
*   [**Troubleshooting:**](troubleshooting.md) Solutions to common issues you might encounter.

## Stay in the Loop

Want to keep up with Chunklet-py's latest adventures?

  *   [**What's New:**](whats-new.md) Discover all the exciting new features and improvements in Chunklet 2.1.0.
  *   [**Migration Guide:**](migration.md) Learn how to smoothly transition from previous versions to Chunklet 2.x.x.

 *   [**Changelog:**](https://github.com/speedyk-005/chunklet-py/blob/main/CHANGELOG.md) See what's new, what's fixed, and what's been improved in recent versions.


## 🗺 What's Working & What's Next

**Already rocking these features:**
- [x] CLI interface for quick chunking
- [x] Document chunking with rich metadata
- [x] Smart code chunking that respects structure
- [x] Interactive web visualizer
- [x] Bonus file formats: ODT, CSV, Excel

**Coming soon (we're excited about these!):**
- [ ] Even more document formats

---

## Project Details & Join the Fun

For the behind-the-scenes info and if you're thinking of contributing:

 *   [**GitHub Repository:**](https://github.com/speedyk-005/chunklet-py) The main hub for all things Chunklet.
 *   [**License Information:**](https://github.com/speedyk-005/chunklet-py/blob/main/LICENSE) All the necessary bits and bobs about Chunklet's license.
 *   [**Contributing:**](https://github.com/speedyk-005/chunklet-py/blob/main/CONTRIBUTING.md) Want to help make Chunklet even better? Find out how you can contribute!                                            
