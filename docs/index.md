# Welcome to the Chunklet-py Documentation!

<p align="center">
  <img src="https://github.com/speedyk-005/chunklet-py/blob/main/images/logo_with_tagline.svg?raw=true" alt="Chunklet-py Logo" width="300"/>
</p>

“One library to split them all: Sentence, Code, Docs— RAG-ready, token-aware,
and multi-format.”

Hello there! Welcome to the official documentation for Chunklet-py. We're thrilled to have you here and excited to guide you through everything our library has to offer.

---

## Why Bother with Smart Chunking?

You might be thinking, 'Can't I just split my text or code with a simple character count or by arbitrary lines?' Well, you certainly *could*, but let's be frank – that's a bit like trying to perform delicate surgery with a butter knife! Standard splitting methods often lead to:

-   **Literary Butchery:** Sentences chopped mid-thought or code blocks broken mid-function, leading to a loss of crucial meaning.
-   **Monolingual Approach:** A disregard for the unique rules of non-English languages or the specific structures of programming languages.
-   **A Goldfish's Memory:** Forgetting the context of the previous chunk, resulting in disconnected ideas and a less coherent flow.

## 🤔 Why Chunklet-py? What is it, Anyway? (And Why Should You Care?)

**Chunklet-py** is your go-to solution for transforming large volumes of text and code into perfectly sized, context-aware chunks. It intelligently understands the structure of your content, employing clever techniques like clause-level overlapping for text and structural awareness for code, all to preserve the original meaning. Think of it as a meticulous curator, ensuring the integrity of your valuable data.

Whether you're preparing data for Large Language Models (LLMs), developing Retrieval-Augmented Generation (RAG) pipelines, or enhancing AI-driven document search, Chunklet-py (version 2.0) expertly manages the intricate process of text segmentation with remarkable precision. It ensures your data is RAG-ready, token-aware, and compatible with multiple formats, making it a top choice for efficient indexing, embedding, and inference.

Feature                  | Why it’s great  
------------------------|----------------
🌐 **Multilingual text chunking** | Supports over 50 languages with the help of robust third-party libraries and a reliable fallback splitter. It intelligently leverages language-specific algorithms and detection for broad coverage.
⚙️ **Language-agnostic Code Chunking** | Works seamlessly across a wide array of programming languages (including Python, C/C++, Java, C#, and many others) without needing language-specific grammars.
⛓️ **Hybrid Mode Text chunking**          | Offers the best of both worlds by supporting both token and sentence limits simultaneously, complete with guaranteed Clause-Level Overlap for text chunking – a feature rarely found even in commercial solutions.  
⚡ **Efficient Parallel Batch Processing** | Utilizes `Mpire` for efficient parallel processing, optimizing for fast batch chunking of your content.
 🔧 **Highly Customizable**  | Provides extensive customization options, including pluggable token counters, custom sentence splitters, and flexible custom processors for document registration.

And there's even more to discover!

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

## The Grand Tour

Wanna know what's under the hood?

*   [**Supported Languages:**](supported-languages.md) See which languages Chunklet speaks fluently.
*   [**Exceptions and Warnings:**](exceptions-and-warnings.md) Because sometimes, things go wrong. Here's what to do when they do.

## Keeping Up-to-Date 
 
 Stay informed about Chunklet's evolution:
 
 *   [**What's New:**](whats-new.md) Discover all the exciting new features and improvements in Chunklet 2.0.
 *   [**Migration Guide:**](migration.md) Learn how to smoothly transition from previous versions to Chunklet 2.0.
 
 *   [**Changelog:**](https://github.com/speedyk-005/chunklet-py/blob/main/CHANGELOG.md) See what's new, what's fixed, and what's been improved in recent versions.
 
 
## Project Information & Contributing For the serious stuff (and if you want to join the fun):
 
 *   [**GitHub Repository:**](https://github.com/speedyk-005/chunklet-py) The main hub for all things Chunklet.
 *   [**License Information:**](https://github.com/speedyk-005/chunklet-py/blob/main/LICENSE) All the necessary bits and bobs about Chunklet's license.
 *   [**Contributing:**](https://github.com/speedyk-005/chunklet-py/blob/main/CONTRIBUTING.md) Want to help make Chunklet even better? Find out how you can contribute!                                            