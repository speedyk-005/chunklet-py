# Supported Languages: A World Tour

Curious about the languages Chunklet-py supports? You're in the right place! We've built Chunklet-py to be quite the language expert, thanks to some fantastic third-party libraries. When we talk about language codes, we're usually using the [ISO 639-1 standard](https://en.wikipedia.org/wiki/ISO_639-1) (those handy two-letter codes). If you're ever wondering about other language codes, Wikipedia's [List of ISO 639 language codes](https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes) is a great resource.

---

## ⭐ The All-Stars: Officially Supported Languages

Let's dive into the languages where Chunklet-py truly shines! Through wonderful collaborations with various libraries, we're proud to offer dedicated, high-quality splitters for over **50** languages. And if your language isn't in this impressive lineup, don't you worry – our dependable [Fallback Splitter](#the-universal-translator-fallback-splitter) is always ready to lend a hand. Below, you'll discover the specific libraries that make this extensive language support possible.

### Headliner: `pysbd`

Meet `pysbd`, one of our primary tools for accurate sentence boundary detection. This library is highly effective at identifying sentence endings, even in complex linguistic contexts.

| Language Code | Language Name | Flag |
|:--------------|:--------------|:----:|
| en            | English       | 🇬🇧 |
| mr            | Marathi       | 🇮🇳 |
| hi            | Hindi         | 🇮🇳 |
| bg            | Bulgarian     | 🇧🇬 |
| es            | Spanish       | 🇪🇸 |
| ru            | Russian       | 🇷🇺 |
| ar            | Arabic        | 🇸🇦 |
| am            | Amharic       | 🇪🇹 |
| hy            | Armenian      | 🇦🇲 |
| fa            | Persian (Farsi)| 🇮🇷 |
| ur            | Urdu          | 🇵🇰 |
| pl            | Polish        | 🇵🇱 |
| zh            | Chinese (Mandarin)| 🇨🇳 |
| nl            | Dutch         | 🇳🇱 |
| da            | Danish        | 🇩🇰 |
| fr            | French        | 🇫🇷 |
| it            | Italian       | 🇮🇹 |
| el            | Greek         | 🇬🇷 |
| my            | Burmese (Myanmar)| 🇲🇲 |
| ja            | Japanese      | 🇯🇵 |
| de            | German        | 🇩🇪 |
| kk            | Kazakh        | 🇰🇿 |
| sk            | Slovak        | 🇸🇰 |

### Special Guest: `sentsplit`

`sentsplit` complements our primary tools by providing support for additional languages. It effectively extends our coverage for diverse linguistic needs.

| Language Code | Language Name | Flag |
|:--------------|:--------------|:----:|
| ko            | Korean        | 🇰🇷 |
| lt            | Lithuanian    | 🇱🇹 |
| pt            | Portuguese    | 🇵🇹 |
| tr            | Turkish       | 🇹🇷 |

### The Dance Troupe: `Indic NLP Library`

The [`Indic NLP Library`](https://github.com/anoopkunchukuttan/indic_nlp_library) is crucial for supporting the rich and diverse languages of the Indian subcontinent. It provides comprehensive linguistic support for these languages.

| Language Code | Language Name | Flag |
|:--------------|:--------------|:----:|
| as            | Assamese      | 🇮🇳 |
| bn            | Bengali       | 🇮🇳 |
| gu            | Gujarati      | 🇮🇳 |
| kn            | Kannada       | 🇮🇳 |
| ml            | Malayalam     | 🇮🇳 |
| ne            | Nepali        | 🇳🇵 |
| or            | Odia          | 🇮🇳 |
| pa            | Punjabi       | 🇮🇳 |
| sa            | Sanskrit      | 🇮🇳 |
| ta            | Tamil         | 🇮🇳 |
| te            | Telugu        | 🇮🇳 |

### The Versatile Voice: `Sentencex`

[`Sentencex`](https://github.com/wikimedia/sentencex) significantly expands Chunklet's language capabilities. This library contributes a substantial collection of languages, ensuring broad and comprehensive coverage.

!!! note
    `Sentencex` is a powerful library that uses a fallback system to support a vast number of languages.
     It uses a fallback system to support a vast number of languages. Many languages are mapped to fallbacks of more common languages. The list below is a curated selection of the more reliable and unique languages from `Sentencex`. It has been filtered to:
    *   Include only languages with an ISO 639-1 code.
    *   Exclude languages that are already covered by `pysbd`, `sentsplit`, or `Indic NLP Library`.
    *   Exclude languages that are fallbacks to other languages in the list but are not reliable enough.

| Language Code | Language Name | Flag |
|:--------------|:--------------|:----:|
| an            | Aragonese     | 🇪🇸 |
| ca            | Catalan       | 🇪🇸 |
| co            | Corsican      | 🇫🇷 |
| cs            | Czech         | 🇨🇿 |
| fi            | Finnish       | 🇫🇮 |
| gl            | Galician      | 🇪🇸 |
| io            | Ido           | 🏳️ |
| jv            | Javanese      | 🇮🇩 |
| li            | Limburgish    | 🇳🇱 |
| mo            | Moldovan      | 🇲🇩 |
| nds           | Low German    | 🇩🇪 |
| nn            | Norwegian Nynorsk | 🇳🇴 |
| oc            | Occitan       | 🇫🇷 |
| su            | Sundanese     | 🇮🇩 |
| wa            | Walloon       | 🇧🇪 |


---

## The Universal Translator: Fallback Splitter

!!! info "API Reference"

    The API documentation for the universal fallback splitter can be found in the [`FallbackSplitter` API docs](reference/chunklet/sentence_splitter/_fallback_splitter.md) file.

For languages not covered by our specialized libraries, the **Fallback Splitter** steps in. Consider it Chunklet's adaptable solution, a rule-based regex splitter designed to provide a reasonable attempt at sentence segmentation for any language. While it may not offer the nuanced precision of language-specific tools, it's a dependable option to ensure no language is left unaddressed.

---

### Teaching Chunklet New Tricks: Custom Splitters

What if your specific language or domain requires a unique approach to sentence splitting? Or perhaps you have a very particular method in mind? No need to worry! Chunklet-py is designed to be flexible, allowing you to implement and integrate your own **Custom Splitter**.
    
You can integrate your own sentence splitting logic in two ways:

**a) The Function Call Method (A Direct Approach):**

```python
from chunklet.sentence_splitter.registry import register_splitter

def my_custom_splitter(text: str) -> list[str]:
    # Your brilliant, custom splitting logic here
    return text.split('.')

# Teach Chunklet your new trick for English
register_splitter('en', callback=my_custom_splitter, name='MyCustomSplitter')
```

**b) The Decorator Method (An Elegant Approach):**

```python
from chunklet.sentence_splitter.registry import registered_splitter

@registered_splitter('fr', name='MyFrenchSplitter')
def my_french_splitter(text: str) -> list[str]:
    # Your magnifique splitting logic for French
    return text.split('!')
```

!!! tip "Global Splitter Magic"

    Feeling extra global? You can register a splitter with the special language code `xx`. This makes it a universal fallback that you can explicitly call by setting `lang='xx'` in your chunking operations. Pretty neat, huh?
