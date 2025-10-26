# Supported Languages

Chunklet leverages powerful third-party libraries and flexible customization options to provide robust multilingual support. While we list the languages explicitly supported by our integrated libraries below, for the most comprehensive and up-to-date information, we highly recommend checking their official documentation.

If your language isn't explicitly listed, or if you require specialized handling, you have one powerful option:

1.  **Custom Splitters:** You can integrate your own sentence splitting logic by registering custom splitter functions. This allows you to define precise rules for specific languages or domains.

    You can register a splitter in two ways:

    **a) Using the `register_splitter` function:**

    ```python
    from chunklet.sentence_splitter.registry import register_splitter

    def my_custom_splitter(text: str) -> list[str]:
        # Your custom splitting logic here
        return text.split('.')

    # Register the splitter for English
    register_splitter('en', callback=my_custom_splitter, name='MyCustomSplitter')
    ```

    **b) Using the `@registered_splitter` decorator:**

    ```python
    from chunklet.sentence_splitter.registry import registered_splitter

    @registered_splitter('fr', name='MyFrenchSplitter')
    def my_french_splitter(text: str) -> list[str]:
        # Your custom splitting logic for French
        return text.split('!')
    ```

## Languages supported by `pysbd`

`pysbd` (Python Sentence Boundary Disambiguation) offers highly accurate sentence boundary detection for a wide array of languages. For the complete and most current list, please refer to the [official pysbd documentation](https.pypi.org/project/pysbd/).

| Language Code | Language Name |
|:--------------|:--------------|
| en            | English       |
| mr            | Marathi       |
| hi            | Hindi         |
| bg            | Bulgarian     |
| es            | Spanish       |
| ru            | Russian       |
| ar            | Arabic        |
| am            | Amharic       |
| hy            | Armenian      |
| fa            | Persian (Farsi)|
| ur            | Urdu          |
| pl            | Polish        |
| zh            | Chinese (Mandarin)|
| nl            | Dutch         |
| da            | Danish        |
| fr            | French        |
| it            | Italian       |
| el            | Greek         |
| my            | Burmese (Myanmar)|
| ja            | Japanese      |
| de            | German        |
| kk            | Kazakh        |
| sk            | Slovak        |

## Languages Unique to `sentence-splitter`

`sentence-splitter` provides support for additional languages that are *not* covered by `pysbd`, thus complementing its coverage. For the complete and most current list, please refer to the [official sentence-splitter documentation](https://github.com/mediacloud/sentence-splitter).

| Language Code | Language Name |
|:--------------|:--------------|
| ko            | Korean        |
| lt            | Lithuanian    |
| pt            | Portuguese    |
| tr            | Turkish       |

## Languages Unique to `Indic NLP Library`

The Indic NLP Library offers support for a range of Indian languages.

| Language Code | Language Name |
|:--------------|:--------------|
| as            | Assamese      |
| bn            | Bengali       |
| gu            | Gujarati      |
| kn            | Kannada       |
| ml            | Malayalam     |
| ne            | Nepali        |
| or            | Odia          |
| pa            | Punjabi       |
| sa            | Sanskrit      |
| ta            | Tamil         |
| te            | Telugu        |

## Languages Unique to `Sentencex`

`Sentencex` provides support for the following languages not covered by other libraries.

| Language Code | Language Name |
|:--------------|:--------------|
| ca            | Catalan       |
| fi            | Finnish       |

## Fallback Splitter

For any language not explicitly supported by the libraries above, Chunklet employs a rule-based, language-agnostic sentence boundary detector. This ensures that text can always be segmented, even if language-specific rules are not available.
