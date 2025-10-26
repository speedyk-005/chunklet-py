from typing import Annotated, Any, Union
from collections.abc import Iterable, Iterator, Generator
from itertools import tee
from functools import wraps
from pydantic import validate_call, ConfigDict, PlainValidator, ValidationError
from chunklet.exceptions import InvalidInputError


def pretty_errors(error: ValidationError) -> str:
    """Formats Pydantic validation errors into a human-readable string."""
    lines = [f"{error.error_count()} validation error for {getattr(error, 'subtitle', '') or error.title}."]
    for ind, err in enumerate(error.errors(), start=1):
        msg = err["msg"]
        
        loc = err.get("loc", [])
        formatted_loc = ""
        if len(loc) >= 1:
            formatted_loc = str(loc[0]) + "".join(f"[{l!r}]" for l in loc[1:])
            formatted_loc = f"({formatted_loc})" if formatted_loc else ""

        input_value = err["input"]
        input_type = type(input_value).__name__
        lines.append(
            f"{ind}) {formatted_loc} {msg}.\n"
            f"  Found: (input={input_value!r}, type={input_type})"
        )

    lines.append("  " + getattr(error, "hint", ""))
    return "\n".join(lines)


def restricted_iterable(*hints: Any) -> Any:
    """
    Creates a Pydantic Annotated type that represents a RestrictedIterable 
    containing the specified hints (*hints), and applies a PlainValidator 
    to reject str input.
    """
    def enforce_non_string(v: Any) -> Any:
        if isinstance(v, str):
            # Pydantic-Core is sometimes pickier; using ValueError often works better
            # with external validators than a raw TypeError
            raise ValueError(
                f"Input cannot be a string.\n  Found: (input={v!r}, type=str)"
            )
        return v
    
    ItemUnion = Union[hints] if len(hints) == 1 else hints[0]
    
    # Build the Full Container Type
    TargetType = (
        list[ItemUnion] | 
        tuple[ItemUnion, ...] |
        set[ItemUnion] | 
        frozenset[ItemUnion] | 
        Generator[ItemUnion, None, None]
    )

    # Create the Annotated Type
    return Annotated[TargetType, PlainValidator(enforce_non_string)]


def validate_input(fn):
    """
    A decorator that validates function inputs and outputs
    
    A wrapper around Pydantic's `validate_call` that catches`ValidationError` and re-raises it as a more user-friendly `InvalidInputError`.
    """
    validated_fn = validate_call(fn, config=ConfigDict(arbitrary_types_allowed=True))

    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return validated_fn(*args, **kwargs)
        except ValidationError as e:
            raise InvalidInputError(pretty_errors(e)) from None
    return wrapper


def safely_count_iterable(name: str, iterable: Iterable) -> tuple[int, Iterable]:
    """
    Counts elements in an iterable while preserving its state and forcing validation.

    If the input is an Iterator, it is duplicated using `itertools.tee` to prevent
    consumption during counting. The iteration simultaneously triggers any 
    underlying Pydantic item validation.

    Args:
        name (str): Descriptive name for the iterable (used in error context).
        iterable (Iterable): The iterable or iterator to count and validate.

    Returns:
        tuple[int, Iterable]: The element count and the original (or preserved) 

    Raises:
        InvalidInputError: If any element fails validation during the counting process.
    """
     # Tee if it's an iterator
    if isinstance(iterable, Iterator):
        iterable, copy_iterable = tee(iterable)
    else:
        copy_iterable = iterable

    try:  # If pydantic wrap it as ValidatorIterator object
        count = sum(1 for _ in copy_iterable)
    except ValidationError as e:
        e.subtitle = name   # to be less generic
        e.hint = "💡 Hint: Ensure all elements in the iterable are valid."
        raise InvalidInputError(pretty_errors(e)) from None

    return count, iterable
