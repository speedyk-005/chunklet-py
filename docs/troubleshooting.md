# Troubleshooting

Welcome to the troubleshooting guide! Here you'll find solutions to common issues you might encounter while using `chunklet-py`.

## Batch Processing Hangs or Fails on Exit

??? question "Why does `batch_chunk` hang, and then show a `TypeError` when I try to exit with `Ctrl+C`?"

    This can happen if you are using `batch_chunk` but do not fully iterate through all the results it yields. For example, if you use a `break` statement in your loop to stop early.

    The `batch_chunk` method uses a multiprocessing pool in the background. If you exit the loop early, the generator is abandoned without being properly closed. The background processes in the pool can be left in a hanging state. When you then try to exit your script with `Ctrl+C`, the Python interpreter tries to clean up, which can lead to a `TypeError: 'NoneType' object is not callable` as it fails to shut down the orphaned processes correctly.

    **Solution:**

    To fix this, you must ensure that the generator is always fully consumed or explicitly closed.

    **Option 1: Explicitly Close the Generator (Recommended)**

    The most robust way is to wrap your loop in a `try...finally` block and call the `close()` method on the generator in the `finally` block. This ensures proper cleanup even if you break out of the loop early.

    Here is an example:

    ```python
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

        By explicitly closing the generator, you ensure that all background processes are properly cleaned up, preventing the hang and allowing your program to exit cleanly.

    **Option 2: Convert to a List**

    If you don't need to process chunks as they are generated and prefer to have all chunks available at once, you can convert the generator to a list. This forces the generator to be fully consumed, ensuring the multiprocessing pool is properly terminated.

    ```python
    from chunklet import DocumentChunker

    paths = ["path/to/your/doc1.pdf", "path/to/your/doc2.txt"]
    chunker = DocumentChunker()
    all_chunks = list(chunker.batch_chunk(paths))

    for i, chunk in enumerate(all_chunks):
        if i >= 10:  # Example: You can still break, but the pool is already closed
            break
        print(chunk.content)
    ```

        This approach is simpler if memory is not a concern and you need all chunks before proceeding.

    **Related Issues:**
    *   [mpire Issue #141: Fork-mode processes hanging](https://github.com/sybrenjansen/mpire/issues/141)
    *   [Why your multiprocessing Pool is stuck](https://pythonspeed.com/articles/python-multiprocessing/)
    