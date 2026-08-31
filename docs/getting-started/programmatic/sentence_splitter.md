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

## Custom Sentence Splitters Removed ⚠️ {#custom-sentence-splitter}

!!! warning "Removed in v3.0.0"
    The custom splitter registry (`custom_splitter_registry` / `CustomSplitterRegistry`) and the `BaseSplitter` interface were removed in v3.0.0. There is no longer a way to register custom splitting logic via the registry.

    `SentenceSplitter` now always uses its built-in language handlers and, when a language isn't supported (or auto-detection confidence is low), falls back to a universal rule-based splitter (`UniversalSplitter`). For unsupported languages you can still split manually or open a feature request for the language you need.

??? info "API Reference"
    For complete technical details on the `SentenceSplitter` class, check out the [API documentation](../../reference/chunklet/sentence_splitter/sentence_splitter.md).