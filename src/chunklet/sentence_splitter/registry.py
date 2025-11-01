import inspect
from typing import Callable
from pydantic import TypeAdapter, ValidationError
from chunklet.utils.validation import validate_input, pretty_errors
from chunklet.exceptions import CallbackError


class CustomSplitterRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CustomSplitterRegistry, cls).__new__(cls)
            cls._instance._splitters: dict[str, tuple[str, Callable]] = {}
        return cls._instance

    @property
    def splitters(self):
        """
        Returns a shallow copy of the dictionary of registered splitters.

        This prevents external modification of the internal registry state.
        """
        return self._splitters.copy()

    @validate_input
    def is_registered(self, lang: str) -> bool:
        """
        Check if a splitter is registered for the given language.
        """
        return lang in self._splitters

    @validate_input
    def register(
        self, *langs: str, callback: Callable[str, list[str]], name: str | None = None
    ):
        """
        Register a splitter callback for one or more languages.

        Args:
            *langs: One or more language codes (str)
            callback: Callable that takes exactly one argument (the text to split)
            name (str, optional): The name of the splitter. Defaults to the function name.

        Raises:
            InvalidInputError: If the provided arguments are not valid.
        """
        sig = inspect.signature(callback)
        params = list(sig.parameters.values())

        # Exclude 'self' if it's a method
        if params and params[0].name == "self":
            params = params[1:]

        # Filter for required parameters (those without a default value)
        required_params = [p for p in params if p.default is inspect.Parameter.empty]

        if len(required_params) != 1:
            param_list = ", ".join(p.name for p in params)
            raise TypeError(
                f"'{callback.__name__}' has signature ({param_list}).\n"
                "Expected exactly one required parameter to accept the text.\n"
                "💡Hint: Optional parameters with default values are allowed."
            )

        splitter_name = name or callback.__name__
        for lang in langs:
            self._splitters[lang] = (splitter_name, callback)

    @validate_input
    def unregister(self, *langs: str) -> None:
        """
        Remove splitter(s) from the registry.

        Args:
            *langs: Language codes to remove
        """
        for lang in langs:
            self._splitters.pop(lang, None)

    def clear(self) -> None:
        """
        Clears all registered splitters from the registry.
        """
        self._splitters.clear()

    @validate_input
    def split(self, text: str, lang: str) -> tuple[list[str], str]:
        """
        Processes a text using a splitter registered for the given language.

        Args:
            text (str): The text to split.
            lang (str): The language of the text.

        Returns:
            tuple[list[str], str]: A tuple containing a list of sentences and the name of the splitter used.

        Raises:
            CallbackError: If the splitter callback fails.
            TypeError: If the splitter returns the wrong type.
        """
        splitter_info = self._splitters.get(lang)
        if not splitter_info:
            raise CallbackError(
                f"No splitter registered for language '{lang}'.\n"
                f"💡Hint: Use `.register('{lang}', fn=your_function)` first."
            )

        name, callback = splitter_info

        try:
            # Validate the return type
            result = callback(text)
            validator = TypeAdapter(list[str])
            validator.validate_python(result)
        except ValidationError as e:
            e.subtitle = f"{name} result"
            e.hint = "💡Hint: Make sure your splitter returns a list of strings."
            raise CallbackError(f"{pretty_errors(e)}.\n") from None
        except Exception as e:
            raise CallbackError(
                f"Splitter '{name}' for lang '{lang}' raised an exception.\nDetails: {e}"
            ) from None

        return result, name


def registered_splitter(*langs: str, name: str | None = None):
    """
    Decorator version of splitter registration.

    Usage:
        @registered_splitter("en", "fr")
        def my_splitter(text):
            ...
    """
    registry = CustomSplitterRegistry()

    def decorator(callback: Callable):
        registry.register(*langs, callback=callback, name=name)
        return callback

    return decorator
