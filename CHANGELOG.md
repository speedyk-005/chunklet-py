# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),  
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.4.post4] - 2025-07-25

### Added

- **CLI Mode:** Implemented a command-line interface using `argparse` for direct execution of chunking operations.
- **CLI Entry Point:** Added `[project.scripts]` entry point in `pyproject.toml` to enable running `chunklet` directly from the command line.

### Changed

- **Default Chunking Mode:** Changed the default `mode` in `chunk` and `batch_chunk` methods from `hybrid` to `sentence`.
- **Author Information:** Updated author name to "Speedyk_005" in `src/chunklet/__init__.py`, `README.md`, and `pyproject.toml`.
- **GitHub URLs:** Updated `Homepage`, `Repository`, and `Issues` URLs in `pyproject.toml` to reflect the new GitHub username.
- **README Updates:** Marked CLI feature as checked and rephrased "Named chunking presets" in `README.md`.

## [1.0.4] - 2025-07-25

### Added

- **License File:** Added the MIT License file (`LICENSE`) to the project.
- **Batch Chunking Test:** Introduced `test_batch_chunk_method` to verify the functionality of the `batch_chunk` method, including its parallel processing.

### Changed

- **Clause-Level Overlap (Milestone):**    
  Clauses are determined via punctuation triggers like (`; , ) ] ’ ” —`). 
  Overlap is now performed at the **clause level**, not just on sentences.   
  This ensures smoother, more context-rich chunk transitions
- **Chunking logic Refactor:** Lots of methods have be modularized, Refactored, optimised.
- **Test Assertions:** Adjusted tests to match the improved clause overlap logic.
- Documentations and comments are refined.
### Fixed

- **Docstring Redundancy:** Removed redundant module-level docstring from `src/chunklet/core.py`.
- **Token Counter Handling:** Fixed incorrect propagation of `token_counter` in `batch_chunk`, ensuring consistent behavior during multiprocessing.
- Lots of bugs were fixed 

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
