# Exceptions and Warnings: When Chunklet Gets a Bit Grumpy

Even the most robust tools have their moments, and Chunklet is no exception (pun intended!). This page is your guide to understanding the various hiccups and murmurs you might encounter while using Chunklet. Don't worry, most of them are easily fixed, and some are just friendly nudges.

## Exceptions: When Things Go Sideways (and Stop)

These are the big ones. When Chunklet throws an exception, it means something went wrong enough to halt the process. But fear not, we'll tell you why!

### ChunkletError

This is the grand-daddy of all Chunklet-specific errors. If you see this, it means something fundamental went wrong within Chunklet itself. It's usually a sign that a deeper issue occurred, often related to a custom function you provided.

*   **Common Scenario:** Your custom `token_counter` function decided to take a coffee break (i.e., it raised an exception).
*   **What to do:** Check your custom `token_counter` or any other custom callbacks you've provided. Make sure they're robust and handle all possible inputs gracefully.

### InvalidInputError

Chunklet is a stickler for rules, especially when it comes to your input. This error means you've given Chunklet something it just can't work with.

*   **Common Scenarios:**
    *   You tried to initialize Chunklet with some funky `custom_splitters` that didn't quite fit the mold.
    *   Your chunking configuration (like `max_tokens` or `mode`) was a bit off.
    *   In batch processing, you forgot to provide a list of texts, or you asked for a negative number of parallel jobs (we're good, but not *that* good).
*   **What to do:** Double-check your input parameters against the documentation. Make sure everything is in the right format and within the expected ranges.

### TokenNotProvidedError

This one's pretty self-explanatory, but we'll explain it anyway. If you're trying to chunk by tokens (or in hybrid mode, which also needs token awareness) but haven't told Chunklet *how* to count tokens, it'll politely (or not so politely) refuse to proceed.

*   **Common Scenario:** You set `mode="token"` or `mode="hybrid"` but didn't provide a `token_counter` when initializing Chunklet or in your `chunk()` call.
*   **What to do:** Provide a `token_counter` function. You can use a simple word counter, or for more accuracy, integrate a library like `tiktoken`. Check the [Programmatic Usage](getting-started/programmatic.md) documentation for examples.

## Warnings: Chunklet's Friendly Nudges (and Occasional Grumbles)

Warnings are Chunklet's way of saying, "Hey, I did what you asked, but you might want to know this..." They don't stop the process, but they often indicate something you could optimize or be aware of.

### "The language is set to `auto`. Consider setting the `lang` parameter to a specific language to improve performance."

*   **What it means:** You've let Chunklet guess the language of your text. While it's pretty good at it, explicitly telling it the language (`lang='en'`, `lang='fr'`, etc.) can sometimes speed things up and improve accuracy, especially for shorter texts.
*   **What to do:** If you know the language of your text, set the `lang` parameter. If not, no worries, Chunklet will do its best!

### "Low confidence in language detected. Detected: '{lang_detected}' with confidence {confidence:.2f}."

*   **What it means:** Chunklet tried its best to detect the language, but it's not super confident about its guess. This often happens with very short texts or texts that mix multiple languages.
*   **What to do:** If you know the language, set the `lang` parameter explicitly. If the text is genuinely ambiguous, just be aware that the sentence splitting might not be perfect.

### "Language not supported or detected with low confidence. Universal regex splitter was used."

*   **What it means:** Chunklet couldn't find a specialized sentence splitter for your language (or it wasn't confident enough in its detection), so it fell back to its trusty universal regex splitter. This splitter is robust but might not be as linguistically nuanced as the specialized ones.
*   **What to do:** If you need highly accurate sentence splitting for an unsupported language, consider implementing a [Custom Splitter](getting-started/programmatic.md#custom-sentence-splitter). Otherwise, the universal splitter will still get the job done!

### "Using `--batch` with `--file` is deprecated." (CLI Warning)

*   **What it means:** You're using an older way of batch processing. While it still works, we've introduced a more streamlined approach.
*   **What to do:** For batch processing multiple files, use `--input-dir`. If you're processing a single file, just provide it directly without `--batch`. Check the [CLI Usage](getting-started/cli.md) documentation for the latest methods.