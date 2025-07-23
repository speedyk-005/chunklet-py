# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2025-07-23

### Added

- **New Caching Test:** Introduced `test_chunklet_cache` to validate chunk caching behavior and confirm performance consistency when reusing the same input.
- **Readme Improvements:** Updated `README.md` with emoji-safe formatting, clearer usage sections, improved GPT-2 tokenizer example, and batch chunking illustration.
- **Pytest Configuration in `pyproject.toml`:** Integrated `[tool.pytest.ini_options]` to avoid requiring `PYTHONPATH=./src` manually during test runs.
- **Warning Suppression:** Applied filters to hide known deprecation warnings from `pkg_resources`, `coverage.tracer`, and others for cleaner test outputs.
- **Setup Integration:** Provided full `pyproject.toml` configuration with editable install support, setuptools metadata, and dev dependencies under `[project.optional-dependencies.dev]`.

### Changed

- **Core Token Counter Handling:** The `Chunklet` class now accepts the token counter directly during initialization (`__init__`), improving clarity and simplifying repeated use across methods.
- **Fallback Splitter Formatting:** Adjusted `_fallback_splitter()` logic in the core to preserve whitespace formatting more faithfully across edge cases.
- **Test Adjustments:** Reworked existing tests (`test_chunklet.py`) to align with internal refactors, improve readability, and ensure token counter alignment with new `__init__` signature.
- **Removed deprecated** `License :: OSI Approved :: MIT License` **classifier in compliance with PEP 639 license expression standards.**

### Fixed

- **Format-Preserving Chunking:** Refined fallback sentence splitting to better preserve paragraph and newline structure in low-resource language cases.
- **Token Counter Pass-Through:** Ensured consistent propagation of the user-defined `token_counter` throughout chunking and batch processing logic.
- **Critical UTF-8 DecodeError fix:** Resolved `UnicodeDecodeError` during editable installs caused by invalid encoding in metadata files, enabling clean installation.
- Editable install now runs cleanly without subprocess errors or warnings.

## [1.0.1] - 2025-07-23

### Added

-   **Unit Test Suite:** Introduced robust unit tests for `sentence`, `token`, and `hybrid` chunking modes with `pytest`, covering chunk count, overlap accuracy, acronym handling, and multilingual segmentation.
-   **Language-Aware Batch Testing:** Added tests verifying behavior across English, French, Spanish, and German inputs using both auto-detection and specified language parameters.

### Fixed

-   **Sentence Overlap Verification:** Adjusted test overlap assertions to compare meaningful subsequences rather than relying on edge alignment alone.
-   **Minor Sentence Boundary Handling:** Improved handling for multilingual and acronym-heavy inputs by fine-tuning `sentence_splitter` fallback routing and whitespace normalization.

### Changed

-   **Chunklet Core Logic:** Refined internal overlap calculations and sentence accumulation logic for better precision in edge cases during chunk construction.
-   **Test Structure:** Sample inputs are now clearly grouped and reused across test cases for readability and DRY principles.

## [1.0.0] - 2025-07-22

### Added

-   **Initial Project Setup:** Established core project structure with `src/` directory and `chunklet.py`.
-   **Multilingual Sentence Splitter:** Integrated `sentsplit` (CRF-based) and `sentence_splitter` (rule-based) with language detection.
-   **Flexible Chunking Modes:** Implemented `sentence`, `token`, and `hybrid` chunking strategies.
-   **Configurable Overlap:** Added `overlap_fraction` for contextual chunking.
-   **Parallel Processing:** Integrated `mpire` for efficient batch chunking.
-   **LRU Caching:** Included caching for `_chunk` method for performance.
-   **Regex Fallback Splitter:** Provided a basic regex-based sentence splitter as a fallback for unsupported languages.
-   **Verbose Mode & Warnings:** Added options for verbose output and warnings for low language detection confidence.