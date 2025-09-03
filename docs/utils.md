# Utils

These are the unsung heroes of Chunklet, the utility functions that work behind the scenes to make everything tick. You might not interact with them directly often, but they're crucial for Chunklet's multilingual and robust operation.

## `detect_text_language`

This function is Chunklet's linguistic detective. It automatically identifies the language of a given text, which is vital for applying the correct sentence splitting rules. It's smart enough to give you a confidence score, so you know how sure it is.

**Source Code:** [src/chunklet/utils/detect_text_language.py](https://github.com/speedyk-005/chunklet-py/blob/main/src/chunklet/utils/detect_text_language.py)

**Function Signature:**

```python
def detect_text_language(text: str) -> Tuple[str, float]:
```

**Description:**

This function uses the `py3langid` library to classify the input text and determine its language. It returns a tuple containing the detected language code (e.g., "en", "fr") and a normalized probability score representing the confidence of the detection.

**Key Features:**

-   **Numerical Stability:** Uses the log-sum-exp trick to ensure stable calculations.
-   **Focused Ranking:** Considers the top 10 language candidates for improved accuracy.

## `UniversalSplitter`

When all else fails, the `UniversalSplitter` steps in. This is Chunklet's reliable fallback for languages not explicitly supported by `pysbd` or `sentence-splitter`, or when language detection is uncertain. It uses a smart regex-based approach to split text into sentences, ensuring that even the most obscure texts get chunked.

**Source Code:** [src/chunklet/utils/universal_splitter.py](https://github.com/speedyk-005/chunklet-py/blob/main/src/chunklet/utils/universal_splitter.py)

This class provides a rule-based sentence splitter that works as a fallback when language-specific splitters are not available.

**Class:** `UniversalSplitter`

**Description:**

The `UniversalSplitter` uses a series of regular expressions to split text into sentences. It is designed to handle various edge cases, such as abbreviations, acronyms, numbered lists, and different types of punctuation.

**Key Features:**

-   **Robust Splitting:** Handles complex sentence boundaries and avoids common errors like splitting on decimals or after abbreviations.
-   **Multi-stage Processing:**
    1.  An initial split is performed based on sentence-ending punctuation.
    2.  A post-processing stage merges sentences that were incorrectly split (e.g., after an abbreviation).
    3.  A final cleanup stage normalizes whitespace and removes empty sentences.
