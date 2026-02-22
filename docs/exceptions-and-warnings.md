# Exceptions and Warnings 🛑

Sometimes things break. Sometimes they almost break. Here's what it means.

---

## Exceptions 💥

### `ChunkletError`

The base exception. Catch this if you want to catch all the things. One ring to rule them all. All other exceptions in this library inherit from this, so catching this one catches everything.

### `InvalidInputError`

You passed something wrong. Wrong type, missing required field, bad file extension, etc. We tried to work with it but couldn't. This is our way of saying "that doesn't look right" — we validate inputs on the way in so you find out early.

**Fix:** Check the error message. It usually tells you what's up. Yes, actually read it.

---

### `MissingTokenCounterError` 🔢

You tried to chunk by tokens but forgot to give us a `token_counter`. We can't read minds... yet. Without it, we have no idea how many tokens your text has, so we can't enforce `max_tokens`. This only applies to token-based chunking — if you're using sentences or lines, you're fine.

**Fix:** Pass one:

```py
chunker.chunk_text(text, token_counter=some_counter)
# or
chunker = SomeChunker(token_counter=some_counter)
```

---

### `FileProcessingError` 📁

File couldn't be read. Missing, permissions, encoding issues, corrupted — something went wrong and we gave up. This happens when we try to open a file and it fails, whether the file doesn't exist, you don't have permission, it's binary garbage, or it's just broken.

**Fix:** Check if the file exists and actually opens.

---

### `UnsupportedFileTypeError` 📄

We don't support that file extension. We checked our list of supported formats and yours wasn't on it. This can also happen if:

- The processor for that file type returns an iterable (not a string), which requires batch processing 🔄
- The file has no extension, so we don't know how to handle it

The list of supported formats includes things like `.txt`, `.md`, `.pdf`, `.docx`, `.epub`, `.html`, `.rst`, `.rtf`, `.tex`, `.odt`, `.csv`, and `.xlsx`. If your file isn't one of these, you'll see this error.

**Fix:** Use a supported format, register a [custom processor](./getting-started/programmatic/document_chunker.md#custom-document-processors), or use `chunk_files([path])` for formats that require batch processing.

---

### `TokenLimitError` 📏

A code block is too fat for `max_tokens` and you're in `strict` mode. We refuse to split it because that would break the code. This happens in `CodeChunker` when a function or class is larger than your token limit — splitting it would result in broken, unrunnable code, so we error instead.

**Fix:** Bump `max_tokens` or set `strict=False` (which will split it anyway, even if it breaks).

---

### `CallbackError` 🔌

Your custom callback (token_counter, splitter, processor) threw an error. Whatever you wrote in that function crashed. We wrap this so you know the error came from your code, not ours — the traceback will point you to exactly where things went sideways.

**Fix:** Debug your callback. The stack trace has the answers.

---

## Warnings ⚠️

### Language auto-detect 🌍

```
The language is set to `auto`. Consider setting `lang` explicitly.
```

**What it means:** We don't know what language your text is. Auto-detect works, but explicit is faster and more reliable, especially with short texts. Language detection is a guess — short texts have less signal, so the guess is less confident.

**Fix:** Pass `lang='en'` (or whatever) if you know it.

---

### Universal splitter fallback 🌐

```
Using universal rule-based splitter. Language not supported or detected with low confidence.
```

**What it means:** No specialized splitter for your language exists in pysbd. We're using the generic regex fallback instead. Some languages have complex punctuation rules that the specialized splitters handle — the fallback is a one-size-fits-all that works okay but isn't great for anything.

**Fix:** Either provide a [custom splitter](./getting-started/programmatic/sentence_splitter.md#custom-sentence-splitter), or don't worry — the fallback is decent enough.

---

### Offset out of range 📍

```
Offset {} >= total sentences {}. Returning empty list.
```

**What it means:** Your offset is bigger than the text. There's nothing left to split so we return nothing. This is just informing you — it's not an error, you just asked for more sentences than exist.

**Fix:** Use a smaller offset.

---

### Skipping failed task 🏃

```
Skipping failed task. Reason: {error}
```

**What it means:** One file in your batch choked and you set `on_errors='skip'`. We logged the error and kept going. This is intentional — you told us to continue on error, so we do. Check the logs to see what actually failed.

**Fix:** Check the reason. Fix the file or change `on_errors`.

---

### Validation failure ✅

```
Skipping document {path} due to validation failure. Reason: {reason}
```

**What it means:** File failed validation. Bad extension, corrupted, or some other issue — we couldn't process it. This happens before we even try to extract text — the file just doesn't look right.

**Fix:** Check the reason.

---

### No valid files 📂

```
No valid files found after validation. Returning empty generator.
```

**What it means:** None of your input files passed the vibe check. Wrong paths, unsupported formats, or all of them failed validation. We validated every file and found nothing worth processing.

**Fix:** Check your paths and file types.

---

### Oversized code block 💪

```
Splitting oversized block ({token_count} tokens) into sub-chunks
```

**What it means:** A code block exceeded `max_tokens`. In non-strict mode, we split it anyway to avoid throwing an error. This is us being helpful — we could have errored, but instead we broke it into smaller chunks even though they're not valid code anymore.

**Fix:** Set `strict=True` if you want it to error instead.

---

### Path not found 🔍

```
{path} is path-like but was not found. Skipping.
```

**What it means:** That file? Doesn't exist. We checked the filesystem and it's not there. Either you typo'd the path, the file was moved, or it's a symlink pointing to nowhere.

**Fix:** Check the path.

---

### Path doesn't look like a path 🧐

```
{path} does not resemble a valid file system path. Skipping.
```

**What it means:** You passed something that doesn't look like a file path. We use heuristics to guess, and this one failed the test. It's probably a URL, a glob pattern, or just a random string.

**Fix:** Double-check your input.

---

### No processable files 📭

```
No processable files found in the specified source(s). Exiting.
```

**What it means:** No files with supported extensions found in your input. We scanned the directories and came up empty. Either the directory is empty, contains only unsupported file types, or you pointed us at the wrong place.

**Fix:** Check your paths.

---

### No chunks generated 🫙

```
No chunks were generated. Input might be empty.
```

**What it means:** Nothing to chunk. The input is empty or we couldn't extract any text from it. This can happen with binary files, image-only PDFs, or literally empty files.

**Fix:** Check your input.

---

### Deprecation warning ⏳

```
{object} was deprecated since v{version}. Use {replacement} instead.
```

**What it means:** You're using old stuff. It works now, but we'll remove it in a future version so you should migrate eventually. We're not removing it yet, but we're telling you now so you're not surprised later.

**Fix:** Switch to the replacement when you get a chance.
