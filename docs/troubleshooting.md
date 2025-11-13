# Troubleshooting

Welcome to the troubleshooting guide! Here you'll find solutions to common issues you might encounter while using `chunklet-py`.

## Batch Processing Errors

??? question "Why do I get a `TypeError: 'NoneType' object is not callable` when using `batch_chunk`?"

    This error can occur if you are using `batch_chunk` (or `batch_chunk` from `DocumentChunker`) and you don't fully consume the returned generator. This often happens if you use a `break` statement in your loop.

    The `batch_chunk` methods use multiprocessing in the background to process the data in parallel. When the generator is not fully consumed, the multiprocessing pool might not be terminated correctly, leading to this error.

    **Solution:**

    To fix this, you should ensure that the generator is always closed, even if you break out of the loop early. You can do this by wrapping your loop in a `try...finally` block and calling the `close()` method on the generator in the `finally` block.

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

    By explicitly closing the generator, you ensure that all background processes are properly cleaned up, avoiding the `TypeError`.

    **Further Reading:**
    *   [Python CPython Issue #91776: multiprocessing.pool.Pool.close() can cause TypeError in finalizer](https://github.com/python/cpython/issues/91776)

