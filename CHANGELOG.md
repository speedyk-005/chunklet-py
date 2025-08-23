# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),  
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.3.1] - 2025-08-23

### Added
- Added an example for PDF chunking.
- Added a `try...except` block for `pypdf` import in the example.
- Updated the `README.md` to include the PDF chunking example and added it to the ToC.

### Fixed
- Refactored 'match' statement to 'if/elif/else' for Python 3.9 compatibility.
- Fixed a warning in `core.py` where `language` was used instead of `lang`.

---

## [1.3.0] - 2025-08-21

### Added

- **Custom Sentence Splitters:** Added support for integrating custom sentence splitting functions, allowing users to define their own logic for specific languages or requirements.
- **Robust fallback splitter:** Switched to a simpler, more robust and predictable sentence splitter fallback. Reduced over splitting and merging.  
- **Custom Exception Types:** Introduced `ChunkletError`, `InvalidInputError`, and `TokenNotProvidedError` for more specific and robust error handling across the library.
- **Progress Bar for Batch Processing**: Visual feedback for batch processing with a `rich` progress bar.
- **Faster batching**: On `n_jobs=1`, mpire is not used to prevent overheads. on `n_jobs>=2` batch are process with group of 2 per process. 

### Changed

- **Fault-Tolerant Batch Processing**: In batch mode, if a task fails, `chunklet` will now stop processing and return the results of the tasks that completed successfully, preventing wasted work.
- **_get_overlap_clauses Logic:** Simplified the logic for calculating overlap clauses by filtering empty clauses and improving the capitalization check.
- **Improved fallback splitter:** Used `p{Lu}`, `p{Ll}` in `regex_splitter.py` to identify and handle abbreviations and acronyms more accurately across different languages.                
- **Token Counter Error Handling:** Enhanced robustness by introducing a helper method to safely count tokens and handle potential errors from user-provided token counters. On error, operation is aborted.
- **LRU Cache Optimization:** Increased `lru_cache` maxsize from 25 to 256 for improved caching performance.
- **`preview_sentences` Enhanced Output:** The `preview_sentences` function now returns a tuple containing the list of sentences and any warnings encountered during processing, allowing for better insight into potential issues.
  
### Fixed

- **Critical Bug Fixes:** Addressed an `IndexError` in overlap calculation and other bugs.


## [1.2.0] - 2025-08-19

### Added

- **Custom Tokenizer Command:** Introduced a `--tokenizer-command` CLI argument to allow users to define a custom shell command for token counting.
- **Input Validation:** Enforced a minimum value of 1 for `max_sentences` and 10 for `max_tokens`. Overlap percentage is cap at maximum to 75.
  
### Changed

- **Parallel Processing Implementation:** Replaced `concurrent.futures.ThreadPoolExecutor` with `mpire` for batch processing, leveraging true multiprocessing for improved performance.
- **Fallback Splitter Enhancement:** Improved the fallback splitter logic  to split more logically and handle more edge cases. That ensure about 18.2 % more accuracy.
- **Language Detection Refinement:** detect_text_language now internally trims the ranked results to the top 10 candidates and uses a more stable normalization method, improving accuracy and reliability for ambiguous or short texts.
- **Simplified & Smarter Grouping Logic**: Simplified the grouping logic by eliminating unnecessary steps. The algorithm now split sentence further into clauses to ensure more logical overlap calculation and balanced groupings. The original formatting of the text is prioritized.
- **Default Overlap Percentage:** Increased the default `overlap_percent` from 10% to 20% for `chunk`, `_chunk`, and `_chunk_cached` methods to ensure consistency.
- **Regex Pattern Construction:** Replaced string concatenation with f-strings for creating regex patterns to improve readability and maintainability.
- **Refactoring** Refactored some logics to be more concise in the codebase.
- **Documentation:** Improved code clarity by enhancing docstrings and adding more comments throughout the codebase. Updated the `README.md` with a new table of contents, revised examples, and other improvements.
- **Enhanced Verbosity:** Emits a higher number of logs when `verbose` is set to true to improve traceability.
- **Aggregated Logging:** Warnings from parallel processing runs are now aggregated and displayed with a repetition count for better readability.
- **Testing:** Improved the test suite by prioritizing quality over quantity, resulting in more robust and meaningful tests.

### Removed

- **Invalid Import:** Removed an erroneous import of `simple_token_counter` in `cli.py` that was causing an `ImportError`.
- **Unused Parameter:** Deleted the unused `verbose` parameter from the `batch_chunk` method in `core.py`.
- **Unused File:** Deleted the `presets.py_` file, which was no longer needed.
- **Unused Import:** Removed an unused `import sys` statement.

### Fixed

- **Logo Rendering:** Corrected issues with the display of the project logo.
- **Clause Splitting:** Rewrote the clause detection pattern to ensure more accurate and reliable splitting of sentences.

---

## [1.1.0] - 2025-08-13

### Changed

- **Primary sentence splitter replaced:** Replaced `sentsplit` with `pysbd` for improved sentence boundary detection.
- **Language Detection Engine:** Migrated from `langid` to `py3langid` due to significant performance improvements (~40× faster in benchmarks) while maintaining identical accuracy and confidence scores. This change greatly reduces classification latency in multilingual processing workflows.
- **Language Support:** Updated language support details in `core.py` and `README.md` to reflect `pysbd` and `sentence-splitter` capabilities.
- **CLI Refactoring:** Moved CLI logic from `core.py` to a separate `cli.py` file.
- **Documentation:** Added comprehensive docstrings and comments to `core.py` for improved clarity and maintainability.
- **README Updates:** Updated version numbers, badges, and language support sections in `README.md`.
- **Performance Optimization:** Replaced `mpire.WorkerPool` with `concurrent.futures.ThreadPoolExecutor` for parallel batch processing to reduce overhead on small to medium-sized batches.
- **Chunk Token Counter:** Added support in `chunk` for overriding the token counter set during initialization if a different one is provided.

### Documentation

- **README Update:** Embedded Mermaid flow diagram for internal workflow visualization.
- **README Update:** Added a logo display with responsive HTML, custom sizing (300px), and accompanying "chunklet" text.


## [1.0.4.post4] - 2025-07-25

### Added

- **CLI Mode:** Implemented a command-line interface using `argparse` for direct execution of chunking operations.
- **CLI Entry Point:** Added `[project.scripts]` entry point in `pyproject.toml` to enable running `chunklet` directly from the command line.

### Changed

- **Default Chunking Mode:** Changed the default `mode` in `chunk` and `batch_chunk` methods from `hybrid` to `sentence`.
- **Author Information:** Updated author name to "Speedyk_005" in `src/chunklet/__init__.py`, `README.md`, and `pyproject.toml`.
- **GitHub URLs:** Updated `Homepage`, `Repository`, and `Issues` URLs in `pyproject.toml` to reflect the new GitHub username.
- **README Updates:** Marked CLI feature as checked and rephrased "Named chunking presets" in `README.md`.

---

## [1.0.4] - 2025-07-25

### Added

- **License File:** Added the MIT License file (`LICENSE`) to the project.
- **Batch Chunking Test:** Introduced `test_batch_chunk_method` to verify the functionality of the `batch_chunk` method, including its parallel processing.

### Changed

- **Clause-Level Overlap (Milestone):** Clauses are determined via punctuation triggers like (`; , ) ] ’ ” —`). 
  Overlap is now performed at the **clause level**, not just on sentences. 
  This ensures smoother, more context-rich chunk transitions
- **Chunking logic Refactor:** Lots of methods have be modularized, Refactored, optimised.
- **Test Assertions:** Adjusted tests to match the improved clause overlap logic.
- **Refined documentatios:** Documentations and comments are refined.

### Fixed

- **Docstring Redundancy:** Removed redundant module-level docstring from `src/chunklet/core.py`.
- **Token Counter Handling:** Fixed incorrect propagation of `token_counter` in `batch_chunk`, ensuring consistent behavior during multiprocessing.
- **Detected flaws:** Lots of bugs were fixed 

---

## [1.0.2] - 2025-07-23

### Added

- **New Caching Test:** Introduced `test_chunklet_cache` to validate chunk caching behavior.
- **Readme Improvements:** Better formatting, emoji-safe layout, usage examples, and tokenizer documentation.
- **Pytest Config:** Added `[tool.pytest.ini_options]` in `pyproject.toml` to support test discovery without modifying `PYTHONPATH`.
- **Warning Suppression:** Filters added to hide known deprecation warnings.
- **Setup Tools Integration:** Full `pyproject.toml` with editable install, metadata, and dev dependencies.

### Changed

- **Token Counter Injection:** `Chunklet` now takes the `token_counter` function in the constructor, simplifying reuse.
- **Fallback Splitter:** Improved formatting for low-resource language cases.

### Removed

- **PEP 639 Compliance:** Removed deprecated `License :: OSI Approved` classifier.

### Fixed

- **UTF-8 DecodeError Fix:** Resolved encoding errors during editable install.
- **Token Counter Propagation:** Corrected inconsistent usage across batch and core chunk methods.

---

## [1.0.1] - 2025-07-23

### Added

- **Unit Tests:** Full coverage for sentence, token, and hybrid modes.
- **Multilingual Testing:** English, French, Spanish, and German tests with auto-detection.

### Changed

- **Core Overlap Logic:** Improved overlap accuracy with better chunk boundary handling.
- **Test Structure:** Sample inputs grouped and reused across test cases.

### Fixed

- **Sentence Boundary Handling:** Better handling of acronyms and edge punctuation.
- **Overlap Verification:** Subsequence checks instead of naive boundary comparison.

---

## [1.0.0] - 2025-07-22

### Added

- **Initial Project Setup:** Core files, structure, and package skeleton under `src/`.
- **Multilingual Splitters:** Integrated `sentsplit` and `sentence_splitter` with auto language detection.
- **Chunking Modes:** Sentence, token, and hybrid support.
- **Configurable Overlap:** Added `overlap_fraction` for contextual continuity.
- **Parallel Processing:** Integrated `mpire` for fast batch chunking.
- **Caching:** Added LRU caching for chunk operations.
- **Regex Split Fallback:** Regex-based splitter for unsupported languages.
- **Verbose Warnings:** Logged low-confidence language detection.
