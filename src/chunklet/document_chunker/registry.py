import inspect
from typing import Callable, Iterable, Any
from pydantic import TypeAdapter, ValidationError
from chunklet.utils.validation import validate_input, pretty_errors
from chunklet.exceptions import CallbackError, InvalidInputError


# A tuple containing the extracted text(s) and a dictionary of metadata.
ReturnType = tuple[str | Iterable[str], dict[str, Any]]


class CustomProcessorRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CustomProcessorRegistry, cls).__new__(cls)
            cls._instance._processors: dict[str, tuple[str, Callable]] = {}
        return cls._instance

    @property
    def processors(self):
        """
        Returns a shallow copy of the dictionary of registered processors.

        This prevents external modification of the internal registry state.
        """
        return self._processors.copy()

    @validate_input
    def is_registered(self, ext: str) -> bool:
        """
        Check if a document processor is registered for the given file extension.
        """
        return ext in self._processors

    @validate_input
    def register(
        self, *exts: str, callback: Callable[[str], ReturnType], name: str | None = None
    ):
        """
        Register a document processor callback for one or more file extensions.

        Args:
            *exts: One or more file extensions (str), e.g., '.json', '.xml'.
            callback: A callable that takes a file path and returns a tuple of (text or text iterable, metadata dictionary).
            name (str, optional): The name of the processor. Defaults to the function name.

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
                "Expected exactly one required parameter to accept the file path.\n"
                "💡Hint: Optional parameters with default values are allowed."
            )

        processor_name = name or callback.__name__
        for ext in exts:
            if not isinstance(ext, str) or not ext.startswith("."):
                raise InvalidInputError(
                    f"Invalid file extension '{ext}'. Must be a string starting with '.'"
                )
            self._processors[ext] = (processor_name, callback)

    @validate_input
    def unregister(self, *exts: str) -> None:
        """
        Remove document processor(s) from the registry.

        Args:
            *exts: File extensions to remove.
        """
        for ext in exts:
            self._processors.pop(ext, None)

    def clear(self) -> None:
        """
        Clears all registered processors from the registry.
        """
        self._processors.clear()

    @validate_input
    def extract_data(self, file_path: str, ext: str) -> tuple[ReturnType, str]:
        """
        Processes a file using a processor registered for the given file extension.

        Args:
            file_path (str): The path to the file.
            ext (str): The file extension.

        Returns:
            tuple[ReturnType, str]: A tuple containing the extracted data and the name of the processor used.

        Raises:
            CallbackError: If the processor callback fails or returns the wrong type.
            InvalidInputError: If no processor is registered for the extension.
        """
        processor_info = self._processors.get(ext)
        if not processor_info:
            raise InvalidInputError(
                f"No document processor registered for file extension '{ext}'.\n"
                f"💡Hint: Use `register('{ext}', callback=your_function)` first."
            )

        name, callback = processor_info

        try:
            # Validate the return type
            result = callback(file_path)
            validator = TypeAdapter(ReturnType)
            validator.validate_python(result)
        except ValidationError as e:
            e.subtitle = f"{name} result"
            e.hint = (
                "💡Hint: Make sure your processor returns a tuple of (text/texts, metadata_dict)."
                " An empty dict can be provided if there's no metadata."
            )

            raise CallbackError(f"{pretty_errors(e)}.\n") from None
        except Exception as e:
            raise CallbackError(
                f"Processor '{name}' for extension '{ext}' raised an exception.\nDetails: {e}"
            ) from None

        return result, name


def registered_processor(*exts: str, name: str | None = None):
    """
    Decorator version of document processor registration.

    Usage:
        @registered_processor(".json", ".xml")
        def my_json_processor(file_path):
            # ... logic to extract text from JSON
            return text_content
    """
    registry = CustomProcessorRegistry()

    def decorator(callback: Callable):
        registry.register(*exts, callback=callback, name=name)
        return callback

    return decorator
