# What's New in Chunklet v2.0.0! 🎉

Welcome to Chunklet v2.0.0, where we've taken a giant leap forward in text and code chunking! Our team has been hard at work refining the core architecture, enhancing language support, and making the library even more robust and user-friendly. Get ready for a quick tour of the exciting new features and significant improvements:

## ✨ Highlights of v2.0.0

*   **Class Renaming:** The `Chunklet` class has been thoughtfully renamed to `PlainTextChunker`! This change provides clearer semantics and sets the stage for other specialized chunkers. And don't worry about adapting your code – our [Migration Guide](migration.md) is here to help you every step of the way!
*   **Continuation marker:** 📑 Improved the continuation marker logic and exposed it's value so users can define thier own or set it to an empty str to disabled it.
*   **Code Chunker Introduction:** We're excited to introduce `CodeChunker`! 🧑‍💻 This new, rule-based, language-agnostic chunker offers a significant advancement for syntax-aware code splitting. It's designed to be highly effective for your code-related RAG needs!
*   **Document Chunker Introduction:** We're pleased to introduce `DocumentChunker`! 📄 This robust tool is designed to efficiently process a wide variety of file formats, including `.pdf`, `.docx`, `.txt`, `.md`, `.rst`, `.rtf`, `.tex`, `.html/hml`, and `.epub`. It's ready to help you manage your diverse document processing needs!
*   **Expanded Language Support:** ¡Hola! Bonjour! Namaste! 🗣️ We've gone from 36+ to a staggering 50+ languages! This linguistic leap is thanks to our integrated library dream team (`sentsplit`, `sentencex`, `indic-nlp-library`) and some seriously clever fallback mechanisms. Prepare for global domination!
*   **New Constraint Flags:** We've introduced `max_section_breaks` for PlainTextChunker and DocumentChunker, and `max_lines` for CodeChunker. These new flags provide even more granular control over how your text and code are chunked, allowing for highly customized segmentation strategies!
*   **Improved Error Handling:** No more head-scratching! 🤯 We've rolled out more specific exception types (like `FileProcessingError` and `CallbackError`) and a centralized batch error handling system. This means crystal-clear feedback and ultimate control when things inevitably go a little wonky.
*   **Flexible Batch Error Handling:** Ever wished you could tell Chunklet *exactly* what to do when an error pops up in a batch? Now you can! The new `on_errors` parameter lets you play puppet master: `raise` a dramatic fuss, `skip` it like a pro, or `break` for a well-deserved coffee. Your kingdom, your rules!
*   **CLI Refactoring:** Our command-line interface has been to the spa and gotten a full makeover! ✨ It's now super streamlined with simplified input/output flags and turbocharged batch processing capabilities. Get ready for a CLI experience so smooth, it's practically butter!
*   **Modularity & Extensibility:** We've gone full LEGO! 🧱 The library's architecture is now incredibly modular, boasting a dedicated `SentenceSplitter` and a flexible custom splitter registry. Build your chunking dreams, piece by piece, with unparalleled ease!
*   **Performance & Memory Optimization:** Say goodbye to memory hogs and hello to lightning speed! ⚡ We've unleashed significant refactoring, harnessing generators for batch methods to drastically slash memory footprint for even the most colossal documents. Your RAM will sing praises!
*   **Caching Strategy Refined:** We've gone lean and mean!♻️ In-memory caching has been largely (but strategically) removed to prioritize raw performance optimization. Only `count_tokens` gets to keep its cozy cache. Speed is the name of the game, and we're playing to win!
*   **Python 3.8/3.9 Support Dropped:** Time marches on, and so do we! 🕰️ Official support for Python 3.8 and 3.9 has gracefully retired. To keep up with the latest and greatest, the minimum required Python version is now 3.10. Upgrade your Python, upgrade your life!
*   **CLI Flags Deprecation (--no-cache, --batch, --mode):** Out with the old, in with the streamlined! 👋 We've tidied up the CLI by waving goodbye to the redundant `--no-cache`, the deprecated `--batch`, and the `--mode` arguments. Less clutter, more clarity, and a happier command line!


## 🗺️ Want to see how far we've come? Check out previous versions!

For a detailed list of *every single* tweak, fix, and improvement across all versions, including the nitty-gritty details of v2.0.0 and beyond, explore our comprehensive [Changelog](https://github.com/speedyk-005/chunklet-py/blob/main/CHANGELOG.md). It's like a historical novel, but for code!