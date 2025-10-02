# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),  
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0 beta] - 2025-09-12

### Added

- **Expanded Language Support:** Integrated `sentsplit`, `sentencex`, and `indic-nlp-library` for more accurate and comprehensive sentence splitting across a wider range of languages.
This officially boosts language support from 36+ to 40+.
- **Error Handling**: Added an `on_errors` parameter to `batch_chunk` to allow for more flexible error handling (raise, ignore, or break).
- **Faster Language Detection**: Optimized language detection by using only the first 500 characters of the input text. This significantly improves performance, especially for large documents, without compromising accuracy for language identification.
- **Code Chunker Introduction:** Introduced `CodeChunker` for syntax-aware chunking of source code, with support for multiple programming languages by leveraging `src/libs/code_structure_extractor` to dispatch code into structural elements.
- **CLI Multiple Input Files:** Added an `--input-files` argument to allow processing of multiple specific files.
- **CLI Metadata Flag:** Added a `-m, --metadata` flag to the CLI to display chunk metadata in the output.
- **Document Chunker:** Introduced `DocumentChunker` to handle various file formats like `.pdf`, `.docx`, `.txt`, `.md`, `.rst`, `.rtf`.
- **Show Progress Parameter:** Added `show_progress` parameter to `batch_chunk` in `PlainTextChunker` to allow users to control the display of the progress bar.
- **Custom Processors:** Introduced support for custom document processors, allowing users to define their own logic for extracting text from various file types.
- **Custom Exception Types:** Introduced `TextProcessingError` for errors during text processing, `FileProcessingError`, during file processing and `UnsupportedFileTypeError` for unsupported file formats.
- **Cache Management**: Added a static method `clear_cache` to `PlainTextChunker` to allow programmatic clearing of the shared in-memory cache.

### Changed

- **Improved Universal Splitter:** Replaced the existing universal sentence splitter with a more robust, multi-stage version. The new splitter offers more accurate handling of abbreviations, numbered lists, and complex punctuation, and has a larger punctuation coverage, improving fallback support for unsupported languages.
- **Clause Delimiters**: Added ellipsis to the list of clause delimiters for more accurate chunking.
- **Logging**: Replaced `loguru` with the standard `logging` module and `RichHandler` for a cleaner and more beautiful logging experience that integrates seamlessly with progress bars.
- **Batch Chunking Flexibility:** Modified `PlainTextChunker.batch_chunk` to accept any `Iterable` of strings for the `texts` parameter, instead of being restricted to `list`.
- **Memory Optimization:** Refactored all batch methods in the lib to fully utilize generators, yielding chunks one at a time to reduce memory footprint, especially for large documents. That also means you dont have to wait for the chunks fully be processed before start using them.
- **Memory Friendly caching:** Replaced `functools.lrucache` with `cachetools.cache` to avoid instance references in cache keys to prevent unnecessary memory retention.
- **Project Structure:** Moved several utility modules to a new `src/chunklet/libs` directory.
- **Linting:** Integrated `flake8` for code linting and updated `CONTRIBUTING.md` with instructions for running it.
- **Code Quality:** Fixed various `pyflakes` linting issues across the `src/` and `tests/` directories, improving code cleanliness.
- **Error rebranding:** Renamed `TokenNotProvidedError` to `MissingTokenCounterError` for clearer semantics and updated all relevant usages.
- **Error Handling:**
    - Modified `_count_tokens` to return `TextProcessingError` instead of `ChunkletError`.
    - Catched errors raised by the usage of `custom_splitters`'s callback and reraised as `TextProcessingError` instead.
    - Improves the exception hierarchy by removing `MissingTokenCounterError` as subclass of `InvalidInputError`.
- **Project Restructuring:**
    - Renamed `src/chunklet/core.py` to `src/chunklet/plain_text_chunker.py`.
    - Renamed `Chunklet` class to `PlainTextChunker`.
- **Improved Error Messages:** Improved error messages across the library to be more user-friendly and provide hints for fixing the issues.  
- **Friendlier Initialization:** Updated `PlainTextChunker` to accept a a list of dict instead of a list of models for more beginner friendly initialization.
- **Safer Tokenizer Command processing:** Changed `shell=True` to `shell=False` for the subprocess.run call in create_external_tokenizer for enhanced security and predictability. The shlex module is now implicitly used for command parsing when shell=False.
- **Improved chunking format:** Added a newline between sentences for structured chunking format output. This helps preserving original format better.
- **Grouping improvements:**
    - Improved logic for handling sentences that exceed max_tokens or max_sentences. The `_find_clauses_that_fit` method's output (fitted, unfitted) is now more accurately integrated, ensuring that sentences are correctly split and assigned to chunks.
    - Modified `_find_clauses_that_fit` to return a list of str instead of a tuple of list of str for easier control. That Ensures that unfitted sentences are properly joined and accounted for when starting a new chunk after an overlap.
    - Use incremental token recalculation for better performance.
    - Artifacts handling: Ignore the last chars after the first 150 ones in the loop around sentences. Reason: if the original text to chunk has parts not well written. (e.g. long text stream without punctuations, embeded images urls, ...)
- **Absolute Imports:** Converted all relative imports to absolute imports within the `chunklet` package for better clarity and to avoid potential import issues.
- **Project Layout:** Restructured project by moving the logo to the root and adding a `samples/` directory to store the sample files.
- **CLI Aliases:** Added `-f` as an alias for `--file` and `-d` as an alias for `--input-dir`.
- **Default Limits:** Changed the default `max_tokens` from 512 to 256 and `max_sentences` from 100 to 12.
- **Model renamed:** Renamed `ChunkingConfig` to `TextChunkingConfig`.
- **Continuation marker:** Exposed continuation marker so users can define thier own or set it to an empty str to disabled it.
- **Custom Splitter Validation**: Refactored custom splitter callback validation into a `split` method within `CustomSplitterConfig`, providing a safer wrapper for callback execution and clearer error messages.

### Removed

- **Python 3.8 Support:** Dropped official support for Python 3.8. The minimum required Python version is now 3.9.
- **CLI Argument:** Removed the `--no-cache` command-line argument.
- **CLI Argument:** Removed the deprecated `--batch` argument.
- **Sentence-splitter removed:** Removed `sentence-splitter` and replaced by other libs. 

---

## [1.4.0] - 2025-08-27

### Added

- **CLI Version Flag:** Implemented a `--version` flag to display the package version.
- **Version Attribute:** Added `__version__` to the `__init__.py` file.
- **CLI Directory Input:** Batch processing now supports reading input from a directory (`--input-dir`), automatically discovering `.txt` and `.md` files.
- **CLI Flexible Output:** Chunks can now be written to a specified output directory (`--output-dir`), with each chunk saved as a separate file (e.g., `filename_chunk_1.txt`).
- **CLI Input File Alias:** Added `--input-file` as an alias for `--file` for consistency with `--input-dir`.

### Changed

- **Project rebranding:** Renamed project from `chunklet` to `chunklet-py` to improve its online discovery and distinguish it from other unrelated projects that use the similar names.
- **CLI Output Formatting:** Added a newline between each chunk in console and single-file output for improved readability.
- **CLI Error Handling:** Improved the error message when no input arguments are provided, offering clearer guidance and examples.
- **CLI Deprecation Warning:** Introduced a deprecation warning when using `--batch` with `--file` (or `--input-file`), encouraging the use of `--input-dir` for batch processing.
- **Lazy Import of `mpire`:** Modified `core.py` to lazily import the `mpire` library, improving startup time by only importing it when batch processing is utilized. 

---

## [1.3.2] - 2025-08-25

### Changed 

- **Validation Error:** Improved the readability of validation error messages.
- 
### Fixed

- **Empty Chunk:** Resolved an issue where an empty chunk could be generated if the first sentence exceeded the `max_tokens` limit.
- **Hybrid Chunking:** Fixed a bug in hybrid chunking mode where chunking limits were not correctly applied, leading to chunks being larger than intended.
- **Custom Splitters:** Fixed an issue with custom splitters where extra spaces were added between sentences.
- **CLI SyntaxError:** Fixed a `SyntaxError` in the CLI due to an unterminated string literal.
- **Infinite Loop:** Fixed infinite loop bug caused by max sentences validation using 0 instead of 1 as minimum.

---

## [1.3.1] - 2025-08-23

### Added

- **PDF Chunking:** Added an example for PDF chunking.
- **PyPDF Import:** Added a `try...except` block for `pypdf` import in the example.
- **README Update:** Updated the `README.md` to include the PDF chunking example and added it to the ToC.

### Fixed

- **Python 3.9 Compatibility:** Refactored 'match' statement to 'if/elif/else' for Python 3.9 compatibility.
- **Core Warning:** Fixed a warning in `core.py` where `language` was used instead of `lang`.

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
