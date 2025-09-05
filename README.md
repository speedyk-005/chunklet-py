# 🧩 Chunklet: Multi_strategy, Context-aware, Multilingual Text Chunker

---
<p align="center">
  <img src="https://github.com/speedyk-005/chunklet-py/blob/main/logo.png?raw=true" alt="Chunklet Logo" width="300"/>
</p>
---

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/chunklet-py)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/chunklet-py)](https://pypi.org/project/chunklet-py)
[![Stability](https://img.shields.io/badge/stability-stable-brightgreen)](https://github.com/Speedyk-005/chunklet-py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](https://github.com/speedyk-005/chunklet-py/actions)

> Chunk smarter, not harder — built for LLMs, RAG pipelines, and beyond.  
**Author:** speedyk_005  
**Version:** 1.4.0
**License:** MIT

For a detailed history of changes, please see the [Changelog](https://github.com/speedyk-005/chunklet-py/blob/main/CHANGELOG.md).


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

---

## 🧩 Chunking Modes

Pick your flavor:

- `"sentence"` — chunk by sentence count only # the minimum `max_sentences` is 1.
- `"token"` — chunk by token count only # The minimum `max_tokens` is 10
- `"hybrid"` — sentence + token thresholds respected with guaranteed overlap. Internally, the system estimates a residual capacity of 0-2 typical clauses per sentence to manage chunk boundaries effectively.  

---

## 🌍 Language Support (36+)

- **Primary (Pysbd):** Supports a wide range of languages for highly accurate sentence boundary detection.
  (e.g., ar, pl, ja, da, zh, hy, my, ur, fr, it, fa, bg, el, mr, ru, nl, es, am, kk, en, hi, de)
  For more information: [Pypi](https://pypi.org/project/pysbd/) 
- **Secondary (sentence_splitter):** Provides support for additional languages not covered by Pysbd.
  For more information: [Github](https://github.com/mediacloud/sentence-splitter) 
  (e.g., pt, no, cs, sk, lv, ro, ca, sl, sv, fi, lt, tr, hu, is)
- **Fallback (Smart Regex):** For any language not explicitly supported by the above, a smart regex-based splitter is used as a reliable fallback.

## 📦 Installation

Install `chunklet-py` easily from PyPI:

```bash
pip install chunklet-py
```

To install from source for development:

```bash
git clone https://github.com/Speedyk-005/chunklet-py.git
cd chunklet
pip install -e .
```

---
## Getting Started

See the [Getting Started](https://github.com/speedyk-005/chunklet-py/blob/main/docs/getting-started/index.md) guide to get started with Chunklet.

For the full documentation, visit our [documentation site](https://speedyk-005.github.io/chunklet-py/).

## Benchmarks

See [BENCHMARKS.md](https://github.com/speedyk-005/chunklet-py/blob/main/BENCHMARKS.md) for detailed performance benchmarks, and the [benchmark script](https://github.com/speedyk-005/chunklet-py/blob/main/benchmark.py) for the code used to generate them.

## Internal Workflow

See the [Internal Workflow](https://github.com/speedyk-005/chunklet-py/blob/main/docs/internal-flow.md) for a high-level overview of Chunklet's internal processing flow.

## Configuration Models

For detailed definitions, refer to the [Models](https://github.com/speedyk-005/chunklet-py/blob/main/docs/models.md) documentation.

## Troubleshooting & Reference

*   [**Exceptions and Warnings:**](https://github.com/speedyk-005/chunklet-py/blob/main/docs/exceptions-and-warnings.md) Understand the various errors and warnings Chunklet might throw your way, and how to deal with them.

## Changelog

See the [Changelog](https://github.com/speedyk-005/chunklet-py/blob/main/CHANGELOG.md) for a history of changes.

---

## 🧪 Planned Features

- [x] CLI interface with --file, --mode, --overlap-percent, etc.
- [x] Documents chunking with metadata.
- [ ] Code chunking based on interest point.

---

## 💡Projects that inspired me

| Tool                      | Description                                                                                      |
|---------------------------|--------------------------------------------------------------------------------------------------|
| [**Semchunk**](https://github.com/cocktailpeanut/semchunk)  | Semantic-aware chunking using transformer embeddings.                  |
| [**CintraAI Code Chunker**](https://github.com/CintraAI/code-chunker) | AST-based code chunker for intelligent code splitting.                 |
| [**semantic-chunker**](https://github.com/Goldziher/semantic-chunker) | A strongly-typed semantic text chunking library that intelligently splits content while preserving structure and meaning.                |

---

## 🤝 Contributing

Want to help make Chunklet even better? 

1. Fork this repo
2. Create a new feature branch
3. Code like a star
4. Submit a pull request
   
Check out the [issues](https://github.com/Speedyk-005/chunklet-py/issues) or open a PR!

See our [Contributing Guidelines](https://github.com/speedyk-005/chunklet-py/blob/main/CONTRIBUTING.md) for details.

---

## 🙌 Contributors & Thanks

Big thanks to the people who helped shape **Chunklet**:

- [@jmbernabotto](https://github.com/jmbernabotto) — for spotting lots of bugs 🐞 and even convincing me to add some cool features 🚀  

---

📜 License

See the [LICENSE](https://github.com/speedyk-005/chunklet-py/blob/main/LICENSE) file for full details.

> MIT License. Use freely, modify boldly, and credit the legend (me. Just kidding!)

 
