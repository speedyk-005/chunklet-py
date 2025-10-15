from __future__ import annotations
import inspect
from typing import Callable
from pydantic import TypeAdapter, ValidationError
from chunklet.utils.validation import validate_input, pretty_errors
from chunklet.exceptions import CallbackExecutionError

# --- Splitter registry ---
_splitters: dict[str, tuple[str, Callable]] = {}


@validate_input
def is_registered(lang: str) -> bool:
    """
    Check if a splitter is registered for the given language.

    Args:
        lang (str): The language code.

    Returns:
        bool: True if a splitter is registered, False otherwise.
    """
    return lang in _splitters


@validate_input
def register_splitter(*langs: tuple[str], callback: Callable, name: str | None = None):
    """
    Register a splitter callback for one or more languages.

    Args:
        *langs: One or more language codes (str)
        callback: Callable that takes exactly one argument (the text to split)
            (or two if it is a bound method with 'self')
        name (str, optional): The name of the splitter. Defaults to the function name.

    Raises:
        TypeError: If callback is not callable or has the wrong number of parameters.
    """
    if not callable(callback):
        raise TypeError(
            f"{type(callback).__name__} is not callable.\n"
            f"💡Hint: Pass a function or a bound method accepting one argument (the text)."
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
            f"💡Hint: Define the function like `def splitter(text): ...`"
        )

    splitter_name = name or callback.__name__
    for lang in langs:
        _splitters[lang] = (splitter_name, callback)


@validate_input
def unregister_splitter(*langs: tuple[str]):
    """
    Remove splitter(s) from the registry.

    Args:
        *langs: Language codes to remove
    """
    for lang in langs:
        _splitters.pop(lang, None)


def registered_splitter(*langs: tuple[str], name: str | None = None):
    """
    Decorator version of splitter registration.

    Usage:
        @registered_splitter("en", "fr")
        def my_splitter(text):
            ...
    """

    def decorator(callback: Callable):
        register_splitter(*langs, callback=callback, name=name)
        return callback

    return decorator


@validate_input
def use_registered_splitter(text: str, lang: str) -> tuple[list[str], str]:
    """
    Processes a text using a splitter registered for the given language.

    Args:
        text (str): The text to split.
        lang (str): The language of the text.

    Returns:
        tuple[list[str], str]: A tuple containing a list of sentences and the name of the splitter used.

    Raises:
        CallbackExecutionError: If the splitter callback fails.
        TypeError: If the splitter returns the wrong type.
    """
    splitter_info = _splitters.get(lang)
    if not splitter_info:
        raise CallbackExecutionError(
            f"No splitter registered for language '{lang}'.\n"
            f"💡Hint: Use `register_splitter('{lang}', fn=your_function)` first."
        )

    name, callback = splitter_info

    try:
        # Validate the return type
        result = callback(text)
        validator = TypeAdapter(list[str])
        validator.validate_python(result)
    except ValidationError as e:
        raise CallbackExecutionError(
            f"Splitter '{name}' returns an invalid type: {pretty_errors(e)}.\n"
            f"💡Hint: Make sure your splitter returns a list of strings."
        ) from None
    except Exception as e:
        raise CallbackExecutionError(
            f"Splitter '{name}' raised an exception.\n"
            f"💡Hint: Review the logic inside this function.\n"
            f"Details: {e}"
        ) from None

    return result, name
