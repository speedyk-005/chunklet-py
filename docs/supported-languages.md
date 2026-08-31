# Supported Languages: A World Tour 🌍

So you want to know if Chunklet-py speaks your language? Short answer: probably yes. Long answer: keep reading!

I've built Chunklet-py to be quite the polyglot. Thanks to **yasbd** (our own from-scratch SBD library) plus the Indic NLP Library and Sentencex, it can handle **62** languages out of the box. And if your language isn't on the list? Don't sweat it, the fallback splitter's got you covered. Think of it as that friend who kind of understands every language at the party.

We use [ISO 639-1](https://en.wikipedia.org/wiki/ISO_639-1) codes (those handy two-letter shortcuts like `en`, `fr`, `es`). Check out Wikipedia's [full list](https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes) if you're hunting for a specific code.

---

## The All-Stars: Languages Where Chunklet-py Truly Shines ⭐

Here's where we bring out the big guns. These languages have dedicated, high-quality splitters — think of them as the VIP section of our language support. If your language is here, you're in good hands.

And if it's not? No worries — the [Fallback Splitter](#the-universal-translator-fallback-splitter) at the bottom of this page has your back.

Let me introduce you to the libraries making this magic happen:

### The Headliner: `yasbd`

This is our workhorse. **yasbd** (Yet Another Sentence Boundary Detector) is our own from-scratch library. Read about why we built it and how it compares to pysbd here: [yasbd-lib vs pysbd: Two Philosophies of Sentence Boundary Detection](https://dev.to/speed_k_7e1b449706e59e433/yasbd-lib-vs-pysbd-two-philosophies-of-sentence-boundary-detection-i88)

| Language Code | Language Name | Flag |
|:--------------|:--------------|:----:|
| af            | Afrikaans     | 🇿🇦 |
| am            | Amharic       | 🇪🇹 |
| ar            | Arabic        | 🇸🇦 |
| bg            | Bulgarian     | 🇧🇬 |
| bn            | Bengali       | 🇧🇩 |
| cs            | Czech         | 🇨🇿 |
| da            | Danish        | 🇩🇰 |
| de            | German        | 🇩🇪 |
| el            | Greek         | 🇬🇷 |
| en            | English       | 🇬🇧 |
| es            | Spanish       | 🇪🇸 |
| fa            | Persian (Farsi)| 🇮🇷 |
| fr            | French        | 🇫🇷 |
| hi            | Hindi         | 🇮🇳 |
| ht            | Haitian Creole| 🇭🇹 |
| hy            | Armenian      | 🇦🇲 |
| id            | Indonesian    | 🇮🇩 |
| it            | Italian       | 🇮🇹 |
| ja            | Japanese      | 🇯🇵 |
| kk            | Kazakh        | 🇰🇿 |
| ko            | Korean        | 🇰🇷 |
| lt            | Lithuanian    | 🇱🇹 |
| ml            | Malayalam     | 🇮🇳 |
| mr            | Marathi       | 🇮🇳 |
| my            | Burmese (Myanmar)| 🇲🇲 |
| nl            | Dutch         | 🇳🇱 |
| pl            | Polish        | 🇵🇱 |
| pt            | Portuguese    | 🇵🇹 |
| ro            | Romanian      | 🇷🇴 |
| ru            | Russian       | 🇷🇺 |
| sk            | Slovak        | 🇸🇰 |
| sv            | Swedish       | 🇸🇪 |
| sw            | Swahili       | 🇹🇿 |
| th            | Thai          | 🇹🇭 |
| tr            | Turkish       | 🇹🇷 |
| uk            | Ukrainian     | 🇺🇦 |
| ur            | Urdu          | 🇵🇰 |
| vi            | Vietnamese    | 🇻🇳 |
| zh            | Chinese (Mandarin)| 🇨🇳 |

### The Indian Subcontinent Squad: `Indic NLP Library`

The [`Indic NLP Library`](https://github.com/anoopkunchukuttan/indic_nlp_library) handles 11 languages from the Indian subcontinent. These languages have some pretty complex scripts, so specialized support is a must.

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

### The Wildcard: `Sentencex`

[`Sentencex`](https://github.com/wikimedia/sentencex) from Wikimedia adds even more languages to the mix. It's a bit more relaxed about things — uses fallbacks when it doesn't have a perfect match for your language.

!!! tip "Wait, what's a fallback?"
    Good question! If `Sentencex` doesn't have a perfect splitter for your language, it falls back to a similar one. Like using Spanish rules for Galician — close enough, usually gets the job done.

    I've filtered the list below to only show languages that are actually useful and reliable. No point showing you 200 languages if half of them are just "eh, good enough" — right?

| Language Code | Language Name | Flag |
|:--------------|:--------------|:----:|
| an            | Aragonese     | 🇪🇸 |
| ca            | Catalan       | 🇪🇸 |
| co            | Corsican      | 🇫🇷 |
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

## The Universal Translator: Fallback Splitter 🔄

So your language isn't on the list? That's okay — this is where things get interesting.

The **Fallback Splitter** is my "when in doubt" solution. It's a rule-based regex splitter that takes a reasonable shot at sentence segmentation for... well, anything. Is it as smart as the dedicated libraries above? Nope. But it'll work when you need it to.

Think of it as that friend at the karaoke bar who doesn't know the song but will still give it their best shot. 🥤

!!! info "API Reference"
    For the nerds who want the full details, check out the [`_universal_splitter` API docs](reference/chunklet/sentence_splitter/_universal_splitter.md).

---

## Custom Splitters Removed ⚠️

!!! warning "Removed in v3.0.0"
    The custom splitter registry (`custom_splitter_registry`) was removed in v3.0.0. There is no longer a way to register your own splitting logic.

    For languages not covered by the built-in handlers, `SentenceSplitter` automatically falls back to the universal rule-based splitter above. If you need proper support for a specific language, consider requesting it or contributing a handler.
