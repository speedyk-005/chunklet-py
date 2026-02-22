# Troubleshooting 🛠️

Things break. Here's how to fix them.

## Batch Processing Hangs on Exit

??? question "Why does `batch_chunk` hang, then throw a `TypeError` when I Ctrl+C?"

    You broke out of the loop early with a `break`, or didn't finish iterating through all chunks. 
    
    Batch methods use multiprocessing. When you bail out early, the background processes don't get cleaned up properly. Hit Ctrl+C and Python has a breakdown.

    **Fix:**

    **Option 1: Close the generator**

    ```py
    from chunklet import DocumentChunker

    paths = ["doc1.pdf", "doc2.txt"]
    chunker = DocumentChunker()
    chunks = chunker.chunk_files(paths)

    try:
        for chunk in chunks:
            if some_condition:
                break
            print(chunk.content)
    finally:
        chunks.close()
    ```

    **Option 2: Convert to list**

    ```py
    all_chunks = list(chunker.chunk_files(paths))
    # pool is closed once list is built
    ```

    Simple tradeoff: memory vs peace of mind.

## Visualizer Showing Old/Cached Stuff

??? question "Why does the visualizer look broken after I updated?"

    Browser cache. The classic "it worked yesterday" problem.
    
    **Fix:**

    - Hard refresh: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
    - Or just open incognito — caches don't follow you there

## Something Broke or Warned

??? question "Something threw an exception. Now what?"

    First: actually read the error message. We know, we know — "just read the error" sounds obvious, but sometimes it actually tells you what's wrong.
    
    If it's a warning, you're probably fine — just a heads up. If it's an exception, something actually broke.
    
    **What to do:**
    
    1. **Read the message** — it usually tells you what's up
    2. **Check [exceptions-and-warnings.md](./exceptions-and-warnings.md)** — we explain what each one means
    3. **Check [What's New](./whats-new.md)** — breaking changes and new stuff live there
    4. **Open an issue** — if it's genuinely broken and not covered, let us know. But check first.
