# Converters vs. Processors

This document explains the difference between `converters` and `processors` in the `DocumentChunker` and why both are used.

## High-Level Summary

`converters` and `processors` both play a role in extracting text from documents, but they are designed for different kinds of files:

*   **`converters`** are for simple, text-centric files.
*   **`processors`** are for more complex, structured documents.

---

## `converters`

`converters` are designed for file formats that can be effectively treated as a single, continuous block of text.

*   **Purpose:** Their main job is to convert the *entire* file content into a clean, plain text format (specifically Markdown).
*   **File Types:** `.html`, `.rst` (reStructuredText), `.tex` (LaTeX).
*   **How they work:** They are simple functions that take a file path, read the whole file, and return a single string.
*   **Metadata:** They do not handle metadata extraction. The only metadata associated with them is the file path, which is added later in the chunking process.

> **Analogy:** Think of `converters` as a "quick text dump." They just get all the text out in one go.

---

## `processors`

`processors` are designed for complex, structured file formats that have a richer internal structure, such as distinct pages, sections, and embedded metadata.

*   **Purpose:** To provide a more sophisticated interface for handling complex documents.
*   **File Types:** `.pdf`, `.docx`, `.epub`.
*   **How they work:** They are classes that offer more control over the extraction process:
    *   **Text Extraction:** They extract text in pieces (e.g., page by page for a PDF). This is more memory-efficient for large, multi-page documents. The text is returned as a `Generator`.
    *   **Metadata Extraction:** They have a dedicated method (`extract_metadata`) to pull detailed, structured metadata from the file itself (e.g., author, title, creation date).
    *   **Initialization:** They are initialized with the file path (`__init__(self, file_path)`), allowing them to open the file and prepare for extraction.

> **Analogy:** Think of `processors` as a "detailed file analysis." They understand the file's structure, giving you both the content in manageable pieces and the important metadata about it.

---

## Comparison Table

| Feature | `converters` | `processors` |
| :--- | :--- | :--- |
| **Use Case** | Simple, text-based files | Complex, structured documents |
| **Output** | A single `string` | Text as a `Generator` + a metadata `dict` |
| **Metadata**| Basic (file path only) | Rich, format-specific metadata |

By using both, the system can apply the right tool for the job: a simple, fast approach for simple files and a more powerful, structured approach for complex ones.
