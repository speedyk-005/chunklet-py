from __future__ import annotations
import inspect
from typing import Callable
from pydantic import TypeAdapter, ValidationError
from chunklet.utils.validation import validate_input, pretty_errors
from chunklet.exceptions import CallbackExecutionError, InvalidInputError

# --- Document Processor registry ---
_processors: dict[str, tuple[str, Callable]] = {}


@validate_input
def is_registered(ext: str) -> bool:
    """
    Check if a document processor is registered for the given file extension.

    Args:
        ext (str): The file extension (e.g., '.json').

    Returns:
        bool: True if a processor is registered, False otherwise.
    """
    return ext in _processors


@validate_input
def register_processor(
    *exts: tuple[str], callback: Callable[[str], str], name: str | None = None
):
    """
    Register a document processor callback for one or more file extensions.

    Args:
        *exts: One or more file extensions (str), e.g., '.json', '.xml'.
        callback: Callable that takes the file path (str) and returns its content (str).
        name (str, optional): The name of the processor. Defaults to the function name.

    Raises:
        TypeError: If callback is not callable or has the wrong number of parameters.
        InvalidInputError: If an extension is not valid (e.g., missing leading dot).
    """
    if not callable(callback):
        raise TypeError(
            f"{type(callback).__name__} is not callable.\n"
            f"💡Hint: Pass a function or a bound method accepting one argument (the file path)."
        )

    # Validate it accepts exactly one argument (or two if first is 'self')
    sig = inspect.signature(callback)
    params = list(sig.parameters.values())
    if params and params[0].name == "self":
        params = params[1:]
    if len(params) != 1:
        param_list = ", ".join(p.name for p in params)
        raise TypeError(
            f"'{callback.__name__}' has signature ({param_list}).\n"
            f"Expected exactly one parameter (excluding 'self').\n"
            f"💡Hint: Define the function like `def processor(file_path): ...`"
        )

    processor_name = name or callback.__name__
    for ext in exts:
        if not isinstance(ext, str) or not ext.startswith("."):
            raise InvalidInputError(
                f"Invalid file extension '{ext}'. Must be a string starting with '.'"
            )
        _processors[ext] = (processor_name, callback)


@validate_input
def unregister_processor(*exts: tuple[str]):
    """
    Remove document processor(s) from the registry.

    Args:
        *exts: File extensions to remove.
    """
    for ext in exts:
        _processors.pop(ext, None)


def registered_processor(*exts: tuple[str], name: str | None = None):
    """
    Decorator version of document processor registration.

    Usage:
        @registered_processor(".json", ".xml")
        def my_json_processor(file_path):
            # ... logic to extract text from JSON
            return text_content
    """

    def decorator(callback: Callable):
        register_processor(*exts, callback=callback, name=name)
        return callback

    return decorator


@validate_input
def use_registered_processor(file_path: str, ext: str) -> tuple[str, str]:
    """
    Processes a file using a processor registered for the given file extension.

    Args:
        file_path (str): The path to the file.
        ext (str): The file extension.

    Returns:
        tuple[str, str]: A tuple containing the extracted text content and the name of the processor used.

    Raises:
        CallbackExecutionError: If the processor callback fails or returns the wrong type.
        InvalidInputError: If no processor is registered for the extension.
    """
    processor_info = _processors.get(ext)
    if not processor_info:
        raise InvalidInputError(
            f"No document processor registered for file extension '{ext}'.\n"
            f"💡Hint: Use `register_processor('{ext}', callback=your_function)` first."
        )

    name, callback = processor_info

    try:
        result = callback(file_path)
        validator = TypeAdapter(str)  # Expecting string content
        validator.validate_python(result)
    except ValidationError as e:
        raise CallbackExecutionError(
            f"Document processor '{name}' for extension '{ext}' returned an invalid type: {pretty_errors(e)}.\n"
            f"💡Hint: Make sure your processor returns a string."
        ) from None
    except Exception as e:
        raise CallbackExecutionError(
            f"Document processor '{name}' for extension '{ext}' raised an exception.\n"
            f"💡Hint: Review the logic inside this function.\n"
            f"Details: {e}"
        ) from None

    return result, name
