# Sentence Splitter

<p align="center">
  <img src="../../../img/sentence_splitter.png?raw=true" alt="Sentence splitter" width="512"/>
</p>

## The Art of Precise Sentence Splitting ✂️

Splitting text by periods is like trying to perform surgery with a butter knife — it barely works and makes a mess. Abbreviations get misinterpreted, sentences get cut mid-thought, and your NLP models end up confused.

This problem has a name: [Sentence Boundary Disambiguation](https://en.wikipedia.org/wiki/Sentence_boundary_disambiguation). That's where `SentenceSplitter` comes in.

Think of it as a skilled linguist who knows where sentences actually end. It handles grammar, context, and those tricky abbreviations (like "Dr." or "U.S.A.") without breaking a sweat. Supports 50+ languages out of the box.

### What's Under the Hood? ⚙️

The `SentenceSplitter` is a sophisticated system:

-  **Multilingual Support 🌍:** Handles over **50** languages with intelligent detection. See the [full list](../../supported-languages.md).
-  **Custom Splitters 🔧:** Plug in your own splitting logic for specialized languages or domains.
-  **Reliable Fallback 🛡️:** For unsupported languages, a rule-based fallback kicks in.
-  **Error Monitoring 🔍:** Reports issues with custom splitters clearly.
-  **Output Refinement ✨:** Removes empty sentences and fixes punctuation.

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

splitter = SentenceSplitter(verbose=True)
sentences = splitter.split_text(TEXT, lang="auto") #(1)!

for sentence in sentences:
    print(sentence)
```

1.  **Auto language detection**: Let the splitter automatically detect the language of your text. For best results, specify a language code like `"en"` or `"fr"` directly.

??? success "Click to show output"
    ```linenums="0"
    2025-11-02 16:27:29.277 | WARNING  | chunklet.sentence_splitter.sentence_splitter:split_text:192 - The language is set to `auto`. Consider setting the `lang` parameter to a specific language to improve reliability.
    2025-11-02 16:27:29.316 | INFO     | chunklet.sentence_splitter.sentence_splitter:detected_top_language:146 - Language detection: 'en' with confidence 10/10.
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

splitter = SentenceSplitter()
sentences = splitter.split_file("sample.txt", lang="en")

for i, sentence in enumerate(sentences):
    print(f"Sentence {i+1}: {sentence}")
```

??? success "Click to show output"
    ```linenums="0"
    Sentence 1: This is the first sentence.
    Sentence 2: This is the second sentence.
    Sentence 3: And the third.
    ```

### Detecting Top Languages 🎯

Here's how you can detect the top language of a given text using the `SentenceSplitter`:

``` py linenums="1"
from chunklet.sentence_splitter import SentenceSplitter

lang_texts = {
    "en": "This is a sentence. This is another sentence. Mr. Smith went to Washington. He said 'Hello World!'. The quick brown fox jumps over the lazy dog.",
    "fr": "Ceci est une phrase. Voici une autre phrase. M. Smith est allé à Washington. Il a dit 'Bonjour le monde!'. Le renard brun et rapide saute par-dessus le chien paresseux.",
    "es": "Esta es una oración. Aquí hay otra oración. El Sr. Smith fue a Washington. Dijo '¡Hola Mundo!'. El rápido zorro marrón salta sobre el perro perezoso.",
    "de": "Dies ist ein Satz. Hier ist ein weiterer Satz. Herr Smith ging nach Washington. Er sagte 'Hallo Welt!'. Der schnelle braune Fuchs springt über den faulen Hund.",
    "hi": "यह एक वाक्य है। यह एक और वाक्य है। श्री स्मिथ वाशिंगटन गए। उसने कहा 'नमस्ते दुनिया!'। तेज भूरा लोमड़ी आलसी कुत्ते पर कूदता है।"
}

splitter = SentenceSplitter()

for lang, text in lang_texts.items():
    detected_lang, confidence = splitter.detected_top_language(text)
    print(f"Original language: {lang}")
    print(f"Detected language: {detected_lang} with confidence {confidence:.2f}")
    print("-" * 20)
```

??? success "Click to show output"
    ```linenums="0"
    Original language: en
    Detected language: en with confidence 1.00
    --------------------
    Original language: fr
    Detected language: fr with confidence 1.00
    --------------------
    Original language: es
    Detected language: es with confidence 1.00
    --------------------
    Original language: de
    Detected language: de with confidence 1.00
    --------------------
    Original language: hi
    Detected language: hi with confidence 1.00
    --------------------
    ```

## Custom Sentence Splitter: Your Playground 🎨 {#custom-sentence-splitter}

Want to bring your own splitting logic? You can plug in custom splitter functions to Chunklet! Perfect for specialized languages or domains.

!!! warning "Global Registry Alert!"
    Custom splitters get registered globally - once you add one, it's available everywhere in your app. Watch out for side effects if you're registering splitters across different parts of your codebase, especially in multi-threaded or long-running applications!

To use a custom splitter, you leverage the [`@registry.register`](../../reference/chunklet/sentence_splitter/registry.md) decorator. This decorator allows you to register your function for one or more languages directly. Your custom splitter function must accept a single `text` parameter (str) and return a `list[str]` of sentences.

!!! important "Custom Splitter Rules"
    - Your function must accept exactly one required parameter (the text)
    - Optional parameters with defaults are totally fine
    - Must return a list of strings
    - Empty strings get filtered out automatically
    - Lambda functions work if you provide a `name` parameter
    - Errors during splitting will raise a [`CallbackError`](../../exceptions-and-warnings.md#callbackerror)

#### Basic Custom Splitter

Create a custom sentence splitter for a single language using the registry decorator:

``` py linenums="1" hl_lines="2 6-9"
import re
from chunklet.sentence_splitter import SentenceSplitter, custom_splitter_registry

splitter = SentenceSplitter(verbose=False)

@custom_splitter_registry.register("en", name="MyCustomEnglishSplitter")
def english_sent_splitter(text: str) -> list[str]:
    """A simple custom sentence splitter"""
    return [s.strip() for s in re.split(r'(?<=\\.)\s+', text) if s.strip()]

text = "This is the first sentence. This is the second sentence. And the third."
sentences = splitter.split_text(text=text, lang="en")

print("--- Sentences using Custom Splitter ---")
for i, sentence in enumerate(sentences):
    print(f"Sentence {i+1}: {sentence}")
```

??? success "Click to show output"
    ```linenums="0"
    --- Sentences using Custom Splitter ---
    Sentence 1: This is the first sentence.
    Sentence 2: This is the second sentence.
    Sentence 3: And the third.
    ```

#### Multi-Language Custom Splitter

Register the same splitter function for multiple languages at once:

``` py linenums="1" hl_lines="1"
@custom_splitter_registry.register("fr", "es", name="MultiLangExclamationSplitter")  #(1)!
def multi_lang_splitter(text: str) -> list[str]:
    return [s.strip() for s in re.split(r'(?<=!)\s+', text) if s.strip()]
```

1.  This registers the same custom splitter for both French ("fr") and Spanish ("es") languages.

#### Unregistering Custom Splitters

Remove a registered custom splitter when you no longer need it:

``` py linenums="1"
custom_splitter_registry.unregister("en")  # (1)!
```

1.  This will remove the custom splitter associated with the "en" language code. Note that you can unregister multiple languages if you had registered them with the same function: `registry.unregister("fr", "es")`

!!! note "Skip the Decorator?"
    Not a fan of decorators? No worries - you can directly use the `registry.register()` method. Super handy for dynamic registration or when your callback function isn't in the global scope.

    ``` py linenums="1"
    from chunklet.sentence_splitter import custom_splitter_registry

    def my_other_splitter(text: str) -> list[str]:
        return text.split(' ')

    custom_splitter_registry.register(my_other_splitter, "jp", name="MyOtherSplitter")
    ```

!!! tip "Want to Build from Scratch?"
    Going full custom? Inherit from the `BaseSplitter` abstract class! It gives you a clear interface (`def split(self, text: str, lang: str) -> list[str]`) to implement. Your custom splitter will then work seamlessly with [`DocumentChunker`](document_chunker.md).

### [`CustomSplitterRegistry`](../../reference/chunklet/sentence_splitter/registry.md) Methods Summary

*   `splitters`: Returns a shallow copy of the dictionary of registered splitters.
*   `is_registered(lang: str)`: Checks if a splitter is registered for the given language, returning `True` or `False`.
*   `register(callback: Callable[[str], list[str]] | None = None, *langs: str, name: str | None = None)`: Registers a splitter callback for one or more languages.
*   `unregister(*langs: str)`: Removes splitter(s) from the registry.
*   `clear()`: Clears all registered splitters from the registry.
*   `split(text: str, lang: str)`: Processes a text using a splitter registered for the given language, returning a list of sentences and the name of the splitter used.

??? info "API Reference"
    For complete technical details on the `SentenceSplitter` class, check out the [API documentation](../../reference/chunklet/sentence_splitter/sentence_splitter.md).