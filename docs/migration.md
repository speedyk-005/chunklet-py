# Migration Guide from v1 to v2: What's New and How to Adapt!   

Hello there, fellow Chunklet enthusiast! 👋 Ready to explore the exciting new world of Chunklet v2? We've been hard at work, making Chunklet-py even more robust, flexible, and, dare we say, *efficient*! This guide is designed to walk you through all the fantastic changes and help you smoothly transition your existing code. No need to worry, we're here to support you every step of the way!

## 💥 Breaking Changes: A Quick Heads-Up! 💥

We've implemented some significant changes to enhance Chunklet-py's architecture and overall usability. While these updates might require minor adjustments to your existing code, we believe the improvements are well worth it!

### Renamed `Chunklet` class to `PlainTextChunker`

Our core chunking class now has a new, more descriptive name!

**What's new with `Chunklet`?** The class you knew as `Chunklet` has been thoughtfully renamed to `PlainTextChunker`!

**Why the glow-up?** We wanted to give it a name that *really* screams 'I chunk plain text!' This clears the stage for other awesome chunkers (like our new [DocumentChunker](getting-started/programmatic/document_chunker.md) and [CodeChunker](getting-started/programmatic/code_chunker.md)) to shine. It's all about clarity and making Chunklet's family tree a bit more logical!

**How to adapt your code?** A simple find-and-replace will do the trick! Just update your imports and class instantiations:

=== "Before (v1.4.0)"

    ```python
    from chunklet import Chunklet
    chunker = Chunklet()
    ```

=== "After (v2.0.0)"

    ```python
    from chunklet import PlainTextChunker
    chunker = PlainTextChunker()
    ```

### Removed `use_cache` flag from `PlainTextChunker`

The `use_cache` flag has been removed from the `PlainTextChunker`.

**Where did `use_cache` go?** The `use_cache=False` flag has been officially retired! You won't find it in `PlainTextChunker`'s `chunk` or `batch_chunk` methods anymore.

**Why the change?** We've streamlined Chunklet-py to manage its own caching internally, optimizing for speed without requiring any manual intervention from you. This simplifies the API, allowing you to focus on the core task of chunking!

**How to adapt your code:** Simply remove the `use_cache` argument from your `chunk` and `batch_chunk` calls. It's a small change that leads to a cleaner API!

=== "Before (v1.4.0)"

    ```python
    chunker = PlainTextChunker()
    chunks = chunker.chunk(text, use_cache=False)
    ```

=== "After (v2.0.0)"

    ```python
    chunker = PlainTextChunker()
    chunks = chunker.chunk(text)
    ```

### Removed `preview_sentences` method

The `preview_sentences` method has been removed from the main chunker class.

**Missing `preview_sentences`?** This method has transitioned out of the `PlainTextChunker` (formerly `Chunklet`) instance. It's a sign of growth!

**Why the change?** We've refactored the sentence splitting logic into its own dedicated utility, [SentenceSplitter](getting-started/programmatic/sentence_splitter.md)! This enhances modularity and flexibility, giving sentence splitting the focused attention it deserves.

**How to access sentence splitting now?** You can directly utilize the `SentenceSplitter` class. It's ready for action:

=== "Before (v1.4.0)"

    ```python
    from chunklet import Chunklet
    chunker = Chunklet()
    sentences, warnings = chunker.preview_sentences(text, lang="en")
    ```

=== "After (v2.0.0)"

    ```python
    from chunklet import SentenceSplitter
    splitter = SentenceSplitter()
    sentences = splitter.split(text, lang="en")
    ```

### Default Limits for `max_tokens` and `max_sentences`

We've adjusted the default chunking limits to provide more optimized defaults for common use cases.

**Slightly smaller, but way smarter defaults!** We've tweaked the default `max_tokens` from `512` to `256`, and `max_sentences` from a whopping `100` to a more sensible `12`.

**Why the new numbers?** These defaults are now perfectly tailored for typical LLM context window sizes and common chunking strategies. Less configuration headache, more seamless chunking bliss!

**Prefer the previous defaults?** If you'd like to retain the older default values, you can easily do so by explicitly setting `max_tokens` or `max_sentences` in your `chunk` or `batch_chunk` calls.

=== "Before (v1.4.0 - implicit defaults)"

    ```python
    chunker = PlainTextChunker()
    chunks = chunker.chunk(text, mode="token") # max_tokens=512
    ```

=== "After (v2.0.0 - explicit for old behavior)"

    ```python
    chunker = PlainTextChunker()
    chunks = chunker.chunk(text, mode="token", max_tokens=512) # To retain old default
    ```

### Language Detection Logic Integrated

The standalone language detection utility has found a new home!

**Where's the language expert?** Our old `detect_text_language.py` has hung up its hat (or rather, its file path). Its brilliant brainpower is now living directly inside `src/chunklet/sentence_splitter/sentence_splitter.py`, making language detection a super-integrated part of the splitting process!

**Why the internal move?** We wanted to simplify the internal magic and put our language detective right on the front lines with the sentence-splitting squad! Optimized, integrated, and ready to roll!

**Need to find your language?** If you were directly importing `detect_text_language`, you'll need to update those imports. But good news for most: if you're interacting with Chunklet via the `PlainTextChunker`, all this magic happens behind the scenes! Need to explicitly detect language? `SentenceSplitter`'s got a fresh `detected_top_language` method just for you:

=== "Before (v1.4.0)"

    ```python
    from chunklet.utils.detect_text_language import detect_text_language
    lang, confidence = detect_text_language(text)
    ```

=== "After (v2.0.0)"

    ```python
    from chunklet.sentence_splitter import SentenceSplitter
    splitter = SentenceSplitter()
    lang, confidence = splitter.detected_top_language(text)
    ```

### Custom Sentence Splitters: Your Rules, Our Game!

Have a unique way you prefer your sentences split? We've made it even simpler to integrate your own custom sentence splitting logic!

**Say goodbye to `custom_splitters` parameter!** The `custom_splitters` parameter in our (now named `PlainTextChunker`) constructor has gracefully retired. Custom splitters now reside in a super handy, centralized registry (`src/chunklet/sentence_splitter/registry.py`)!

**Why the registry revamp?** We've crafted a more robust, organized, and flexible hub for your custom splitting logic! This change thoughtfully decouples splitter registration from the `PlainTextChunker`, enabling global registration and effortless reuse of your fantastic custom splitters across *all* instances. It's like giving your custom splitters the VIP treatment they deserve!

**Time for a quick code update:** If you were using that old `custom_splitters` parameter, it's time to embrace our new, more elegant registry system. We're confident you'll find it a breeze! For more details on how to create and register your own splitters, see the [Custom Sentence Splitter documentation](getting-started/programmatic/sentence_splitter.md#custom-sentence-splitter).

=== "Before (v1.4.0)"

    ```python
    import re
    from chunklet import Chunklet
    from typing import List

    # Define a simple custom sentence splitter
    def my_custom_splitter(text: str) -> List[str]:
        # This is a very basic splitter for demonstration
        # In a real scenario, this would be a more sophisticated function
        return [s.strip() for s in re.split(r'(?<=\.)\\s+', text) if s.strip()]

    # Initialize Chunklet with the custom splitter
    chunker = Chunklet(
        custom_splitters=[
            {
                "name": "MyCustomEnglishSplitter",
                "languages": "en",
                "callback": my_custom_splitter,
            }
        ]
    )

    text = "This is the first sentence. This is the second sentence. And the third."
    sentences, warnings = chunker.preview_sentences(text=text, lang="en")

    print("---" + " Sentences using Custom Splitter ---")
    for i, sentence in enumerate(sentences):
        print(f"Sentence {i+1}: {sentence}")

    if warnings:
        print("\n---" + " Warnings ---")
        for warning in warnings:
            print(warning)
    ```

=== "After (v2.0.0)"

    ```python
    from chunklet.sentence_splitter.registry import registered_splitter
    from chunklet import PlainTextChunker # Updated class name
    import re

    # If 'name' is not provided, the function's name ('my_awesome_splitter' in this case) will be used.
    # When using the decorator, the decorated function itself is automatically registered as the callback;
    @registered_splitter("en", name="MyAwesomeEnglishSplitter")
    def my_awesome_splitter(text: str) -> list[str]:
        # Your super-duper custom splitting logic here!
        return [s.strip() for s in re.split(r'[.!?]\s+', text) if s.strip()]

    # If you prefer not to use decorators, you can use the 'register_splitter' function instead.
    # from chunklet.sentence_splitter.registry import register_splitter
    # register_splitter("en", callback=my_awesome_splitter, name="MyAwesomeEnglishSplitter")

    # Now, when you use PlainTextChunker with lang="en", it will use your splitter!
    chunker = PlainTextChunker()
    text = "Hello world! How are you? I am fine."
    sentences = chunker.chunk(text, lang="en", mode="sentence") # Use chunk method
    print(sentences)
    ```

### Exception Renames and Changes

We've refined our exception handling to provide more clarity and specificity.
  -   **`TokenNotProvidedError` is now `MissingTokenCounterError`**: This exception is raised when a `token_counter` is required but not provided.
  -   **`CallbackError` for Token Counter Failures**: Previously, issues within user-provided token counters might have raised a generic `ChunkletError`. Now, a more specific `CallbackError` is raised, making debugging easier.  

### CLI Usage Changes

In v1.4.0, the `chunklet` CLI had a simpler structure, primarily focused on plain text. In v2.0.0, the CLI has been reorganized for clarity and to support different chunkers.

**New `chunk` command and chunker selection!** A new `chunk` command is now the main entrypoint for all chunking operations.
- When you provide text directly as an argument, `PlainTextChunker` is used.
- When you use `--source` to provide a file path, `DocumentChunker` is used by default to handle a variety of document types.
- You can use flags like `--code` to explicitly select the `CodeChunker`.

**Why the new structure?** This change provides a clearer and more extensible command-line interface, making it easier to select the right chunker for your content.

For more details, see the [CLI Usage documentation](getting-started/cli.md).

=== "Before (v1.4.0)"

    ```bash
    chunklet "Your text here." --mode sentence --max-sentences 5
    ```

=== "After (v2.0.0)"

    ```bash
    # Chunking a string uses PlainTextChunker
    chunklet chunk "Your text here." --mode sentence --max-sentences 5

    # Chunking a file from a path uses DocumentChunker by default
    chunklet chunk --source your_text.txt --mode sentence --max-sentences 5
    ```
    
That's all for this migration guide! We truly hope these updates enhance your Chunklet-py experience and make your chunking tasks even more enjoyable. Happy chunking! 🎉