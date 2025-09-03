# Supported Languages

Chunklet leverages powerful third-party libraries and flexible customization options to provide robust multilingual support. While we list the languages explicitly supported by our integrated libraries below, for the most comprehensive and up-to-date information, we highly recommend checking their official documentation.

If your language isn't explicitly listed, or if you require specialized handling, you have two powerful options:

1.  **Custom Splitters:** Integrate your own sentence splitting logic. This allows you to define precise rules for specific languages or domains. Learn more about [Custom Splitters in our Models documentation](models.md#customsplitterconfig). For exemple usage check.[getting-started/programmatic.md#custom-sentence-splitter](getting-started/programmatic.md#custom-sentence-splitter)
2.  **Universal Regex Fallback:** Chunklet will automatically fall back to a smart regex-based splitter, ensuring text can always be segmented, even without specific language support.

## Languages supported by `pysbd`

`pysbd` (Python Sentence Boundary Disambiguation) offers highly accurate sentence boundary detection for a wide array of languages. For the complete and most current list, please refer to the [official pysbd documentation](https://pypi.org/project/pysbd/).

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

## Languages Unique to `sentence-splitter` (NOT Supported by `pysbd`)

`sentence-splitter` provides support for additional languages that are *not* covered by `pysbd`, thus complementing its coverage. For the complete and most current list, please refer to the [official sentence-splitter documentation](https://github.com/mediacloud/sentence-splitter).

| Language Code | Language Name |
|:--------------|:--------------|
| ca            | Catalan       |
| cs            | Czech         |
| fi            | Finnish       |
| hu            | Hungarian     |
| is            | Icelandic     |
| lv            | Latvian       |
| lt            | Lithuanian    |
| no            | Norwegian     |
| pt            | Portuguese    |
| ro            | Romanian      |
| sk            | Slovak        |
| sl            | Slovenian     |
| sv            | Swedish       |
| tr            | Turkish       |

## Fallback: Universal Regex Splitter

For any language not explicitly supported by `pysbd` or `sentence-splitter`, Chunklet employs a robust, smart regex-based splitter. This ensures that text can always be segmented, even if language-specific rules are not available. You can find more details about this in the [Utility Functions](utils.md#universalsplitter) documentation.