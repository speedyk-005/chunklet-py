import pickle
from functools import partial

from chunklet.common.batch_runner import capture_result_and_exception
from chunklet.document_chunker import DocumentChunker


def test_result_and_exception_wrapper_is_picklable():
    chunker = DocumentChunker(lang="en", max_sentences=1)
    chunk_func = partial(
        chunker.plain_text_chunker.chunk,
        base_metadata=None,
        token_counter=None,
    )

    worker = capture_result_and_exception(chunk_func)
    restored_worker = pickle.loads(pickle.dumps(worker))

    result, error = restored_worker("First sentence. Second sentence.")

    assert error is None
    assert result
    assert result[0].content
