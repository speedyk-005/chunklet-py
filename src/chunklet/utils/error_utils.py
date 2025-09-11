from pydantic import ValidationError


def pretty_errors(e: ValidationError) -> str:
    """Makes pydantic validation error more readable"""
    lines = []
    for err in e.errors():
        field = " ->  ".join(str(loc) for loc in err["loc"])
        msg = err["msg"]
        lines.append(f"[{field}] {msg}")
    return "\n".join(lines)
