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
    chunks_generator = chunker.batch_chunk(paths)

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
    all_chunks = list(chunker.batch_chunk(paths))

    for i, chunk in enumerate(all_chunks):
        if i >= 10:  # Example: You can still break, but the pool is already closed
            break
        print(chunk.content)
    ```

        This approach is simpler if memory isn't a concern and you need all chunks ready before moving on.

    **Related Reading:**
    *   [mpire Issue #141: Fork-mode processes hanging](https://github.com/sybrenjansen/mpire/issues/141)
    *   [Why your multiprocessing Pool is stuck](https://pythonspeed.com/articles/python-multiprocessing/)
    