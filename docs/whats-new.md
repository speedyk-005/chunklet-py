!!! info "What's on This Page"
    This page highlights the **big features and major changes** for each version. For all the nitty-gritty details, check out our [full changelog](https://github.com/speedyk-005/chunklet-py/blob/main/CHANGELOG.md).

---

## Chunklet v2.2.0

### ✨ Simpler Chunking API

We've cleaned up the chunking method names to make them more intuitive:

- **chunk_text()** - Chunk a string of text
- **chunk_file()** - Chunk a file directly
- **chunk_texts()** - Batch process multiple texts
- **chunk_files()** - Batch process multiple files

The old methods still work but show a friendly deprecation warning.

### 🔗 PlainTextChunker Joins DocumentChunker

The `PlainTextChunker` class has been merged into `DocumentChunker`. Use `chunk_text()` for single texts or `chunk_texts()` for batch processing. The old `PlainTextChunker` import still works with a deprecation warning.

### ✂️ SentenceSplitter Gets Slicing Upgrades

The `SentenceSplitter` now uses `split_text()` instead of the deprecated `split()` method. A new `split_file()` method lets you split files directly into sentences.

### 🎨 A Fresh New Look for the Visualizer

The chunk visualizer got a complete makeover:

- **Fullscreen Mode** - Present your results without distractions
- **3-Row Layout** - Cleaner, more intuitive design
- **Smoother Interactions** - No more jumpy hover effects when exploring chunks
- **Smarter Buttons** - Stay enabled after processing so you can download anytime

### 🧑‍💻 Code Chunking Just Got Smarter

Better code understanding with zero extra work from you:

- **Cleaner Output** - Fixed weird artifacts in chunks from comment handling
- **More Languages** - Now supports Forth, PHP 8 attributes, VB.NET, ColdFusion, and Pascal
- **String Protection** - Multi-line strings and triple-quotes are now protected

### 🔧 Small Things, Big Difference

- **Tokenizer Timeout** - Custom tokenizers now have a 10-second timeout so your processing never hangs forever
- **Global Registries** - Added `custom_splitter_registry` and `custom_processor_registry` for easier customization
- **Better Errors** - Clearer messages when things go wrong

---

## Chunklet v2.1.1

### 🐛 Visualizer Was Broken

The chunk visualizer wasn't working after installation from PyPI - static files were missing. That's now fixed!

---

## Chunklet v2.1.0

### 🌐 Your First Look at the Visualizer

A brand new way to explore chunking:

- Interactive web interface for real-time parameter tuning
- Launch with `chunklet visualize`
- Works with all chunker types

### 📁 More File Formats

Added support for ODT, CSV, and Excel files - now you can process pretty much anything.

---

## Chunklet v2.0.0

### 🚀 The Big Rewrite

This was a massive update that changed everything:

- ** 🗃 New Classes** - PlainTextChunker, DocumentChunker, and CodeChunker
- ** 🌍 50+ Languages** - Multilingual support for sentence splitting
- ** 📄 Document Formats** - PDF, DOCX, EPUB, HTML, and more
- ** 💻 Code Understanding** - Intelligent code-aware chunking
- ** 🎯 More Control** - New constraints like max_section_breaks and max_lines
- ** ⚡ Memory Efficient** - Generators for handling large files

---

## 🗺️ Want More Details?

Check out our [changelog](https://github.com/speedyk-005/chunklet-py/blob/main/CHANGELOG.md) for the complete story!
