# Contributing to Chunklet

First and foremost, thank you for considering contributing to Chunklet! We appreciate the time and effort you are willing to invest. Every contribution, whether it's a bug report, a new feature, or a documentation update, helps make Chunklet better for everyone.

## Getting Started

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/speedyk-005/chunklet-py.git
    cd chunklet-py
    ```

2.  **Install dependencies:** It is recommended to use a virtual environment.

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

1.  **Create a new branch:**

    ```bash
    git checkout -b my-feature-branch
    ```

2.  **Write your code:** Make your changes and ensure they follow the project's coding style.

3.  **Run tests:** Make sure all tests pass before submitting a pull request.

    ```bash
    pytest
    ```

4.  **Format your code:** This project uses `black` for code formatting. Please run it before committing your changes.

    ```bash
    black .
    ```

5.  **Lint your code:** This project uses `flake8` for linting. Please run it before committing your changes.

    ```bash
    flake8 src/ tests/
    ```

6.  **Build documentation (if you've made docs changes):** This project uses MkDocs for documentation. Test your changes by building the docs.

    ```bash
    pip install -e ".[docs]"
    ./build_docs.sh
    ```

## Coding Style Guidelines

### Method Ordering

Chunklet follows a **logical, hierarchical method ordering style** to maintain code readability and consistency:

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

**Rationale:** This ordering follows the object lifecycle (init → helpers → public API) and makes the public interface easily discoverable while keeping implementation details organized.

## Submitting a Pull Request

When you are ready to submit your pull request, please ensure you have done the following:

-   Provided a clear and descriptive title for your pull request.
-   Included a summary of the changes and why they are being made.
-   Referenced any related issues in the pull request description (e.g., "Fixes #123").
-   Confirmed that all tests pass.

## Code of Conduct

Look, we're all adults here trying to build cool software together. Be nice, don't be a jerk, respect different opinions, and remember that behind every GitHub profile is a human being who probably has better things to do than deal with your nonsense. If you can't contribute without making the experience miserable for others, maybe try contributing to a different project instead. We're here to code, not to psychoanalyze each other's life choices. Keep it professional, keep it civil, and we'll all get along just fine.
