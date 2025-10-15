from typing_extensions import TypedDict
from typing import get_type_hints, Type, Annotated
from collections.abc import Iterator
from itertools import tee
import inspect
from functools import wraps
from pydantic import TypeAdapter, ConfigDict, ValidationError, FailFast
from chunklet.exceptions import InvalidInputError


def pretty_errors(e: ValidationError) -> str:
    """Formats Pydantic validation errors into a human-readable string."""
    lines = []
    for err in e.errors():
        field_path = " -> ".join(str(loc) for loc in err.get("loc", []))
        msg = err.get("msg", "")
        input_value = err.get("input", "<unknown>")
        input_type = type(input_value).__name__ if input_value is not None else "None"
        lines.append(f"[{field_path}] {msg} (input={input_value!r}, type={input_type})")
    return "\n".join(lines)


def typedict_from_annotations(fn) -> Type[TypedDict]:
    """
    Creates a Pydantic-configured TypedDict from a function's annotations.
    """

    def apply_failfast(hint):
        origin = getattr(hint, "__origin__", None)
        if origin in (list, tuple, set):
            return Annotated[hint, FailFast()]
        return hint

    hints = get_type_hints(fn, include_extras=True)
    hints.pop("return", None)

    name = fn.__name__.capitalize() + "Args"
    TypedDict_class = TypedDict(name, hints)

    # Set config to allow arbitrary types.
    TypedDict_class.model_config = ConfigDict(arbitrary_types_allowed=True, strict=True)

    return TypedDict_class


def validate_input(fn):
    """
    Decorator that validates function inputs using a Pydantic TypeAdapter.
    """
    ArgsDict = typedict_from_annotations(fn)
    adapter = TypeAdapter(ArgsDict)

    sig = inspect.signature(fn)
    first_param = next(iter(sig.parameters.values()), None)
    is_method = first_param and first_param.name in {"self", "cls"}

    @wraps(fn)
    def wrapper(*args, **kwargs):

        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        arguments = bound.arguments

        if is_method:
            arguments.pop(first_param.name, None)

        # Use tee to create two independent iterators to prevent exhaustion on validation.
        iterator_args = {}
        for key, value in arguments.items():
            if isinstance(value, Iterator):
                arguments[key], iterator_args[key] = tee(value)

        try:
            adapter.validate_python(arguments)
            arguments.update(iterator_args)
        except ValidationError as e:
            raise InvalidInputError(pretty_errors(e)) from e
        # Call the function with the original args and kwrags
        # This way we can easily manually validate iterables to less generic versions.
        return fn(*args, **kwargs)

    return wrapper
