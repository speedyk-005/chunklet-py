# Contributing to Chunklet

Hey there! Thanks for thinking about contributing to Chunklet. We really appreciate any help you can give, whether it's fixing a bug, adding a new feature, or improving documentation. Every bit helps make this project better for everyone.

## Getting Started

1. **Clone the repository:**

    ```bash
    git clone https://github.com/speedyk-005/chunklet-py.git
    cd chunklet-py
    ```

2. **Install dependencies:** We recommend using a virtual environment.

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    # For basic development (testing, linting)
    pip install -e ".[dev]"
    # For comprehensive development (including all optional features)
    pip install -e ".[dev-all]"
    ```

    These commands install the package in development mode with all development dependencies (pytest, black, flake8, etc.).

## Making Changes

1. **Create a new branch:** Use descriptive names like `feature/my-feature-branch` or `bugfix/issue-number-description`

    ```bash
    git checkout -b feature/my-feature-branch
    ```

2. **Write your code:** Make your changes and ensure they follow the project's coding style.

3. **Run tests:** Make sure all tests pass before submitting a pull request.

    ```bash
    pytest
    ```

4. **Format and lint your code:** This project uses `ruff` for code formatting and linting. Run it before committing your changes.

    ```bash
    ruff format
    ruff check --fix
    ```

5. **Build documentation (if you've made docs changes):** This project uses MkDocs for documentation. Test your changes by building the docs.

    ```bash
    pip install -e ".[docs]"
    ./build_docs.sh
    ```

## Pull Request Template

We'd love to see a quick summary of what your PR does. Just a few sentences about what problem it solves and how it works.

### Summary

Brief description of what this PR accomplishes.

### Changes

- List of specific changes made
- What problems this solves
- How it impacts existing functionality

### Testing

- Tests added or modified
- Manual testing performed
- Any edge cases covered

### Related Issues

- Fixes #issue-number
- Addresses #issue-number
  
## Coding Style Guidelines

### Method Ordering

Chunklet follows a logical, hierarchical method ordering style to keep things readable and consistent:

1. **Class Docstring** - Comprehensive documentation at the top
2. **Class Constants/Attributes** - Static configuration (e.g., `BUILTIN_SUPPORTED_EXTENSIONS`)
3. **`__init__` Method** - Constructor always first after constants  
4. **Properties** - `@property` decorators and setters (if any)
5. **Private Methods** (`def _method`) - Helper/internal methods in logical execution order
6. **Public Methods** (`def method`) - Main API methods at the end

**Example Structure:**
```python
class ExampleClass:
    """Class docstring."""

    # Class constants
    CONSTANT = "value"

    def __init__(self):
        """Initialize the class."""
        pass

    @property
    def some_property(self):
        """Property getter."""
        return self._value

    def _helper_method(self):
        """Private helper method."""
        pass

    def public_method(self):
        """Main public API method."""
        pass
```

**Rationale:** This ordering follows the object lifecycle (init -> helpers -> public API) and keeps implementation details organized while making the public interface easy to find.

### Docstring Standards

All public methods and classes should include docstrings following the **Google Python Style Guide**. Private methods can have docstrings if they're helpful.

For docstring format, please follow the Google style as outlined in:

- [Google Python Style Guide - Comments and Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- [Google Style Example](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)

This ensures consistency across the codebase and makes documentation more predictable for users and contributors.

### Code Quality Tools

We use **Ruff** for linting and formatting, which provides:
- Faster feedback cycles (10-100x faster than previous tools)
- Unified linting and formatting in a single tool
- Better Python 3.12+ support

## Submitting a Pull Request

When you're ready to submit your pull request, here's what we need:

- Clear and descriptive title for your pull request
- Summary of what changes you made and why
- Links to any related issues (e.g., "Fixes #123")
- Confirmation that all tests pass

## Code of Conduct

We're all adults here trying to build cool software together. Be nice, don't be a jerk, respect different opinions, and remember that behind every GitHub profile is a human being who probably has better things to do than deal with your nonsense. If you can't contribute without making the experience miserable for others, maybe try contributing to a different project instead. We're here to code, not to psychoanalyze each other's life choices. Keep it professional, keep it civil, and we'll all get along just fine.
