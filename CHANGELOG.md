# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),  
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.2.0] - 2026-02-14

### Changed
- **CodeChunker Renames**:
  - Renamed `MULTI_LINE_COMMENT` to `MULTI_LINE_COMM` for consistency
  - Renamed `CLOSURE` to `CLOSER` as it's a misconception
- **PlainTextChunker Improvements**:
  - Fixed `_find_span` to remove continuation markers before matching
  - Added `.strip()` to exact match for whitespace edge cases
  - Added budget cap at 60 to prevent extreme regex backtracking
- **Dependencies**: Added upper version bounds to all dependencies for better stability and reproducibility

### Added
- **Global Registry Instances**: Added global `custom_splitter_registry` and `custom_processor_registry` instances for easier customization
- **Tokenizer CLI Enhancements**:
  - Added `--tokenizer-timeout` / `-t` option (default: 10s) for both `chunk` and `visualize` commands
  - Improved tokenizer error messages to distinguish between invalid output, timeout, and execution errors
  - Added `-h` as a shortcut for `--host` in the `visualize` command
- **Visualizer UI Redesign**:
  - Redesigned layout from 2-column to 3-row structure
  - Added scroll hint that shows only when modal has overflow
  - Fixed placeholder text centering in visualization box
  - Added chunk span pointer-events for better click handling
  - Added custom scrollbar styling
- **Added fullscreen mode** for visualization area with overlay toggle button. Uses browser native fullscreen API with modal dialogs properly rendered on top via Top Layer.
- **Visualizer Layout**:
  - Reduced top row height to 300px max for upload and instructions sections
  - Removed square constraint from upload area for better border adaptation
- **Improved Visualizer Error Handling**: Error messages now distinguish between server connection issues and file format errors, making troubleshooting easier for users.
- **Expanded CodeChunker Patterns**:
  - Added single-line comment patterns for **Forth** (`\|`).
  - Added support for **PHP 8 attributes** (`#[...]`) and **VB.NET metadata** (`<...>`).
  - Added `export` to namespace declarations and `component` to function modifiers for **ColdFusion** compatibility.
  - Added support for **Pascal-style** `BEGIN` and `END` (case-insensitive) as block delimiters.
  - Added open curly bracket in the function pattern to support more languages.
- **Multi-line String Protection**: Added MULTI_LINE_STRING_ASSIGN to prevent the extractor from splitting snippets inside large string blocks or triple-quotes.
- **Direct Import Support**: Enhanced lazy loading to support direct imports while maintaining performance optimizations

### Changed
- **CodeChunker Pattern Logic**:
  - Refactored `METADATA` regex to use recursive sub-routines, enabling proper handling of nested parentheses.
  - Reclassified **Nim** (`##`) and **Erlang** (`%%`) documentation comments as Style 2 line-prefixed comments for better chunk cohesion.
- **Code Extractor Architecture**:
  - Centralized structural state management within _handle_block_start, moving block_indent_level updates away from annotation handlers to follow SRP.
  - Refined the indentation "anchor" logic and guard clauses to correctly separate sibling methods while maintaining parent-child relations for nested closures.
- **Development Tooling**:
  - Replaced Flake8 + Black with **Ruff** for improved performance and unified tooling
  - Ruff provides 10-100x faster feedback cycles while maintaining all existing code quality standards

### Fixed
- **CodeChunker Annotation Remnants**:
  - Fixed remnants of annotation tags in output by using separate patterns for full-line vs inline comments
  - Only full-line comments are now annotated, inline comments stay with their code line
- **Visualizer CSS and Docstring Positioning**:
  - Fixed docstring positioning issue in visualizer web interface. The issue was caused by forcing `.txt` extension on temporary files, preventing proper Python parsing. Fix preserves original file extensions for code mode.
  - Optimized chunk span interactions by replacing layout-affecting borders with box-shadows for smooth, non-jumpy hover effects, custom scrollbar styling, and improved overlap visibility with consistent transitions across all states.
  - Fixed download and reveal buttons to remain enabled after processing chunks, rather than being disabled when no file is uploaded.

---

## [2.1.1] - 2025-12-21

### Fixed
- **Visualizer Static Files:** Fixed critical issue where the Chunk Visualizer static files (CSS, JS, HTML) were not being included in the PyPI package distribution, causing `RuntimeError: Directory does not exist` when running `chunklet visualize`. Added proper package data configuration to include `visualizer/static/*` files in the distribution.

---

## [2.1.0] - 2025-12-19

### Added
- **ODF Support:** Added full support for OpenDocument Text (.odt) files with a new `ODTProcessor` class using the `odfpy` library.
- **Table Processing:** Added support for CSV and Excel (.xlsx) files with automatic Markdown table conversion using the `tabulate2` library.
- **Character-Based Chunking:** Implemented 4k character chunking for DOCX and ODT processors to simulate page-sized segments and enhance parallel execution capabilities.
- **Automatic Encoding Detection:** Integrated charset-normalizer for intelligent text encoding detection in code and document processing, improving reliability by correctly reading files regardless of their encoding instead of assuming UTF-8.
- **Chunk Visualizer:** Added a comprehensive web-based visualizer interface for interactive text and code chunking with real-time visualization, parameter controls, and file upload capabilities.
- **CLI Visualize Command:** Added `chunklet visualize` command with options for host, port, tokenizer integration, and headless operation.

### Changed
- **Default `include_comments`:** Changed the default value of the `include_comments` parameter to `True` in the `CodeChunker.chunk()` method to align with most developer expectations for comprehensive code processing.
- **Base Chunker Inheritance:** Introduced a new `BaseChunker` abstract base class in `base_chunker.py` to standardize the interface for all chunkers.
- **PDF Processor Modularity:** Refactored `PDFProcessor.extract_text()` method for better modularity with improved text cleaning utilities.
- **Refactoring for Readability and Modularity:** Split functions into helpers across PlainTextChunker, CodeChunker, and CLI to reduce cognitive load. Improved variable names, added docstrings, and simplified conditionals for better codebase readability.
- **Documentation Updates:** Modified `cli.md` and `code_chunker.md` to clarify destination behavior, JSON output, and add new scenarios for better user guidance.
- **CLI Conditional Imports:** Improved CLI error handling with conditional imports for optional dependencies (document chunkers, code chunkers, visualizer) providing clear installation instructions when features are unavailable.

### Fixed
- **Code Chunker Issues:**
  - Fixed a classic Python closure bug in the code annotation loop. The original `pattern.sub(lambda match: self._annotate_block(tag, match), code)` caused the lambda to reference the final value of `tag` after the loop completed. Resolved by using the default argument trick to capture the current `tag` value at definition time.
  - Removed redundant string slicing logic where line de-annotation was called twice, creating ambiguity and potential "ghost slicing" issues.
  - Fixed bug in `_split_oversized()` where lines exceeding limits were skipped during chunk creation. Overflow lines were flushed but never added to any chunk, causing missing content in output.
  - Fixed issue where decorators (e.g., `@property`) were incorrectly separated from their associated functions into different chunks. Added proper flush conditions to ensure decorators group with their functions.
  - Fixed critical bug where path detection logic incorrectly called `is_path_like()` on Path objects instead of strings, causing validation errors when PosixPath objects were passed. Corrected the logic to properly check `isinstance(source, Path)` first, then only call `is_path_like()` on string inputs.
- **CLI Destination Logic:** Fixed out-of-design destination handling by removing input count restrictions, ensuring consistent JSON file output and directory handling.
- **CLI Path Validation Bug (#6):** Resolved TypeError where len(destination) was called on a PosixPath object. Thanks to [@arnoldfranz](https://github.com/arnoldfranz) for reporting this issue.
- **Document Chunker Batch Error Handling Bugs:** Fixed multiple bugs in `DocumentChunker._gather_all_data()` that were hidden due to missing test coverage. Issues included incorrect exception raising (`raise error` instead of `raise`), malformed logging format strings, KeyError when accessing path_section_counts for failed files, and missing early return when no files are successfully processed. These bugs were discovered and fixed while adding comprehensive test coverage for batch processing error handling.

---

## [2.0.3] - 2025-11-21

### Fixed

- **Span Detection:** Fixed hardcoded distance limit that caused spans to always return (-1, -1) for longer text portions.
- **Accuracy:** Improved span detection with adaptive budget calculation and continuation marker handling.

### Changed

- **Find Span Logic:** Replaced fuzzysearch-based implementation with enhanced regex-based approach for better performance and accuracy.

### Removed

- **Dependencies:** Removed fuzzysearch dependency.

---

## [2.0.2] - 2025-11-20

### Fixed

- **Internal:** Removed debug print statements from the `_filter_sentences` method in `SentenceSplitter`.

---

## [2.0.1] - 2025-11-20

### Fixed

- **CLI Bug:** Fixed a critical unpacking bug in the `split` command. The line intended to extract sentences and confidence from `splitter.split` (e.g., `sentences, confidence = splitter.split(...)`) caused either a `ValueError` (if `splitter.split` returned a number of sentences other than exactly two) or silent, incorrect unpacking (if exactly two sentences were returned, assigning the first sentence string to `sentences` and the second to `confidence`, leading to character-level iteration). The fix now correctly separates language detection and confidence retrieval from sentence splitting, resolving both issues and ensuring accurate output.

---

## [2.0.0] - 2025-11-17

### Added

- **Code Chunker Introduction:** Introduced `CodeChunker`, a rule-based language agnostic chunker for syntax-aware chunking of source code.
- **Expanded Language Support:** Integrated `sentsplit`, `sentencex`, and `indic-nlp-library` for more accurate and comprehensive sentence splitting across a wider range of languages.
This officially boosts language support from 36+ to 50+.
- **Error Handling in batch methods**: Added an `on_errors` parameter to `batch_chunk` methods to allow for more flexible error handling (raise, skip, or break).
- **Document Chunker:** Introduced `DocumentChunker` to handle various file formats like `.pdf`, `.docx`, `.txt`, `.md`, `.rst`, `.rtf`, `.tex`, `.html/hml`, `.epub`.
- **Show Progress Parameter:** Added `show_progress` parameter to `batch_chunk` in `PlainTextChunker` to allow users to control the display of the progress bar.
- **Custom Processors:** Introduced support for custom document processors, allowing users to define their own logic for extracting text from various file types.
- **New Constraint Flags:** Introduced `max_section_breaks` for PlainTextChunker and DocumentChunker, and `max_lines` for CodeChunker, providing more granular control over chunking.
- **New Custom Exception Types:** Introduced more specific error types like `FileProcessingError`, `UnsupportedFileTypeError`, `TokenLimitError` and `CallbackError`.
  
### Changed

- **Project Restructuring:**
    - Renamed `src/chunklet/core.py` to `src/chunklet/plain_text_chunker.py`.
    - Renamed `Chunklet` class to `PlainTextChunker`.
- **CLI Refactoring:**
    - Simplified all input flags (--file, --dir, etc.) into a single --source (-s) flag, which accepts one or more paths (files or directories).
    - Combined the verbose --output-file and --output-dir into a single --destination (-d) flag, which automatically adapts to single-file output or multi-file directory writing.
    - Updated constraint flags to match the new constraint style (no `mode`, no default values for `max_tokens` and `max_sentences`).
- **Type Validation:** Replaced Pydantic BaseModel with `pydantic.validate_call` for lightweight and easier validation, centralizing runtime type checking.       
- **Sentence Splitter Refactoring:**
    - Refactored the `SentenceSplitter` to be more modular and extensible. The management of custom splitters has been moved to a new `registry` module, which provides a centralized way to register and use custom splitter functions.
    - Introduced a new way of registering custom splitters using the `register_splitter` function and the `@registered_splitter` decorator, replacing the old dictionary-based approach. This new API is more explicit, provides better validation, and is easier to use.
- **Improved FallbackSplitter:** Replaced the existing universal sentence splitter with a more robust, multi-stage version. The new splitter offers more accurate handling of abbreviations, numbered lists, and complex punctuation, and has a larger punctuation coverage, improving fallback support for unsupported languages.
- **SentenceSplitter Extraction:** The core sentence splitting logic, previously embedded within `PlainTextChunker`, has been extracted and consolidated into a dedicated `SentenceSplitter` module. This significantly improves modularity, reusability, and maintainability across the library.
- **Clause Delimiters**: Added ellipsis to the list of clause delimiters for more accurate chunking.
- **Batch Chunking Flexibility:** Modified `PlainTextChunker.batch_chunk` to accept any `Iterable` of strings for the `texts` parameter, instead of being restricted to `list`.
- **Memory Optimization:** Refactored all batch methods in the lib to fully utilize generators, yielding chunks one at a time to reduce memory footprint, especially for large documents. That also means you dont have to wait for the chunks fully be processed before start using them.
- **Code Quality:**
    - Fixed various `pyflakes` linting issues across the `src/` and `tests/` directories, improving code cleanliness.
    - Integrated `flake8` for code linting and updated `CONTRIBUTING.md` with instructions for running it.
- **Error rebranding:** Renamed `TokenNotProvidedError` to `MissingTokenCounterError` for clearer semantics and updated all relevant usages.
- **Error Handling:**
    - Modified `count_tokens` to return `CallbackError` instead of `ChunkletError`.
    - Re-parented `MissingTokenCounterError` under `InvalidInputError`.
- **Improved Error Messages:** Improved error messages across the library to be more user-friendly and provide hints for fixing the issues.  
- **Safer Tokenizer Command processing:** Changed `shell=True` to `shell=False` for the subprocess.run call in create_external_tokenizer for enhanced security and predictability. The shlex module is now implicitly used for command parsing when shell=False.
- **Improved chunking format:** Added a newline between sentences for structured chunking format output. This helps preserving original format better.
- **Grouping improvements:**
    - Improved logic for handling sentences that exceed max_tokens or max_sentences. The `_find_clauses_that_fit` method's output (fitted, unfitted) is now more accurately integrated, ensuring that sentences are correctly split and assigned to chunks.
    - Modified `_find_clauses_that_fit` to return a list of str instead of tuple[list[str]] (tuple of list of str) for easier control. That Ensures that unfitted sentences are properly joined and accounted for when starting a new chunk after an overlap.
    - Use incremental token recalculation for better performance.
    - Artifacts handling: Improved logic to gracefully handle and segment malformed or extreme text artifacts (e.g., massive URLs, base64 blocks, minified JSON) by applying a Greedy Token Cutoff. This ensures the chunker does not fail or produce overly large, unusable chunks when encountering long, unpunctuated strings.
- **Absolute Imports:** Converted all relative imports to absolute imports within the `chunklet` package for better clarity and to avoid potential import issues.
- **Continuation marker:** Improved the continuation marker logic and exposed it's value so users can define thier own or set it to an empty str to disabled it.

### Removed

- **Chunking Mode:** Removed the `mode` argument from the CLI and `PlainTextChunker`, as its functionality is now implicitly handled by other constraint flags (`max_tokens`, `max_sentences`, `max_section_breaks`).
- **Caching:** Removed the in-memory caching functionality to focus on raw performance optimization. the only part that still have caching is the utils `count_tokens`
- **Python 3.8 and 3.9 Support:** Dropped official support for Python 3.8 and 3.9. The minimum required Python version is now 3.10.
- **CLI Argument:** Removed the `--no-cache` command-line argument.
- **CLI Argument:** Removed the deprecated `--batch` argument.
- **Removed `preview_sentences` method:** The `preview_sentences` method was removed from `PlainTextChunker` as the `SentenceSplitter` is now exposed as a separate, dedicated utility.

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
- **Progress Bar for Batch Processing**: Visual feedback for batch processing with a mpire progress bar.
- **Faster batching**: On `n_jobs=1`, mpire is not used to prevent overheads. on `n_jobs>=2` batch are process with group of 2 per process. 

### Changed

- **Fault-Tolerant Batch Processing**: In batch mode, if a task fails, `chunklet` will now stop processing and return the results of the tasks that completed successfully, preventing wasted work.
- **_get_overlap_clauses Logic:** Simplified the logic for calculating overlap clauses by filtering empty clauses and improving the capitalization check.
- **Improved fallback splitter:** Used `p{Lu}`, `p{Ll}` in `regex_splitter.py` to identify and handle abbreviations and acronyms more accurately across different languages.                
- **Token Counter Error Handling:** Enhanced robustness by introducing a helper method to safely count tokens and handle potential errors from user-provided token counters. On error, operation is aborted.
- **LRU Cache Optimization:** - Made caching mechanism to be internal and subtle and increased `lru_cache` maxsize from 25 to 256 for improved caching performance.
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
