# Migration Guide from v1 to v2: What's New and How to Adapt!

Hey there, awesome Chunklet user! 👋 Ready to level up your text processing game? We've been busy behind the scenes, making Chunklet even more robust, flexible, and, dare we say, *chunky*! This guide will walk you through the exciting changes and how to smoothly transition your existing code. Don't worry, we've got your back (and your chunks!).

## 💥 Breaking Changes: Pay Attention!

We've made some significant changes to improve Chunklet's architecture and usability. These might require you to update your existing code.

### Renamed `Chunklet` class to `PlainTextChunker`

The core chunking class has a new, more descriptive name!

**What changed?**
The main entry point for programmatic chunking, previously known as `Chunklet`, is now `PlainTextChunker`.

**Why the change?**
To better reflect its primary function of chunking plain text and to make room for future specialized chunker implementations (e.g., `DocumentChunker`, `CodeChunker`). It's all about clarity and future-proofing!

**How to adapt?**
Simply update your imports and class instantiations:

**Before (v1.4.0):**
```python
from chunklet import Chunklet
chunker = Chunklet()
```

**After (v2.0.0):**
```python
from chunklet import PlainTextChunker
chunker = PlainTextChunker()
```

### Removed `use_cache` flag from `PlainTextChunker`

The `use_cache` flag has been removed from the `PlainTextChunker`.

**What changed?**
You can no longer pass `use_cache=False` to the `PlainTextChunker`'s `chunk` or `batch_chunk` methods.

**Why the change?**
The `PlainTextChunker` is now focused on speed and handles caching internally where necessary. This change simplifies the API and removes the need for manual cache management.

**How to adapt?**
Simply remove the `use_cache` argument from your `chunk` and `batch_chunk` calls.

**Before (v1.4.0):**
```python
chunker = PlainTextChunker()
chunks = chunker.chunk(text, use_cache=False)
```

**After (v2.0.0):**
```python
chunker = PlainTextChunker()
chunks = chunker.chunk(text)
```

### Removed `preview_sentences` method

The `preview_sentences` method has been removed from the main chunker class.

**What changed?**
The `preview_sentences` method is no longer available directly on the `PlainTextChunker` (formerly `Chunklet`) instance.

**Why the change?**
The sentence splitting logic has been refactored into its own dedicated utility, `SentenceSplitter`. This separation of concerns makes the library more modular and allows for more flexible use of sentence splitting capabilities.

**How to adapt?**
If you need to preview sentences, you should now instantiate and use the `SentenceSplitter` directly:

**Before (v1.4.0):**
```python
from chunklet import Chunklet
chunker = Chunklet()
sentences, warnings = chunker.preview_sentences(text, lang="en")
```

**After (v2.0.0):**
```python
from chunklet import SentenceSplitter
splitter = SentenceSplitter()
sentences = splitter.split(text, lang="en")
```

### Default Limits for `max_tokens` and `max_sentences`

We've adjusted the default chunking limits to provide more sensible defaults for common use cases.

**What changed?**
-   The default `max_tokens` has changed from `512` to `256`.
-   The default `max_sentences` has changed from `100` to `12`.

**Why the change?**
These new defaults are better aligned with typical LLM context window sizes and common chunking strategies, reducing the need for explicit configuration in many scenarios.

**How to adapt?**
If your existing code relied on the old default values, you might need to explicitly set `max_tokens` or `max_sentences` in your `chunk` or `batch_chunk` calls to maintain your desired chunk sizes.

**Before (v1.4.0 - implicit defaults):**
```python
chunker = PlainTextChunker()
chunks = chunker.chunk(text, mode="token") # max_tokens=512
```

**After (v2.0.0 - explicit for old behavior):**
```python
chunker = PlainTextChunker()
chunks = chunker.chunk(text, mode="token", max_tokens=512) # To retain old default
```

### Language Detection Logic Integrated

The standalone language detection utility has found a new home!

**What changed?**
The `src/chunklet/utils/detect_text_language.py` file has been retired. Its powerful logic now lives within `src/chunklet/sentence_splitter/sentence_splitter.py`, making language detection an even more integral part of the splitting process.

**Why the change?**
To simplify the internal architecture and ensure that language detection is always optimized for sentence splitting. It's like giving our language detective a direct line to the sentence-splitting squad!

**How to adapt?**
If you were directly importing and using `detect_text_language` from its old location, you'll need to adjust your imports. However, for most users interacting with Chunklet via the `PlainTextChunker` class, this change is largely transparent – Chunklet handles the magic for you! If you need to explicitly detect the top language, you can now use the `SentenceSplitter`'s new `detected_top_language` method:

**Before (v1.4.0):**
```python
from chunklet.utils.detect_text_language import detect_text_language
lang, confidence = detect_text_language(text)
```

**After (v2.0.0):**
```python
from chunklet.sentence_splitter import SentenceSplitter
splitter = SentenceSplitter()
lang, confidence = splitter.detected_top_language(text)
```

### CLI Usage for PlainTextChunker

In v1.4.0, the `chunklet` CLI primarily supported plain text chunking, corresponding to the `PlainTextChunker` functionality.

**What changed?**
The core CLI arguments for plain text chunking remain largely the same, but the underlying implementation now uses `PlainTextChunker` explicitly. Additionally, a new specialized chunker (`DocumentChunker`) has been introduced, accessible via the `--doc` flag.

**Why the change?**
To provide a clearer separation of concerns and to enable specialized chunking capabilities for different content types.

**How to adapt?**
For basic plain text chunking, your existing CLI commands will continue to work as expected, as they will implicitly use the `PlainTextChunker`. However, if you were relying on any implicit behaviors that are now handled by `DocumentChunker`, you might need to explicitly use the `--doc` flag.

**Before (v1.4.0 - PlainTextChunker CLI):**
```bash
chunklet "Your text here." --mode sentence --max-sentences 5
```

**After (v2.0.0 - PlainTextChunker CLI):**
```bash
chunklet "Your text here." --mode sentence --max-sentences 5
# Or explicitly using --doc for text files (which defaults to PlainTextChunker internally)
chunklet --doc --file your_text.txt --mode sentence --max-sentences 5
```

### Custom Sentence Splitters: Your Rules, Our Game!

Got a special way you like your sentences split? We've made it even easier to plug in your own custom sentence splitting logic!

**What changed?**
The `custom_splitters` parameter in the `Chunklet` (now `PlainTextChunker`) constructor has been removed. Instead, custom splitters are now managed through a centralized registry (`src/chunklet/sentence_splitter/registry.py`).

**Why the change?**
This change provides a more robust, organized, and flexible way to manage custom splitting logic. It decouples the splitter registration from the `PlainTextChunker` instance, allowing for global registration and easier reuse of custom splitters across different `PlainTextChunker` instances.

**How to adapt?**
If you were previously using the `custom_splitters` parameter, you'll need to adapt your code to use the new registry system.

**Before (v1.4.0):**
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

**After (v2.0.0):**
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

That's all for this migration! We hope these updates make your Chunklet experience even more delightful. Happy chunking! 🎉