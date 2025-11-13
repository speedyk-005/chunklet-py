# Sentence Splitter

<p align="center">
  <img src="https://github.com/speedyk-005/chunklet-py/blob/major-changes/docs/img/logo_with_tagline.svg?raw=true" alt="Sentence splitter" width="300"/>
</p>

## The Art of Precise Sentence Splitting

Let's be honest, simply splitting text by periods can be a bit like trying to perform delicate surgery with a butter knife – it often leads to more problems than solutions! This approach can result in sentences being cut mid-thought, abbreviations being misinterpreted, and a general lack of clarity that can leave your NLP models scratching their heads.

This common challenge in NLP, known as [Sentence Boundary Disambiguation](https://en.wikipedia.org/wiki/Sentence_boundary_disambiguation), is precisely what the `SentenceSplitter` is designed to address.

Imagine the `SentenceSplitter` as a skilled linguistic surgeon. It applies its understanding of grammar and context to make precise cuts, cleanly separating sentences while preserving their original meaning. It's intelligent, multilingual, and an excellent tool for transforming your raw text into a well-structured list of sentences, perfectly prepared for your next NLP endeavor.

### What's Under the Hood?

The `SentenceSplitter` is more than just a basic rule-based tool; it's a sophisticated system packed with powerful features:

-  **Multilingual Maestro:** It fluently handles over **50** languages, intelligently detecting the language of your text and applying the most appropriate splitting methods. For a complete overview, check out our [supported languages](../../supported-languages.md) list.
-  **Customizable Genius:** Encounter a unique text format? No problem! You can easily integrate your own custom splitters to manage specific requirements.
-  **Fallback Guardian:** For languages not explicitly covered, a reliable fallback mechanism ensures that sentence splitting is still performed effectively.
-  **Error Detective:** It actively monitors for potential issues, providing clear feedback if any problems arise with your custom splitters.
-  **Punctuation Tamer:** It meticulously refines the output, removing empty sentences and correctly reattaching any misplaced punctuation.

### Example Usage

Here's a quick example of how you can use the `SentenceSplitter` to split a block of text into sentences:

```python
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
sentences = splitter.split(TEXT, lang="en")

for sentence in sentences:
    print(sentence)
```

??? success "Click to show output"
    ```
    2025-11-02 16:27:29.277 | WARNING  | chunklet.sentence_splitter.sentence_splitter:split:136 - The language is set to `auto`. Consider setting the `lang` parameter to a specific language to improve reliability.
    2025-11-02 16:27:29.316 | INFO     | chunklet.sentence_splitter.sentence_splitter:detected_top_language:109 - Language detection: 'en' with confidence 10/10.
    2025-11-02 16:27:29.447 | INFO     | chunklet.sentence_splitter.sentence_splitter:split:167 - Text splitted into sentences. Total sentences detected: 19
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

!!! note
    While the example above uses English (`en`), the `SentenceSplitter` is a true polyglot! It supports over 50 languages out of the box. You can see the full list of [supported languages](../../supported-languages.md).

### Detecting Top Languages

Here's how you can detect the top language of a given text using the `SentenceSplitter`:

```python
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
    ```
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

## Custom Sentence Splitter

You can provide your own custom sentence splitting functions to Chunklet. This is useful if you have a specialized splitter for a particular language or domain that you want to prioritize over Chunklet's built-in splitters.

!!! warning "Global Registry: Be Mindful of Side Effects"
    Custom splitters are registered globally. This means that once you register a splitter, it's available everywhere in your application. Be mindful of potential side effects if you're registering splitters in different parts of your codebase, especially in multi-threaded or long-running applications.

To use a custom splitter, you leverage the [`@registry.register`](../../reference/chunklet/sentence_splitter/registry.md) decorator. This decorator allows you to register your function for one or more languages directly.

!!! note "Error Handling"
    If an error occurs during the sentence splitting process (e.g., an issue with the custom splitter function), a [`CallbackError`](../../exceptions-and-warnings.md#callbackerror) will be raised.

```python
import re
from chunklet.sentence_splitter import SentenceSplitter, CustomSplitterRegistry


splitter = SentenceSplitter(verbose=False)
registry = CustomSplitterRegistry()

@registry.register("en", name="MyCustomEnglishSplitter")
def my_custom_splitter(text: str) -> list[str]:
    """A simple custom sentence splitter"""
    return [s.strip() for s in re.split(r'(?<=\\.)\s+', text) if s.strip()]

text = "This is the first sentence. This is the second sentence. And the third."
sentences = splitter.split(text=text, lang="en")

print("---" + " Sentences using Custom Splitter ---")
for i, sentence in enumerate(sentences):
    print(f"Sentence {i+1}: {sentence}")

# Example with a custom splitter for multiple languages
@registry.register("fr", "es", name="MultiLangExclamationSplitter")
def multi_lang_splitter(text: str) -> list[str]:
    return [s.strip() for s in re.split(r'(?<=!)\s+', text) if s.strip()]

splitter_multi = SentenceSplitter(verbose=False)

text_fr = "Bonjour! Comment ça va? C'est super. Au revoir!"
sentences_fr = splitter_multi.split(text=text_fr, lang="fr")
print("\n--- Sentences using Multi-language Custom Splitter (French) ---")
for i, sentence in enumerate(sentences_fr):
    print(f"Sentence {i+1}: {sentence}")

text_es = "Hola. Qué tal? Muy bien! Adiós."
sentences_es = splitter_multi.split(text=text_es, lang="es")
print("\n--- Sentences using Multi-language Custom Splitter (Spanish) ---")
for i, sentence in enumerate(sentences_es):
    print(f"Sentence {i+1}: {sentence}")


# Unregistering Custom Splitters
registry.unregister("en")            # (1)!
```

1.  This will remove the custom splitter associated with the "en" language code. Note that you can unregister multiple languages if you had registered them with the same function: registry.unregister("fr", "es")

??? success "Click to show output"
    ```
    --- Sentences using Custom Splitter ---
    Sentence 1: This is the first sentence.
    Sentence 2: This is the second sentence.
    Sentence 3: And the third.

    --- Sentences using Multi-language Custom Splitter (French) ---
    Sentence 1: Bonjour!
    Sentence 2: Comment ça va? C'est super. Au revoir!

    --- Sentences using Multi-language Custom Splitter (Spanish) ---
    Sentence 1: Hola. Qué tal? Muy bien!
    Sentence 2: Adiós.
    ```

!!! note "Registering Without the Decorator"
    If you prefer not to use decorators, you can directly use the `registry.register()` method. This is particularly useful when registering splitters dynamically or when the callback function is not defined in the global scope.

    ```python
    from chunklet.sentence_splitter import CustomSplitterRegistry

    registry = CustomSplitterRegistry()

    def my_other_splitter(text: str) -> list[str]:
        return text.split(' ')

    registry.register(my_other_splitter, "jp", name="MyOtherSplitter")
    ```

!!! tip "Building from Scratch: Leveraging BaseSplitter"
    If you're looking to implement a sentence splitter entirely from scratch or integrate a highly custom logic, consider inheriting directly from the `BaseSplitter` abstract class. This provides a clear interface (`def split(self, text: str, lang: str) -> list[str]`) that your custom class must implement, ensuring compatibility with Chunklet's architecture. You can then pass an instance of your custom splitter to the `PlainTextChunker` ([documentation](plain_text_chunker.md)) or `DocumentChunker` ([documentation](document_chunker.md)) during their initialization.

### [`CustomSplitterRegistry`](../../reference/chunklet/sentence_splitter/registry.md) Methods Summary

*   `splitters`: Returns a shallow copy of the dictionary of registered splitters.
*   `is_registered(lang: str)`: Checks if a splitter is registered for the given language, returning `True` or `False`.
*   `register(callback: Callable[[str], list[str]] | None = None, *langs: str, name: str | None = None)`: Registers a splitter callback for one or more languages.
*   `unregister(*langs: str)`: Removes splitter(s) from the registry.
*   `clear()`: Clears all registered splitters from the registry.
*   `split(text: str, lang: str)`: Processes a text using a splitter registered for the given language, returning a list of sentences and the name of the splitter used.

??? info "API Reference"
    For a deep dive into the `SentenceSplitter` class, its methods, and all the nitty-gritty details, check out the full [API documentation](../../reference/chunklet/sentence_splitter/sentence_splitter.md).
