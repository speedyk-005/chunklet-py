# Contributing to Chunklet

Hey! Thanks for thinking about contributing. Bug fixes, features, docs — all welcome.

## Getting Started

1. **Clone the repository:**

    ```bash
    git clone https://github.com/speedyk-005/chunklet-py.git
    cd chunklet-py
    ```

2. **Install dependencies:**

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -e ".[dev]"      # basic dev: pytest, ruff
    pip install -e ".[dev-all]" # all optional features
    ```

## Making Changes

1. **Create a new branch:** Use descriptive names like `feature/my-feature-branch` or `bugfix/issue-number-description`

    ```bash
    git checkout -b feature/my-feature-branch
    ```

2. **Write your code:** Follow the style guide below.

3. **Test:** Run `pytest` and make sure everything passes.

    ```bash
    pytest
    ```

4. **Format and lint:** Run `ruff format && ruff check --fix` before committing.

5. **Build documentation (if you've made docs changes):** This project uses MkDocs for documentation. Test your changes by building the docs.

    ```bash
    pip install -e ".[docs]"
    ./build_docs.sh
    ```

## Pull Request Template

### Summary

Brief description of what this PR accomplishes.

### Changes

- Specific changes made
- Problems solved
- Impact on existing functionality

### Testing

- Tests added or modified
- Manual testing performed

### Related Issues

- Fixes #issue-number
  
## Coding Style Guidelines

### Method Ordering

Order methods like this:

1. Class docstring
2. Constants/attributes
3. `__init__`
4. Properties (`@property`)
5. Private methods (`_method`)
6. Public methods (`method`)

```python
class ExampleClass:
    """Class docstring."""

    CONSTANT = "value"

    def __init__(self):
        pass

    @property
    def some_property(self):
        return self._value

    def _helper_method(self):
        pass

    def public_method(self):
        pass
```

### Docstrings

Use [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for public methods and classes. Private methods can skip docstrings unless they're tricky.

### Code Quality

Run Ruff before committing:

```bash
ruff format
ruff check --fix
```

## Submitting a Pull Request

Not sure about something? Open an issue first — happy to chat before you dive in.

- Descriptive title
- Summary of changes and why
- Link related issues ("Fixes #123")
- Ensure tests pass

## Code of Conduct

We're all adults here trying to build cool software together. Be nice, don't be a jerk, respect different opinions, and remember that behind every GitHub profile is a human being who probably has better things to do than deal with your nonsense. If you can't contribute without making the experience miserable for others, maybe try contributing to a different project instead. We're here to code, not to psychoanalyze each other's life choices. Keep it professional, keep it civil, and we'll all get along just fine.
