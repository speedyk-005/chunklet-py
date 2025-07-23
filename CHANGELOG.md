# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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