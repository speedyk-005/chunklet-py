import inspect
from typing import Callable
from pydantic import TypeAdapter, ValidationError
from chunklet.utils.validation import validate_input, pretty_errors
from chunklet.exceptions import CallbackExecutionError, InvalidInputError


class CustomSplitterRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CustomSplitterRegistry, cls).__new__(cls)
            cls._instance._splitters: Dict[str, Tuple[str, Callable]] = {}
        return cls._instance

    @property
    def splitters(self):
        return self._splitters
        
    @validate_input
    def is_registered(self, lang: str) -> bool:
        """
        Check if a splitter is registered for the given language.
        """
        return lang in self._splitters


    @validate_input
    def register(
        self,
        *langs: str,
        callback: Callable[str, list[str]],
        name: str | None = None
    ):
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
        # Validate it accepts exactly one argument (or two if first is 'self')
        sig = inspect.signature(callback)
        params = list(sig.parameters.values())
        if params and params[0].name == "self":
            params = params[1:]
        if len(params) != 1:
            param_list = ", ".join(p.name for p in params)
            raise InvalidInputError(
                f"1 validation error(s) for {callback.__name__!r}\n"
                "1) Input signature mismatched ({param_list}).\n"
                f"  Expected exactly one parameter (excluding 'self').\n"
                f"  💡Hint: Define the function like `def splitter(text): ...`"
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

    @validate_input
    def split(
        self,
        text: str,
        lang: str
    ) -> tuple[list[str], str]:
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
        splitter_info = self._splitters.get(lang)
        if not splitter_info:
            raise CallbackExecutionError(
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
            e.hint = f"💡Hint: Make sure your splitter returns a list of strings."
            raise CallbackExecutionError(f"{pretty_errors(e)}.\n") from None
        except Exception as e:
            raise CallbackExecutionError(
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
        registry.register(
            *langs, callback=callback, name=name
        )
        return callback

    return decorator
