from typing import Annotated, Any, Union
from collections.abc import Iterable, Iterator, Generator
from itertools import tee
from more_itertools import ilen
from functools import wraps
from pydantic import validate_call, ConfigDict, PlainValidator, ValidationError
from chunklet.exceptions import InvalidInputError


def pretty_errors(error: ValidationError) -> str:
    """Formats Pydantic validation errors into a human-readable string."""
    lines = [
        f"{error.error_count()} validation error for {getattr(error, 'subtitle', '') or error.title}."
    ]
    for ind, err in enumerate(error.errors(), start=1):
        msg = err["msg"]

        loc = err.get("loc", [])
        formatted_loc = ""
        if len(loc) >= 1:
            formatted_loc = str(loc[0]) + "".join(f"[{step!r}]" for step in loc[1:])
            formatted_loc = f"({formatted_loc})" if formatted_loc else ""

        input_value = err["input"]
        input_type = type(input_value).__name__

        # Sliced to avoid overflowing screen
        input_value = (
            input_value
            if len(str(input_value)) < 500
            else str(input_value)[:500] + "..."
        )

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
            # Sliced to avoid overflowing screen
            input_val = v if len(v) < 500 else v[:500] + "..."
            raise ValueError(
                f"Input cannot be a string.\n  Found: (input={input_val!r}, type=str)"
            )
        return v

    ItemUnion = Union[hints] if len(hints) == 1 else hints[0]

    # Build the Full Container Type
    TargetType = (
        list[ItemUnion]
        | tuple[ItemUnion, ...]
        | set[ItemUnion]
        | frozenset[ItemUnion]
        | Generator[ItemUnion, None, None]
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


@validate_input
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

    Examples:
        >>> # With a list
        >>> my_list = [1, 2, 3, 4, 5]
        >>> count, preserved_list = safely_count_iterable("my_list", my_list)
        >>> print(f"Count: {count}")
        Count: 5
        >>> print(f"Original list is preserved: {list(preserved_list)}")
        Original list is preserved: [1, 2, 3, 4, 5]

        >>> # With an iterator (generator)
        >>> my_iterator = (x for x in range(10))
        >>> count, preserved_iterator = safely_count_iterable("my_iterator", my_iterator)
        >>> print(f"Count: {count}")
        Count: 10
        >>> # The iterator is preserved and can still be consumed
        >>> print(f"Sum of preserved iterator: {sum(preserved_iterator)}")
        Sum of preserved iterator: 45
    """
    try:  # If pydantic wrap it as ValidatorIterator object
        # Tee if it's an iterator
        if isinstance(iterable, Iterator):
            iterable, copy_iterable = tee(iterable)
            count = ilen(copy_iterable)
        else:
            count = len(iterable)
    except ValidationError as e:
        e.subtitle = name  # to be less generic
        e.hint = "💡 Hint: Ensure all elements in the iterable are valid."
        raise InvalidInputError(pretty_errors(e)) from None

    return count, iterable
