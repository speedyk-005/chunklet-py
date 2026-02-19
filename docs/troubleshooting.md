# Troubleshooting: Your Chunklet-py Adventure Guide 🛠️

Welcome to the troubleshooting guide! Here you'll find solutions to common issues you might encounter while using `chunklet-py`. Think of this as your friendly roadmap when things don't go quite as planned.

## Batch Processing Hangs or Fails on Exit

??? question "Why does `batch_chunk` hang, and then show a `TypeError` when I try to exit with `Ctrl+C`?"

    This happens when you use `batch_chunk` but don't fully iterate through all the results. For example, using a `break` statement to stop early.

    The `batch_chunk` method uses a multiprocessing pool in the background. If you exit the loop early, the generator gets abandoned without proper cleanup. Those background processes can get stuck in limbo, and when you hit `Ctrl+C`, Python tries to clean up but fails with a `TypeError: 'NoneType' object is not callable`.

    **Solution:**

    The fix is to make sure the generator always gets fully consumed or explicitly closed. Think of it as making sure you finish your meal before leaving the table!

    **Option 1: Explicitly Close the Generator (Recommended)**

    The most reliable approach is to wrap your loop in a `try...finally` block and call the `close()` method on the generator. This ensures proper cleanup even if you bail out early with a break.

    Here is an example:

    ```py
    from chunklet import DocumentChunker

    paths = ["path/to/your/doc1.pdf", "path/to/your/doc2.txt"]
    chunker = DocumentChunker()
    chunks_generator = chunker.chunk_files(paths)

    try:
        for i, chunk in enumerate(chunks_generator):
            if i >= 10:  # Example: Stop after 10 chunks
                break
            print(chunk.content)
    finally:
        chunks_generator.close()
    ```

        By explicitly closing the generator, you ensure all background processes get properly cleaned up, preventing the hang and letting your program exit gracefully.

    **Option 2: Convert to a List**

    If you don't need chunks as they're generated and prefer having everything ready at once, you can convert the generator to a list. This forces full consumption and ensures the multiprocessing pool shuts down properly.

    ```py
    from chunklet import DocumentChunker

    paths = ["path/to/your/doc1.pdf", "path/to/your/doc2.txt"]
    chunker = DocumentChunker()
    all_chunks = list(chunker.chunk_files(paths))

    for i, chunk in enumerate(all_chunks):
        if i >= 10:  # Example: You can still break, but the pool is already closed
            break
        print(chunk.content)
    ```

        This approach is simpler if memory isn't a concern and you need all chunks ready before moving on.

    **Related Reading:**
    
    *   [mpire Issue #141: Fork-mode processes hanging](https://github.com/sybrenjansen/mpire/issues/141)
    *   [Why your multiprocessing Pool is stuck](https://pythonspeed.com/articles/python-multiprocessing/)

## Visualizer Browser Cache Issues

??? question "Why does the visualizer show old/static/incorrect behavior after an update?"

    After updating `chunklet-py`, your browser may be serving cached CSS, JavaScript, or HTML files from the visualizer, causing it to display outdated or broken behavior.

    **Solution:**

    **Option 1: Hard Refresh (Recommended)**

    - **Windows/Linux:** Press `Ctrl + Shift + R` or `Ctrl + F5`
    - **macOS:** Press `Cmd + Shift + R` or `Cmd + F5`

    **Option 2: Clear Browser Cache**

    1. Open Developer Tools (`F12` or `Cmd/Ctrl + Shift + I`)
    2. Go to the **Network** tab
    3. Check the **Disable cache** checkbox
    4. Press `Cmd/Ctrl + R` to reload

    **Option 3: Clear Site Data**

    1. Open Developer Tools (`F12` or `Cmd/Ctrl + Shift + I`)
    2. Go to the **Application** tab (Chrome) or **Storage** tab (Firefox)
    3. Click **Clear site data** or expand the section and delete all items
    4. Reload the page

    **Option 4: Incognito/Private Mode**

    Open the visualizer in a new incognito/private window - this bypasses the cache entirely.

    **Related Reading:**

    * [Cache Issues](https://help.blocsapp.com/knowledge-base/cache-issues/)
    * [Learn how to Clear Browser Cache](https://medium.com/@reennamatovu/how-i-finally-learned-to-clear-my-browser-cache-without-panic-or-losing-everything-17368d88d0ea)
