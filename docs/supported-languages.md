# Supported Languages: A World Tour 🌍

So you want to know if Chunklet-py speaks your language? Short answer: probably yes. Long answer: keep reading!

I've built Chunklet-py to be quite the polyglot. Thanks to some fantastic third-party libraries, it can handle over **50** languages out of the box. And if your language isn't on the list? Don't sweat it — I've got a fallback splitter that's like that friend who kind of understands every language at the party.

We use [ISO 639-1](https://en.wikipedia.org/wiki/ISO_639-1) codes (those handy two-letter shortcuts like `en`, `fr`, `es`). Check out Wikipedia's [full list](https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes) if you're hunting for a specific code.

---

## The All-Stars: Languages Where Chunklet-py Truly Shines ⭐

Here's where we bring out the big guns. These languages have dedicated, high-quality splitters — think of them as the VIP section of our language support. If your language is here, you're in good hands.

And if it's not? No worries — the [Fallback Splitter](#the-universal-translator-fallback-splitter) at the bottom of this page has your back.

Let me introduce you to the libraries making this magic happen:

### The Headliner: `pysbd`

This is our workhorse. `pysbd` (Python Sentence Boundary Detection) is incredibly good at figuring out where sentences end — even in tricky situations. It's the reason we can handle 40+ languages without making a mess of your text.

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

A few more languages needed a home, so `sentsplit` stepped in. Think of these as the opening act — still great, just a smaller crowd.

| Language Code | Language Name | Flag |
|:--------------|:--------------|:----:|
| ko            | Korean        | 🇰🇷 |
| lt            | Lithuanian    | 🇱🇹 |
| pt            | Portuguese    | 🇵🇹 |
| tr            | Turkish       | 🇹🇷 |

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

## The Universal Translator: Fallback Splitter 🔄

So your language isn't on the list? That's okay — this is where things get interesting.

The **Fallback Splitter** is my "when in doubt" solution. It's a rule-based regex splitter that takes a reasonable shot at sentence segmentation for... well, anything. Is it as smart as the dedicated libraries above? Nope. But it'll work when you need it to.

Think of it as that friend at the karaoke bar who doesn't know the song but will still give it their best shot. 🥤

!!! info "API Reference"
    For the nerds who want the full details, check out the [`FallbackSplitter` API docs](reference/chunklet/sentence_splitter/_fallback_splitter.md).

---

## Teaching Chunklet New Tricks: Custom Splitters 🛠️

What if none of this works for you? Maybe you have a weird edge case, or you're working with something really niche. That's where custom splitters come in — you bring your own splitting logic, and Chunklet-py will use it like a boss.

Here's how you can add your own splitter:

**Option A: Register Directly (The No-Nonsense Way)**

```py
from chunklet.sentence_splitter import custom_splitter_registry

def my_custom_splitter(text: str) -> list[str]:
    # Your brilliant, custom splitting logic here
    return text.split('.')

# Teach Chunklet your new trick for English
custom_splitter_registry.register(my_custom_splitter, "en", name="MyCustomSplitter")
```

**Option B: Use a Decorator (The Fancy Way)**

```py
from chunklet.sentence_splitter import custom_splitter_registry

@custom_splitter_registry.register("fr", name="MyFrenchSplitter")
def my_french_splitter(text: str) -> list[str]:
    # Your magnifique splitting logic for French
    return text.split('!')
```

!!! tip "Go Global with 'xx'"
    Register a splitter with the language code `xx` and it'll become your universal fallback. Just set `lang='xx'` when chunking and boom — your splitter runs the show.
