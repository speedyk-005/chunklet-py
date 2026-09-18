Welcome to the programmatic interface! This is where you integrate Chunklet-py's chunking capabilities directly into your Python apps.

<div class="grid cards" markdown>

-   :material-comment-text:{ .lg .middle } __Sentence Splitter__

    ---

    Splits text into sentences across 60+ languages with automatic language detection and complex structure handling.

    Great for preparing clean text data for NLP tasks, LLMs, or any application that needs accurate sentence boundaries.

    [:octicons-arrow-right-24: Learn More](sentence_splitter.md)
    
-   :material-file-document-outline:{ .lg .middle } __Document Chunker__

    ---

    Transforms plain text and diverse document formats (`.pdf`, `.docx`, `.epub`, `.eml`, `.pptx`, `.txt`, `.tex`, `.html`, `.hml`, `.md`, `.rst`, `.rtf`, `.odt`, `.csv`, and `.xlsx`) into sized chunks with composable constraints and overlap for LLM and embedding pipelines.

    Great for RAG systems, document analysis, or any workflow that needs chunk size control.

    [:octicons-arrow-right-24: Learn More](document_chunker.md)

-   :material-code-braces:{ .lg .middle } __Code Chunker__

    ---

    Chunks source code while preserving logical structure and maintaining code semantics across functions, classes, and modules.

    Language-agnostic and lightweight, great for code understanding, generation, analysis, documentation, and AI model training.

    [:octicons-arrow-right-24: Learn More](code_chunker.md)

-   :material-robot:{ .lg .middle } __Self-Tuning Chunker__

    ---

    Self-tuning chunks for mixed text and code corpora. Classifies each source as document or code, learns per-profile structural statistics via a Kaufman Adaptive Moving Average (KAMA), and sizes chunk boundaries to match your content without manual constraint tuning.

    Perfect for heterogeneous corpora, evolving codebases, and anyone tired of hand-picking `max_sentences` / `max_lines` limits.

    [:octicons-arrow-right-24: Learn More](self_tuning_chunker.md)

-   :material-monitor-shimmer:{ .lg .middle } __Text Chunk Visualizer__

    ---

    Interactive web interface for real-time chunk visualization, parameter tuning, and exploring chunking results with live feedback.

    Great for experimenting with chunking strategies and comparing different settings.

    [:octicons-arrow-right-24: Learn More](visualizer.md)

</div>

Pick a card below to get started! 📇
