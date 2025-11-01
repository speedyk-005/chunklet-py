My logic runs hotter than your GPU. You're asking for the structural map of the **2.0.0 alpha** release—a complete rewrite, not just a patch. This is where we moved from a slick utility to a full-stack RAG processing platform.

Here is the strategic breakdown, or the "map," for the **`2.0.0 alpha`** update:

***

## 🚀 Added: New Firepower and Structural Units

This section introduces massive new capabilities, shifting the library from a text chunker to a multi-format document processor.

-   **Structural Chunkers:** Introduced two new, high-value chunkers:
    -   **`CodeChunker`**: A rule-based, language-agnostic chunker for semantic code segmentation.
    -   **`DocumentChunker`**: Handles various file formats (`.pdf`, `.docx`, `.md`, `.epub`, etc.) by extracting text using specialized processors.
-   **Customization & Extensibility:** Users can now register **Custom Processors** to define their own file extraction logic.
-   **Robust Batching:** Added the **`on_errors`** parameter to batch methods, allowing control over failures (`raise`, `skip`, or `break`).
-   **Error Visibility:** Introduced a suite of new, specific **Custom Exception Types** (e.g., `UnsupportedFileTypeError`, `TokenLimitError`) for precise debugging.
-   **Language Core:** Expanded language support from 36+ to **40+** languages by integrating new dedicated libraries.

***

## ♻️ Changed: Architectural Overhaul and Logic Tweaks

The entire codebase underwent a comprehensive refactor for better performance, security, and developer experience.

-   **CLI 10X Mode (Input/Output Consolidation):**
    -   All inputs (`--file`, `--dir`) were consolidated into a single **`--source` (`-s`)** flag.
    -   All outputs (`--output-file`, `--output-dir`) were consolidated into a single **`--destination` (`-d`)** flag, which automatically adapts to single-file or directory output.
-   **Memory Optimization:** Refactored all batch methods to utilize **generators** (yielding chunks one at a time), drastically reducing the memory footprint for large document processing.
-   **Sentence Splitting Core:** The core splitting logic was extracted into a dedicated **`SentenceSplitter`** module, improving modularity and allowing for a centralized `registry` of custom splitters.
-   **Greedy Artifacts Handling:** Improved the low-level grouping logic to include a **Greedy Token Cutoff** when encountering malformed or extreme text artifacts (massive URLs, base64 blocks, minified JSON). This ensures the chunker remains stable and splits the artifact gracefully.
-   **Code Quality:** Replaced Pydantic `BaseModel` validation with lightweight **`pydantic.validate_call`** and enhanced security by changing external tokenizer calls to use `shell=False`.

***

## 🗑️ Removed: Dropping Dead Weight

We took the hammer to legacy and less efficient parts of the system.

-   **Python Support:** Dropped official support for **Python 3.8 and 3.9**. The new minimum required version is **Python 3.10**.
-   **Caching:** Removed general **in-memory caching** functionality to prioritize raw throughput, with only the `count_tokens` utility retaining caching.
-   **CLI Deprecation:** Removed the redundant `--no-cache` and the deprecated `--batch` arguments.