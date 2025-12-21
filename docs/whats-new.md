!!! info "What's on This Page"
    This page highlights the **big features and major changes** for each version. For all the nitty-gritty details, bug fixes, and technical improvements, check out our [full changelog](https://github.com/speedyk-005/chunklet-py/blob/main/CHANGELOG.md).

## What's New in Chunklet v2.1.1! 🐛

### 🐛 Critical Bug Fix in v2.1.1

*   **Visualizer Static Files Issue:** 🚨 **CRITICAL** - Fixed a breaking bug where the Chunk Visualizer static files (CSS, JS, HTML) were missing from the PyPI package distribution. This caused `RuntimeError: Directory does not exist` when running `chunklet visualize`. The visualizer now works correctly after installation!

---

## What's New in Chunklet v2.1.0! 🎉

### ✨ Major Features in v2.1.0

*   **Interactive Chunk Visualizer:** 🌐 Launch a web-based interface for real-time chunk visualization, parameter tuning, and exploring your chunking results interactively!
*   **CLI Visualize Command:** 💻 Use `chunklet visualize` to start the web interface with customizable host, port, and tokenizer options.
*   **Expanded File Format Support:** 📁 Added support for ODT files (.odt) and tabular files (.csv and .xlsx) to handle even more document types.

### 🐛 Bug Fixes in v2.1.0

*   **Code Chunker Issues:** 🔧 Fixed multiple bugs in CodeChunker including line skipping in oversized blocks, decorator separation, path detection errors, and redundant processing logic.
*   **CLI Path Validation Bug:** Resolved TypeError where len() was called on PosixPath object. Thanks to [@arnoldfranz](https://github.com/arnoldfranz) for reporting this issue.
*   **Hidden Bugs Uncovered:** 🕵️‍♂️ Adding comprehensive test coverage revealed and fixed multiple hidden bugs in document chunker batch processing error handling that were previously undetected.

---

# What's New in Chunklet v2.0.1! 🎉

### ✨ Patch Fixes in v2.0.1

- **CLI Bug Fix:** Fixed a tricky unpacking bug in the `split` command that was causing incorrect results. The fix properly separates language detection from sentence splitting for accurate output.

---

# What's New in Chunklet v2.0.3! 🎉

### ✨ Improvements in v2.0.3

*   **Enhanced Span Detection:** 🧭 Fixed some hardcoded limits and added adaptive calculations for better span detection across different text lengths.
*   **Improved Regex Performance:** ⚡ Switched from fuzzysearch to optimized regex for faster and more precise span finding.
*   **Dependency Cleanup:** 🧹 Removed the fuzzysearch dependency to keep things lighter and simpler.

---

# What's New in Chunklet v2.0.2! 🎉

### ✨ Refinements in v2.0.2

*   **Code Cleanup:** 🧹 Removed some debug print statements from the `SentenceSplitter` for cleaner production code.

---

# What's New in Chunklet v2.0.0! 🎉

### ✨ Highlights of v2.0.0

*   **Class Renaming:** The `Chunklet` class has been renamed to `PlainTextChunker` for clearer naming. Don't worry about updating your code - our [Migration Guide](migration.md) has you covered!
*   **Continuation marker:** 📑 Improved the continuation marker logic and exposed its value so you can define your own or disable it entirely.
*   **Code Chunker Introduction:** We're excited to introduce `CodeChunker`! 🧑‍💻 This new rule-based, language-agnostic chunker provides smart syntax-aware code splitting - perfect for code-related RAG applications.
*   **Document Chunker Introduction:** We're pleased to introduce `DocumentChunker`! 📄 This robust tool handles a wide variety of file formats including PDF, DOCX, TXT, MD, RST, RTF, TEX, HTML, and EPUB files.
*   **Expanded Language Support:** ¡Hola! Bonjour! Namaste! 🗣️ We've expanded from 36+ to over 50 languages thanks to our library integrations and smart fallback mechanisms.
*   **New Constraint Flags:** Added `max_section_breaks` for PlainTextChunker and DocumentChunker, plus `max_lines` for CodeChunker - giving you more precise control over chunking.
*   **Improved Error Handling:** Added more specific exception types (like `FileProcessingError` and `CallbackError`) and centralized batch error handling for clearer feedback and better control.
*   **Flexible Batch Error Handling:** The new `on_errors` parameter lets you control what happens when errors occur in batches - you can `raise`, `skip`, or `break` as needed.
*   **CLI Refactoring:** Streamlined the command-line interface with simplified flags and improved batch processing capabilities for a smoother experience.
*   **Modularity & Extensibility:** Made the library more modular with a dedicated `SentenceSplitter` and flexible custom splitter registry for easier customization.
*   **Performance & Memory Optimization:** Significant refactoring with generators for batch methods to drastically reduce memory usage, especially for large documents.
*   **Caching Strategy Refined:** We've gone lean and mean! ♻️ Removed most in-memory caching to prioritize performance, keeping only `count_tokens` cached.
*   **Python 3.8/3.9 Support Dropped:** Time marches on, and so do we! 🕰️ Dropped official support for Python 3.8 and 3.9 - minimum version is now 3.10.
*   **CLI Flags Deprecation (--no-cache, --batch, --mode):** Cleaned up the CLI by removing redundant flags for a simpler interface.


## 🗺️ Curious About Our Journey?

For a complete list of all changes, fixes, and improvements across versions, check out our detailed [Changelog](https://github.com/speedyk-005/chunklet-py/blob/main/CHANGELOG.md) - it's got all the technical details!