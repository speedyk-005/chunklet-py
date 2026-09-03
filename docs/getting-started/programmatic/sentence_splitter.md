# Sentence Splitter

<p align="center">
  <img src="../../../img/sentence_splitter.png?raw=true" alt="Sentence splitter" width="512"/>
</p>

## The Art of Precise Sentence Splitting ✂️

Splitting text by periods is like trying to perform surgery with a butter knife — it barely works and makes a mess. Abbreviations get misinterpreted, sentences get cut mid-thought, and your NLP models end up confused.

This problem has a name: [Sentence Boundary Disambiguation](https://en.wikipedia.org/wiki/Sentence_boundary_disambiguation). That's where `SentenceSplitter` comes in.

Think of it as a skilled linguist who knows where sentences actually end. It handles grammar, context, and those tricky abbreviations (like "Dr." or "U.S.A.") without breaking a sweat. Supports 60+ languages out of the box.

### What's Under the Hood? ⚙️

The `SentenceSplitter` is a sophisticated system:

-  **Multilingual Support 🌍:** Handles over **60** languages with intelligent detection. See the [full list](../../supported-languages.md).
-  **Reliable Fallback 🛡️:** For unsupported languages, a rule-based fallback kicks in.
-  **Output Refinement ✨:** Removes empty sentences and fixes punctuation.

!!! note "Auto language detection requires the `[auto]` extra"
    When you use `lang="auto"`, the splitter needs `py3langid` to detect the language of your text. This is not installed by default — install it with:

    ```bash
    pip install 'chunklet-py[auto]'
    ```

    If you only need specific languages (e.g. `lang="en"`), the default install is enough.

### Example Usage 

### Split Text into Sentences

Here's a quick example of how you can use the `SentenceSplitter` to split a block of text into sentences:

``` py linenums="1"
from chunklet.sentence_splitter import SentenceSplitter

TEXT = """
She loves cooking. He studies AI. "You are a Dr.", she said. The weather is great. We play chess. Books are fun, aren't they?

The Playlist contains:
  - two videos
  - one image
  - one music

Robots are learning. It's raining. Let's code. Mars is red. Sr. sleep is rare. Consider item 1. This is a test. The year is 2025. This is a good year since N.A.S.A. reached 123.4 light year more.
"""

splitter = SentenceSplitter(verbose=True, lang="auto")
sentences = splitter.split_text(TEXT)  # (1)!

for sentence in sentences:
    print(sentence)
```

1.  **Auto language detection**: Let the splitter automatically detect the language of your text by setting `lang="auto"` in the constructor. For best results, specify a language code like `"en"` or `"fr"` directly in the constructor.

??? success "Click to show output"
    ```linenums="0"
    2025-11-02 16:27:29.277 | WARNING  | chunklet.sentence_splitter.sentence_splitter:split_text:192 - The language is set to `auto`. Consider setting the `lang` parameter to a specific language to improve reliability.
    2025-11-02 16:27:29.316 | INFO     | chunklet.sentence_splitter.sentence_splitter:split_text:158 - Language detection: 'en' with confidence 10/10.
    2025-11-02 16:27:29.447 | INFO     | chunklet.sentence_splitter.sentence_splitter:split_text:166 - Text splitted into sentences. Total sentences detected: 19
    She loves cooking.
    He studies AI.
    "You are a Dr.", she said.
    The weather is great.
    We play chess.
    Books are fun, aren't they?
    The Playlist contains:
    - two videos
    - one image
    - one music
    Robots are learning.
    It's raining.
    Let's code.
    Mars is red.
    Sr. sleep is rare.
    Consider item 1.
    This is a test.
    The year is 2025.
    This is a good year since N.A.S.A. reached 123.4 light year more.
    ```

### Splitting Files: From Document to Sentences 📄

Need to split a file directly into sentences? Use `split_file`:

``` py linenums="1"
from chunklet.sentence_splitter import SentenceSplitter

splitter = SentenceSplitter(lang="en")
sentences = splitter.split_file("sample.txt")

for i, sentence in enumerate(sentences):
    print(f"Sentence {i + 1}: {sentence}")
```

??? success "Click to show output"
    ```linenums="0"
    Sentence 1: This is the first sentence.
    Sentence 2: This is the second sentence.
    Sentence 3: And the third.
    ```

??? info "API Reference"
    For complete technical details on the `SentenceSplitter` class, check out the [API documentation](../../reference/chunklet/sentence_splitter/sentence_splitter.md).