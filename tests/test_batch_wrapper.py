import pickle

from chunklet.common.batch_runner import capture_result_and_exception


def test_capture_result_and_exception_is_pickleable():
    """The result/exception wrapper must survive multiprocessing serialization."""
    wrapped_success = capture_result_and_exception(len)
    wrapped_failure = capture_result_and_exception(int)

    restored_success = pickle.loads(pickle.dumps(wrapped_success))
    restored_failure = pickle.loads(pickle.dumps(wrapped_failure))

    result, error = restored_success([1, 2, 3])
    assert result == 3
    assert error is None

    result, error = restored_failure("not an integer")
    assert result is None
    assert isinstance(error, ValueError)
