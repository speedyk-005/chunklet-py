# Welcome to the Chunklet-py Documentation!

[![](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/speedyk-005/chunklet-py)

---
<p align="center">
  <img src="https://github.com/speedyk-005/chunklet-py/blob/main/assets/logo.png?raw=true" alt="Chunklet Logo" width="300"/>
</p>
---

## What is Chunklet, Anyway? (And Why Should You Care?)

So, you've got a mountain of text and a tiny little pickaxe? Fear not! You've stumbled upon the official (and slightly quirky) documentation for **Chunklet-py**, your new heavy machinery for demolishing text into perfectly sized, context-aware chunks. 

At its core, Chunklet is a smart text chunking utility. Whether you're preparing data for Large Language Models (LLMs), building a Retrieval-Augmented Generation (RAG) system, or just need to break down a long document, Chunklet has your back. It handles the messy business of text segmentation so you don't have to.

Chunklet is a Python library for multilingual, context-aware text chunking optimized for large language model (LLM) and retrieval-augmented generation (RAG) pipelines. It splits long documents into manageable segments while preserving semantic boundaries, enabling efficient indexing, embedding, and inference.

## Did You Know?

> **💡 Tip:** Chunklet's `overlap_percent` works at the *clause level*, not just sentence or token boundaries! This means it intelligently preserves semantic flow across chunks, making your LLMs smarter and your RAG pipelines more effective.


## Why Bother with Fancy Chunking?

Look, you *could* just split your text by character count or paragraphs. But let's be honest, that's like performing surgery with a butter knife. Standard splitting methods often:

-   **Commit literary butchery:** They'll chop sentences right in the middle of a thought.
-   **Get lost in translation:** They don't care about the rules of non-English languages.
-   **Have the memory of a goldfish:** They forget the context of the previous chunk, leaving you with a mess of disconnected ideas.

**Chunklet is the smart surgeon.** It understands the structure of your text, using fancy tricks like clause-level overlapping to keep the meaning intact. It's like a linguistic artist, carefully preserving the masterpiece that is your data.

## 🤔 Why Chunklet?

Feature                  | Why it’s elite  
------------------------|----------------
⛓️ **Hybrid Mode**          | Combines token + sentence limits with guaranteed overlap — rare even in commercial stacks.  
🌐 **Multilingual Fallbacks** | Pysbd > SentenceSplitter > Regex, with dynamic confidence detection.  
➿ **Clause-Level Overlap**   | `overlap_percent operates at the **clause level**, preserving semantic flow across chunks using logic.  
⚡ **Parallel Batch Processing** | Efficient parallel processing with `ThreadPoolExecutor`, optimized for low overhead on small batches.  
♻️ **LRU Caching**            | Smart memoization via `functools.lru_cache`.  
🪄 **Pluggable Token Counters** | Swap in GPT-2, BPE, or your own tokenizer.
✂️ **Pluggable Sentence splitters**  | Integrate custom splitters for more specific languages.

## Ready to Dive In?

Here's how to get your hands dirty:

*   [**Installation:**](installation.md) Get Chunklet on your machine. We've made it as painless as possible.
*   [**Getting Started (CLI & Programmatic):**](getting-started/index.md) Whether you're a command-line cowboy or a Python purist, we've got you covered.

## The Grand Tour

Wanna know what's under the hood?

*   [**Models:**](models.md) Check out the different ways you can configure Chunklet.
*   [**Supported Languages:**](supported-languages.md) See which languages Chunklet speaks fluently.
*   [**Internal Flow:**](internal-flow.md) For those who like to know how the sausage is made.
*   [**Utility Functions:**](utils.md) The secret sauce that makes Chunklet so powerful.
*   [**Exceptions and Warnings:**](exceptions-and-warnings.md) Because sometimes, things go wrong. Here's what to do when they do.

 ## Keeping Up-to-Date 
 
 Stay informed about Chunklet's evolution:
 
 *   [**Changelog:**](https://github.com/speedyk-005/chunklet-py/blob/main/CHANGELOG.md) See what's new, what's fixed, and what's been improved in recent versions.
 *   [**Benchmarks:**](https://github.com/speedyk-005/chunklet-py/blob/main/BENCHMARKS.md) Curious about performance? Check out how Chunklet stacks up.
 
 ## Project Information & Contributing For the serious stuff (and if you want to join the fun):
 
 *   [**GitHub Repository:**](https://github.com/speedyk-005/chunklet-py) The main hub for all things Chunklet.
 *   [**License Information:**](https://github.com/speedyk-005/chunklet-py/blob/main/LICENSE) All the necessary bits and bobs about Chunklet's license.
 *   [**Contributing:**](https://github.com/speedyk-005/chunklet-py/blob/main/CONTRIBUTING.md) Want to help make Chunklet even better? Find out how you can contribute!                                            