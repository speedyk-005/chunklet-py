import inspect
from typing import Callable, Iterable, Any
from pydantic import TypeAdapter, ValidationError
from chunklet.common.validation import validate_input, pretty_errors
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

    def register(self, *args: Any, name: str | None = None):
        """
        Register a document processor callback for one or more file extensions.

        This method can be used in two ways:
        1. As a decorator:
            @registry.register(".json", ".xml", name="my_processor")
            def my_processor(file_path):
                ...

        2. As a direct function call:
            registry.register(my_processor, ".json", ".xml", name="my_processor")

        Args:
            *args: The arguments, which can be either (ext1, ext2, ...) for a decorator
                   or (callback, ext1, ext2, ...) for a direct call.
            name (str | None): The name of the processor. If None, attempts to use the callback's name.
        """
        if not args:
            raise ValueError(
                "At least one file extension or a callback must be provided."
            )

        if callable(args[0]):
            # Direct call: register(callback, ext1, ext2, ...)
            callback = args[0]
            exts = args[1:]
            if not exts:
                raise ValueError(
                    "At least one file extension must be provided for the callback."
                )
            self._register_logic(exts, callback, name)
            return callback
        else:
            # Decorator: @register(ext1, ext2, ...)
            exts = args

            def decorator(cb: Callable):
                self._register_logic(exts, cb, name)
                return cb

            return decorator

    @validate_input
    def _register_logic(
        self,
        exts: tuple[str, ...],
        callback: Callable[[str], ReturnType],
        name: str | None = None,
    ):
        """Helper to perform the actual registration and validation."""
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

        if name is None:
            if hasattr(callback, "__name__") and callback.__name__ != "<lambda>":
                processor_name = callback.__name__
            else:
                raise ValueError(
                    "A name must be provided for the processor, or the callback must be a named function (not a lambda)."
                )
        else:
            processor_name = name

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

        Examples:
            >>> from chunklet.document_chunker.registry import CustomProcessorRegistry
            >>> registry = CustomProcessorRegistry()
            >>> @registry.register(".txt", name="my_txt_processor")
            ... def process_txt(file_path: str) -> tuple[str, dict]:
            ...     with open(file_path, 'r') as f:
            ...         content = f.read()
            ...     return content, {"source": file_path}
            >>> # Assuming 'sample.txt' exists with some content
            >>> # result, processor_name = registry.extract_data("sample.txt", ".txt")
            >>> # print(f"Extracted by {processor_name}: {result[0][:20]}...")
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
